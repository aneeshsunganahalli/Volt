from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Tuple
from app.models.gamification import (
    GamificationEvent, UserPoints, UserStreak, Achievement, UserAchievement,
    EventType, StreakType, BadgeTier
)
from app.schemas.gamification_schema import (
    GamificationProfileResponse, StreakSchema, BadgeSchema,
    GamificationEventResponse, GamificationFeedResponse
)
import logging

logger = logging.getLogger(__name__)


# XP Configuration per event type
XP_REWARDS = {
    EventType.TRANSACTION_IMPORTED: 2,
    EventType.TRANSACTION_CATEGORIZED: 5,
    EventType.GOAL_CREATED: 10,
    EventType.GOAL_MILESTONE_REACHED: 25,  # Base; can scale with metadata
    EventType.GOAL_COMPLETED: 150,
    EventType.DAILY_CHECKIN: 3,
    EventType.NO_SPEND_DAY: 15,
    EventType.BUDGET_UNDER_TARGET: 30,
    EventType.SPENDING_REVIEW_COMPLETED: 10,
}

# Daily XP caps per event type
DAILY_XP_CAPS = {
    EventType.TRANSACTION_IMPORTED: 100,
    EventType.TRANSACTION_CATEGORIZED: 100,
    EventType.DAILY_CHECKIN: 3,  # Only once per day
}

# Streak bonus milestones
STREAK_BONUSES = {
    3: 5,
    7: 20,
    14: 40,
    30: 50,
    60: 100,
    100: 200,
}


