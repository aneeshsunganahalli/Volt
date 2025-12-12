from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional
from app.models.goal import Goal, GoalContribution
from app.models.transactions import Transaction
from app.schemas.goal_schema import GoalCreate, GoalUpdate
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
            debit_contribution_rate=goal_data.debit_contribution_rate,
            credit_contribution_rate=goal_data.credit_contribution_rate,
            end_date=goal_data.end_date,
            current_amount=Decimal('0.00'),
            is_active=True,
            is_achieved=False
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
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
        Process a transaction and contribute to active goals based on contribution rates.
        Called whenever a new transaction is created.
        """
        if not transaction.amount or not transaction.type:
            return []
        
        # Get all active goals for the user
        active_goals = GoalService.get_active_goals(db, transaction.user_id)
        
        if not active_goals:
            return []
        
        contributions = []
        
        for goal in active_goals:
            # Skip if goal is already achieved
            if goal.is_achieved:
                continue
            
            # Calculate contribution based on transaction type
            contribution_amount = Decimal('0.00')
            
            if transaction.type.lower() == "debit":
                # For debits, save a percentage (encouraging saving when spending)
                contribution_amount = (transaction.amount * goal.debit_contribution_rate) / Decimal('100')
            elif transaction.type.lower() == "credit":
                # For credits, save a percentage (saving from income)
                contribution_amount = (transaction.amount * goal.credit_contribution_rate) / Decimal('100')
            
            if contribution_amount > 0:
                # Create contribution record
                contribution = GoalContribution(
                    goal_id=goal.id,
                    transaction_id=transaction.id,
                    amount=contribution_amount,
                    contribution_type=transaction.type
                )
                db.add(contribution)
                
                # Update goal's current amount
                goal.current_amount += contribution_amount
                
                # Check if goal is achieved
                if goal.current_amount >= goal.target_amount:
                    goal.is_achieved = True
                    logger.info(f"Goal {goal.id} '{goal.title}' achieved for user {transaction.user_id}!")
                
                contributions.append(contribution)
        
        if contributions:
            db.commit()
            logger.info(f"Processed {len(contributions)} goal contributions for transaction {transaction.id}")
        
        return contributions
    
    @staticmethod
    def calculate_progress(goal: Goal) -> dict:
        """Calculate progress metrics for a goal"""
        now = datetime.now(timezone.utc)
        
        # Calculate progress percentage
        progress_percentage = float((goal.current_amount / goal.target_amount) * 100) if goal.target_amount > 0 else 0
        progress_percentage = min(progress_percentage, 100.0)  # Cap at 100%
        
        # Calculate days remaining
        days_remaining = (goal.end_date - now).days
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