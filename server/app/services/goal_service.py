from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional
from app.models.goal import Goal, GoalContribution
from app.models.transactions import Transaction
from app.schemas.goal_schema import GoalCreate, GoalUpdate
from app.models.gamification import EventType
import logging

logger = logging.getLogger(__name__)


class GoalService:
    """Service to manage savings goals and automatically track contributions from transactions"""
    
    @staticmethod
    def create_goal(db: Session, user_id: int, goal_data: GoalCreate) -> Goal:
        """Create a new savings goal"""
        goal = Goal(
            user_id=user_id,
            title=goal_data.title,
            description=goal_data.description,
            target_amount=goal_data.target_amount,
            end_date=goal_data.end_date,
            current_amount=Decimal('0.00'),
            is_active=True,
            is_achieved=False
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        
        # Award gamification event
        try:
            from app.services.gamification_service import GamificationService
            gamification = GamificationService(db)
            gamification.award_event(user_id, EventType.GOAL_CREATED)
        except Exception as e:
            logger.warning(f"Failed to award GOAL_CREATED event: {e}")
        
        return goal
    
    @staticmethod
    def get_active_goals(db: Session, user_id: int) -> List[Goal]:
        """Get all active goals for a user"""
        return db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.is_active == True
        ).all()
    
    @staticmethod
    def get_all_goals(db: Session, user_id: int) -> List[Goal]:
        """Get all goals for a user"""
        return db.query(Goal).filter(Goal.user_id == user_id).all()
    
    @staticmethod
    def get_goal(db: Session, goal_id: int, user_id: int) -> Optional[Goal]:
        """Get a specific goal"""
        return db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == user_id
        ).first()
    
    @staticmethod
    def update_goal(db: Session, goal_id: int, user_id: int, goal_data: GoalUpdate) -> Optional[Goal]:
        """Update a goal"""
        goal = GoalService.get_goal(db, goal_id, user_id)
        if not goal:
            return None
        
        update_data = goal_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(goal, field, value)
        
        db.commit()
        db.refresh(goal)
        return goal
    
    @staticmethod
    def delete_goal(db: Session, goal_id: int, user_id: int) -> bool:
        """Delete a goal"""
        goal = GoalService.get_goal(db, goal_id, user_id)
        if not goal:
            return False
        
        db.delete(goal)
        db.commit()
        return True
    
    @staticmethod
    async def process_transaction_for_goals(db: Session, transaction: Transaction) -> List[GoalContribution]:
        """
        Process a transaction and update active goals.
        Credits add to savings, debits subtract from savings.
        Savings = Total Credits - Total Debits
        """
        if not transaction.amount or not transaction.type:
            return []
        
        # Get all active goals for the user
        active_goals = GoalService.get_active_goals(db, transaction.user_id)
        
        if not active_goals:
            return []
        
        contributions = []
        
        for goal in active_goals:
            # Calculate amount to add/subtract based on transaction type
            amount_change = Decimal('0.00')
            
            if transaction.type.lower() == "credit":
                # Credits add to savings
                amount_change = transaction.amount
            elif transaction.type.lower() == "debit":
                # Debits subtract from savings (stored as negative)
                amount_change = -transaction.amount
            
            if amount_change != 0:
                # Create contribution record
                contribution = GoalContribution(
                    goal_id=goal.id,
                    transaction_id=transaction.id,
                    amount=amount_change
                )
                db.add(contribution)
                
                # Update goal's current amount (can be negative if debits > credits)
                goal.current_amount += amount_change
                
                # Check if goal is achieved (only if positive and reached target)
                was_achieved = goal.is_achieved
                previous_percentage = float((goal.current_amount - amount_change) / goal.target_amount * 100) if goal.target_amount > 0 else 0
                current_percentage = float(goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
                
                if goal.current_amount >= goal.target_amount and not goal.is_achieved:
                    goal.is_achieved = True
                    logger.info(f"Goal {goal.id} '{goal.title}' achieved for user {transaction.user_id}!")
                    
                    # Award goal completion event
                    try:
                        from app.services.gamification_service import GamificationService
                        gamification = GamificationService(db)
                        gamification.award_event(
                            transaction.user_id, 
                            EventType.GOAL_COMPLETED,
                            metadata={"goal_id": goal.id, "goal_title": goal.title}
                        )
                    except Exception as e:
                        logger.warning(f"Failed to award GOAL_COMPLETED event: {e}")
                        
                elif goal.current_amount < goal.target_amount and goal.is_achieved:
                    # If amount drops below target, mark as not achieved
                    goal.is_achieved = False
                    logger.info(f"Goal {goal.id} '{goal.title}' no longer achieved for user {transaction.user_id}")
                
                # Check for milestone achievements (25%, 50%, 75%)
                if not was_achieved:
                    milestones = [25, 50, 75]
                    for milestone in milestones:
                        if previous_percentage < milestone <= current_percentage:
                            try:
                                from app.services.gamification_service import GamificationService
                                gamification = GamificationService(db)
                                gamification.award_event(
                                    transaction.user_id,
                                    EventType.GOAL_MILESTONE_REACHED,
                                    metadata={
                                        "goal_id": goal.id,
                                        "goal_title": goal.title,
                                        "milestone_percentage": milestone
                                    }
                                )
                            except Exception as e:
                                logger.warning(f"Failed to award GOAL_MILESTONE_REACHED event: {e}")
                
                contributions.append(contribution)
        
        if contributions:
            db.commit()
            logger.info(f"Processed {len(contributions)} goal contributions for transaction {transaction.id}")
        
        return contributions
    
    @staticmethod
    def calculate_progress(goal: Goal) -> dict:
        """Calculate progress metrics for a goal"""
        now = datetime.now(timezone.utc)
        
        # Calculate progress percentage (can be negative if debits > credits)
        progress_percentage = float((goal.current_amount / goal.target_amount) * 100) if goal.target_amount > 0 else 0
        # Don't cap at 100% to show if exceeded, but cap negative at -100%
        progress_percentage = max(progress_percentage, -100.0)
        
        # Calculate days remaining - make end_date timezone-aware if naive
        end_date = goal.end_date if goal.end_date.tzinfo else goal.end_date.replace(tzinfo=timezone.utc)
        days_remaining = (end_date - now).days
        is_overdue = days_remaining < 0
        
        # Count contributions
        total_contributions = len(goal.contributions) if hasattr(goal, 'contributions') else 0
        
        return {
            'progress_percentage': round(progress_percentage, 2),
            'days_remaining': max(days_remaining, 0),
            'is_overdue': is_overdue,
            'total_contributions': total_contributions
        }
    
    @staticmethod
    def check_and_update_goal_status(db: Session, goal: Goal) -> Goal:
        """Check and update goal status (active, achieved, overdue)"""
        now = datetime.now(timezone.utc)
        
        # Check if goal is achieved
        if goal.current_amount >= goal.target_amount and not goal.is_achieved:
            goal.is_achieved = True
            goal.is_active = False  # Deactivate achieved goals
        
        # Optionally deactivate overdue goals (or keep them active)
        # Uncomment if you want to auto-deactivate overdue goals
        # if now > goal.end_date and goal.is_active and not goal.is_achieved:
        #     goal.is_active = False
        
        db.commit()
        db.refresh(goal)
        return goal