class GamificationService:
    """Service to handle all gamification logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _calculate_level_xp(self, level: int) -> int:
        """Calculate total XP required to reach this level (cumulative)"""
        if level <= 1:
            return 0
        elif level == 2:
            return 100
        elif level == 3:
            return 220
        elif level == 4:
            return 360
        elif level == 5:
            return 520
        else:
            # After L5: accumulate XP for each level
            total = 520  # XP for level 5
            for lvl in range(6, level + 1):
                total += 200 + (lvl - 5) * 20
            return total
    
    def _get_level_from_xp(self, xp_total: int) -> Tuple[int, int]:
        """
        Calculate level and next level XP from total XP.
        Returns (current_level, xp_for_next_level)
        """
        level = 1
        
        while True:
            next_level_total_xp = self._calculate_level_xp(level + 1)
            if xp_total < next_level_total_xp:
                # Current level found
                xp_in_current_level = xp_total - self._calculate_level_xp(level)
                xp_needed_for_next = next_level_total_xp - self._calculate_level_xp(level)
                return level, xp_needed_for_next
            level += 1
            if level > 100:  # Safety cap
                return level, 1000
    
    def _check_daily_cap(self, user_id: int, event_type: EventType) -> bool:
        """Check if user has hit the daily XP cap for this event type"""
        if event_type not in DAILY_XP_CAPS:
            return False
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_xp_today = self.db.query(func.sum(GamificationEvent.xp_awarded)).filter(
            and_(
                GamificationEvent.user_id == user_id,
                GamificationEvent.event_type == event_type,
                GamificationEvent.created_at >= today_start
            )
        ).scalar() or 0
        
        return total_xp_today >= DAILY_XP_CAPS[event_type]
    
    def award_event(
        self, 
        user_id: int, 
        event_type: EventType, 
        metadata: Optional[Dict] = None
    ) -> Optional[GamificationEvent]:
        """
        Award XP for a gamification event.
        Returns the event record or None if capped.
        """
        # Check daily cap
        if self._check_daily_cap(user_id, event_type):
            logger.info(f"User {user_id} hit daily cap for {event_type}")
            return None
        
        # Calculate XP to award
        base_xp = XP_REWARDS.get(event_type, 0)
        
        # Scale XP based on metadata (e.g., milestone percentage)
        if event_type == EventType.GOAL_MILESTONE_REACHED and metadata:
            milestone_pct = metadata.get("milestone_percentage", 25)
            if milestone_pct >= 75:
                base_xp = 60
            elif milestone_pct >= 50:
                base_xp = 40
            elif milestone_pct >= 25:
                base_xp = 25
            else:
                base_xp = 15
        
        # Create event record
        event = GamificationEvent(
            user_id=user_id,
            event_type=event_type,
            xp_awarded=base_xp,
            metadata=metadata
        )
        self.db.add(event)
        
        # Update user points
        user_points = self.db.query(UserPoints).filter(
            UserPoints.user_id == user_id
        ).first()
        
        if not user_points:
            user_points = UserPoints(user_id=user_id, xp_total=0, level=1)
            self.db.add(user_points)
        
        user_points.xp_total += base_xp
        new_level, _ = self._get_level_from_xp(user_points.xp_total)
        
        old_level = user_points.level
        user_points.level = new_level
        
        self.db.commit()
        self.db.refresh(event)
        
        # Check for level-up achievements
        if new_level > old_level:
            self._check_level_achievements(user_id, new_level)
        
        # Check for event-based achievements
        self._evaluate_achievements(user_id, event_type)
        
        return event
    
    def update_streak(
        self, 
        user_id: int, 
        streak_type: StreakType, 
        event_date: Optional[date] = None
    ) -> Optional[UserStreak]:
        """
        Update or create a streak for a user.
        Returns the streak record.
        """
        if event_date is None:
            event_date = date.today()
        
        streak = self.db.query(UserStreak).filter(
            and_(
                UserStreak.user_id == user_id,
                UserStreak.streak_type == streak_type
            )
        ).first()
        
        if not streak:
            # Create new streak
            streak = UserStreak(
                user_id=user_id,
                streak_type=streak_type,
                count=1,
                last_date=event_date
            )
            self.db.add(streak)
        else:
            # Check if streak continues or resets
            days_diff = (event_date - streak.last_date).days
            
            if days_diff == 0:
                # Same day, no change
                return streak
            elif days_diff == 1:
                # Consecutive day
                streak.count += 1
                streak.last_date = event_date
                
                # Award streak bonus if milestone reached
                if streak.count in STREAK_BONUSES:
                    bonus_xp = STREAK_BONUSES[streak.count]
                    self.award_event(
                        user_id, 
                        EventType.DAILY_CHECKIN,  # Use checkin as streak bonus event
                        metadata={"streak_bonus": True, "streak_count": streak.count}
                    )
            else:
                # Streak broken, reset
                streak.count = 1
                streak.last_date = event_date
        
        self.db.commit()
        self.db.refresh(streak)
        
        # Check streak achievements
        self._check_streak_achievements(user_id, streak_type, streak.count)
        
        return streak
    
    def get_profile(self, user_id: int) -> GamificationProfileResponse:
        """Get user's gamification profile"""
        # Get or create user points
        user_points = self.db.query(UserPoints).filter(
            UserPoints.user_id == user_id
        ).first()
        
        if not user_points:
            user_points = UserPoints(user_id=user_id, xp_total=0, level=1)
            self.db.add(user_points)
            self.db.commit()
            self.db.refresh(user_points)
        
        # Calculate XP for next level
        current_level_total_xp = self._calculate_level_xp(user_points.level)
        next_level_total_xp = self._calculate_level_xp(user_points.level + 1)
        xp_needed_for_next_level = next_level_total_xp - current_level_total_xp
        xp_to_next = next_level_total_xp - user_points.xp_total
        
        # Get streaks
        streaks_db = self.db.query(UserStreak).filter(
            UserStreak.user_id == user_id
        ).all()
        
        streaks = []
        for streak in streaks_db:
            # Calculate next bonus
            next_bonus = None
            for milestone in sorted(STREAK_BONUSES.keys()):
                if milestone > streak.count:
                    next_bonus = milestone - streak.count
                    break
            
            streaks.append(StreakSchema(
                type=streak.streak_type.value,
                count=streak.count,
                last_date=streak.last_date.isoformat(),
                next_bonus_in=next_bonus
            ))
        
        # Get achievements
        user_achievements = self.db.query(UserAchievement, Achievement).join(
            Achievement
        ).filter(
            UserAchievement.user_id == user_id
        ).all()
        
        # Get all achievements to show locked ones
        all_achievements = self.db.query(Achievement).all()
        
        badges = []
        earned_ids = {ua.achievement_id for ua, _ in user_achievements}
        
        for achievement in all_achievements:
            earned_at = None
            for ua, _ in user_achievements:
                if ua.achievement_id == achievement.id:
                    earned_at = ua.earned_at
                    break
            
            badges.append(BadgeSchema(
                code=achievement.code,
                name=achievement.name,
                description=achievement.description,
                tier=achievement.tier.value if achievement.tier else None,
                earned_at=earned_at,
                icon=achievement.icon
            ))
        
        return GamificationProfileResponse(
            xp_total=user_points.xp_total,
            level=user_points.level,
            next_level_xp=xp_needed_for_next_level,
            xp_to_next_level=xp_to_next,
            streaks=streaks,
            badges=badges
        )
    
    def get_recent_events(
        self, 
        user_id: int, 
        limit: int = 20
    ) -> GamificationFeedResponse:
        """Get recent gamification events for a user"""
        events = self.db.query(GamificationEvent).filter(
            GamificationEvent.user_id == user_id
        ).order_by(
            GamificationEvent.created_at.desc()
        ).limit(limit).all()
        
        total_count = self.db.query(func.count(GamificationEvent.id)).filter(
            GamificationEvent.user_id == user_id
        ).scalar()
        
        event_responses = [
            GamificationEventResponse(
                id=event.id,
                event_type=event.event_type.value,
                xp_awarded=event.xp_awarded,
                message=self._get_event_message(event),
                created_at=event.created_at
            )
            for event in events
        ]
        
        return GamificationFeedResponse(
            events=event_responses,
            total_count=total_count or 0
        )
    
    def _get_event_message(self, event: GamificationEvent) -> str:
        """Generate a friendly message for an event"""
        messages = {
            EventType.TRANSACTION_IMPORTED: "Transaction imported",
            EventType.TRANSACTION_CATEGORIZED: "Transaction categorized",
            EventType.GOAL_CREATED: "New goal created",
            EventType.GOAL_MILESTONE_REACHED: "Goal milestone reached",
            EventType.GOAL_COMPLETED: "Goal completed! 🎉",
            EventType.DAILY_CHECKIN: "Daily check-in",
            EventType.NO_SPEND_DAY: "No-spend day achieved",
            EventType.BUDGET_UNDER_TARGET: "Budget target met",
            EventType.SPENDING_REVIEW_COMPLETED: "Spending review completed",
        }
        return messages.get(event.event_type, "Event completed")
    
    def _evaluate_achievements(self, user_id: int, event_type: EventType):
        """Check and award achievements based on recent events"""
        # Count total events of this type
        count = self.db.query(func.count(GamificationEvent.id)).filter(
            and_(
                GamificationEvent.user_id == user_id,
                GamificationEvent.event_type == event_type
            )
        ).scalar()
        
        # Define achievement triggers
        achievement_checks = []
        
        if event_type == EventType.TRANSACTION_CATEGORIZED:
            if count >= 1:
                achievement_checks.append("FIRST_CATEGORIZATION")
            if count >= 50:
                achievement_checks.append("CATEGORIZER_BRONZE")
            if count >= 200:
                achievement_checks.append("CATEGORIZER_SILVER")
            if count >= 1000:
                achievement_checks.append("CATEGORIZER_GOLD")
        
        elif event_type == EventType.GOAL_COMPLETED:
            if count >= 1:
                achievement_checks.append("GOAL_CRUSHER_BRONZE")
            if count >= 3:
                achievement_checks.append("GOAL_CRUSHER_SILVER")
            if count >= 10:
                achievement_checks.append("GOAL_CRUSHER_GOLD")
        
        # Award achievements
        for achievement_code in achievement_checks:
            self._award_achievement(user_id, achievement_code)
    
    def _check_level_achievements(self, user_id: int, level: int):
        """Award achievements based on level"""
        if level >= 5:
            self._award_achievement(user_id, "LEVEL_5")
        if level >= 10:
            self._award_achievement(user_id, "LEVEL_10")
        if level >= 25:
            self._award_achievement(user_id, "LEVEL_25")
    
    def _check_streak_achievements(
        self, 
        user_id: int, 
        streak_type: StreakType, 
        count: int
    ):
        """Award achievements based on streaks"""
        if streak_type == StreakType.CHECKIN:
            if count >= 7:
                self._award_achievement(user_id, "CONSISTENCY_BRONZE")
            if count >= 30:
                self._award_achievement(user_id, "CONSISTENCY_SILVER")
            if count >= 100:
                self._award_achievement(user_id, "CONSISTENCY_GOLD")
        
        elif streak_type == StreakType.NO_SPEND:
            if count >= 7:
                self._award_achievement(user_id, "NO_SPEND_NINJA")
    
    def _award_achievement(self, user_id: int, achievement_code: str):
        """Award an achievement to a user if not already earned"""
        achievement = self.db.query(Achievement).filter(
            Achievement.code == achievement_code
        ).first()
        
        if not achievement:
            logger.warning(f"Achievement {achievement_code} not found")
            return
        
        # Check if already earned
        existing = self.db.query(UserAchievement).filter(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement.id
            )
        ).first()
        
        if existing:
            return
        
        # Award achievement
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement.id
        )
        self.db.add(user_achievement)
        self.db.commit()
        
        logger.info(f"Awarded achievement {achievement_code} to user {user_id}")


def seed_achievements(db: Session):
    """Seed initial achievements into the database"""
    achievements_data = [
        {
            "code": "FIRST_CATEGORIZATION",
            "name": "First Steps",
            "description": "Categorize your first transaction",
            "tier": None,
            "criteria": {"event_type": "TRANSACTION_CATEGORIZED", "count": 1}
        },
        {
            "code": "CATEGORIZER_BRONZE",
            "name": "Categorizer Bronze",
            "description": "Categorize 50 transactions",
            "tier": BadgeTier.BRONZE,
            "criteria": {"event_type": "TRANSACTION_CATEGORIZED", "count": 50}
        },
        {
            "code": "CATEGORIZER_SILVER",
            "name": "Categorizer Silver",
            "description": "Categorize 200 transactions",
            "tier": BadgeTier.SILVER,
            "criteria": {"event_type": "TRANSACTION_CATEGORIZED", "count": 200}
        },
        {
            "code": "CATEGORIZER_GOLD",
            "name": "Categorizer Gold",
            "description": "Categorize 1000 transactions",
            "tier": BadgeTier.GOLD,
            "criteria": {"event_type": "TRANSACTION_CATEGORIZED", "count": 1000}
        },
        {
            "code": "GOAL_CRUSHER_BRONZE",
            "name": "Goal Crusher Bronze",
            "description": "Complete your first goal",
            "tier": BadgeTier.BRONZE,
            "criteria": {"event_type": "GOAL_COMPLETED", "count": 1}
        },
        {
            "code": "GOAL_CRUSHER_SILVER",
            "name": "Goal Crusher Silver",
            "description": "Complete 3 goals",
            "tier": BadgeTier.SILVER,
            "criteria": {"event_type": "GOAL_COMPLETED", "count": 3}
        },
        {
            "code": "GOAL_CRUSHER_GOLD",
            "name": "Goal Crusher Gold",
            "description": "Complete 10 goals",
            "tier": BadgeTier.GOLD,
            "criteria": {"event_type": "GOAL_COMPLETED", "count": 10}
        },
        {
            "code": "CONSISTENCY_BRONZE",
            "name": "Consistency Bronze",
            "description": "7-day check-in streak",
            "tier": BadgeTier.BRONZE,
            "criteria": {"streak_type": "checkin", "count": 7}
        },
        {
            "code": "CONSISTENCY_SILVER",
            "name": "Consistency Silver",
            "description": "30-day check-in streak",
            "tier": BadgeTier.SILVER,
            "criteria": {"streak_type": "checkin", "count": 30}
        },
        {
            "code": "CONSISTENCY_GOLD",
            "name": "Consistency Gold",
            "description": "100-day check-in streak",
            "tier": BadgeTier.GOLD,
            "criteria": {"streak_type": "checkin", "count": 100}
        },
        {
            "code": "NO_SPEND_NINJA",
            "name": "No-Spend Ninja",
            "description": "7-day no-spend streak",
            "tier": BadgeTier.BRONZE,
            "criteria": {"streak_type": "no_spend", "count": 7}
        },
        {
            "code": "LEVEL_5",
            "name": "Rising Star",
            "description": "Reach level 5",
            "tier": None,
            "criteria": {"level": 5}
        },
        {
            "code": "LEVEL_10",
            "name": "Dedicated",
            "description": "Reach level 10",
            "tier": BadgeTier.SILVER,
            "criteria": {"level": 10}
        },
        {
            "code": "LEVEL_25",
            "name": "Master",
            "description": "Reach level 25",
            "tier": BadgeTier.GOLD,
            "criteria": {"level": 25}
        },
    ]
    
    for achievement_data in achievements_data:
        existing = db.query(Achievement).filter(
            Achievement.code == achievement_data["code"]
        ).first()
        
        if not existing:
            achievement = Achievement(**achievement_data)
            db.add(achievement)
    
    db.commit()
    logger.info("Seeded achievements")
