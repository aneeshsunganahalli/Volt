import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.gamification import (
    GamificationEvent, UserPoints, UserStreak, Achievement, UserAchievement,
    EventType, StreakType, BadgeTier
)
from app.services.gamification_service import GamificationService, seed_achievements


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user"""
    user = User(
        name="Test User",
        email="test@example.com",
        phone_number="1234567890",
        hashed_password="hashed",
        savings=Decimal("0.00")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def gamification_service(db_session: Session):
    """Create a gamification service instance"""
    seed_achievements(db_session)
    return GamificationService(db_session)


class TestGamificationService:
    """Test the gamification service"""
    
    def test_award_event_creates_event(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test that awarding an event creates a record"""
        event = gamification_service.award_event(
            test_user.id,
            EventType.TRANSACTION_IMPORTED
        )
        
        assert event is not None
        assert event.user_id == test_user.id
        assert event.event_type == EventType.TRANSACTION_IMPORTED
        assert event.xp_awarded == 2
    
    def test_award_event_updates_user_points(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test that awarding events updates user points"""
        gamification_service.award_event(test_user.id, EventType.GOAL_CREATED)
        
        user_points = db_session.query(UserPoints).filter(
            UserPoints.user_id == test_user.id
        ).first()
        
        assert user_points is not None
        assert user_points.xp_total == 10
        assert user_points.level == 1
    
    def test_daily_cap_enforced(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test that daily XP caps are enforced"""
        # Award DAILY_CHECKIN (cap is 3 XP)
        event1 = gamification_service.award_event(test_user.id, EventType.DAILY_CHECKIN)
        assert event1 is not None
        
        # Try to award again - should be blocked
        event2 = gamification_service.award_event(test_user.id, EventType.DAILY_CHECKIN)
        assert event2 is None
    
    def test_level_calculation(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test that level is calculated correctly from XP"""
        # Award enough XP to reach level 2 (100 XP)
        for _ in range(10):
            gamification_service.award_event(test_user.id, EventType.GOAL_CREATED)
        
        user_points = db_session.query(UserPoints).filter(
            UserPoints.user_id == test_user.id
        ).first()
        
        assert user_points.xp_total == 100
        assert user_points.level == 2
    
    def test_streak_creation(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test creating a new streak"""
        streak = gamification_service.update_streak(
            test_user.id,
            StreakType.CHECKIN,
            date.today()
        )
        
        assert streak is not None
        assert streak.count == 1
        assert streak.last_date == date.today()
    
    def test_streak_continuation(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test continuing a streak on consecutive days"""
        # Day 1
        streak = gamification_service.update_streak(
            test_user.id,
            StreakType.CHECKIN,
            date.today()
        )
        assert streak.count == 1
        
        # Day 2
        streak = gamification_service.update_streak(
            test_user.id,
            StreakType.CHECKIN,
            date.today() + timedelta(days=1)
        )
        assert streak.count == 2
    
    def test_streak_reset(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test that a streak resets if a day is missed"""
        # Day 1
        gamification_service.update_streak(
            test_user.id,
            StreakType.CHECKIN,
            date.today()
        )
        
        # Day 3 (missed day 2)
        streak = gamification_service.update_streak(
            test_user.id,
            StreakType.CHECKIN,
            date.today() + timedelta(days=2)
        )
        
        assert streak.count == 1
    
    def test_achievement_awarded(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test that achievements are awarded"""
        # First categorization should award FIRST_CATEGORIZATION achievement
        gamification_service.award_event(test_user.id, EventType.TRANSACTION_CATEGORIZED)
        
        user_achievement = db_session.query(UserAchievement).join(Achievement).filter(
            UserAchievement.user_id == test_user.id,
            Achievement.code == "FIRST_CATEGORIZATION"
        ).first()
        
        assert user_achievement is not None
    
    def test_achievement_not_duplicated(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test that achievements are not awarded twice"""
        gamification_service.award_event(test_user.id, EventType.TRANSACTION_CATEGORIZED)
        gamification_service.award_event(test_user.id, EventType.TRANSACTION_CATEGORIZED)
        
        count = db_session.query(UserAchievement).join(Achievement).filter(
            UserAchievement.user_id == test_user.id,
            Achievement.code == "FIRST_CATEGORIZATION"
        ).count()
        
        assert count == 1
    
    def test_get_profile(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test getting a user's profile"""
        gamification_service.award_event(test_user.id, EventType.GOAL_CREATED)
        gamification_service.update_streak(test_user.id, StreakType.CHECKIN)
        
        profile = gamification_service.get_profile(test_user.id)
        
        assert profile.xp_total == 10
        assert profile.level == 1
        assert profile.next_level_xp == 100
        assert len(profile.streaks) == 1
        assert profile.streaks[0].count == 1
    
    def test_milestone_xp_scaling(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test that milestone XP scales with percentage"""
        # 25% milestone
        event25 = gamification_service.award_event(
            test_user.id,
            EventType.GOAL_MILESTONE_REACHED,
            metadata={"milestone_percentage": 25}
        )
        assert event25.xp_awarded == 25
        
        # 75% milestone
        event75 = gamification_service.award_event(
            test_user.id,
            EventType.GOAL_MILESTONE_REACHED,
            metadata={"milestone_percentage": 75}
        )
        assert event75.xp_awarded == 60
    
    def test_get_recent_events(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test getting recent events"""
        gamification_service.award_event(test_user.id, EventType.GOAL_CREATED)
        gamification_service.award_event(test_user.id, EventType.TRANSACTION_CATEGORIZED)
        
        feed = gamification_service.get_recent_events(test_user.id, limit=10)
        
        assert feed.total_count == 2
        assert len(feed.events) == 2
        # Events are ordered by created_at desc, so the last one created is first
        assert feed.events[0].event_type in [EventType.GOAL_CREATED.value, EventType.TRANSACTION_CATEGORIZED.value]
    
    def test_level_achievements(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test that level achievements are awarded"""
        # Award 60 goals to reach level 5 (600 XP total)
        # Level thresholds: L1=0, L2=100, L3=220, L4=360, L5=520
        # Need 520 XP total for level 5
        for _ in range(60):
            gamification_service.award_event(test_user.id, EventType.GOAL_CREATED)
        
        user_points = db_session.query(UserPoints).filter(
            UserPoints.user_id == test_user.id
        ).first()
        
        # Should have 600 XP, which is level 5
        assert user_points.xp_total == 600
        assert user_points.level >= 5
        
        # Check for level 5 achievement
        achievement = db_session.query(UserAchievement).join(Achievement).filter(
            UserAchievement.user_id == test_user.id,
            Achievement.code == "LEVEL_5"
        ).first()
        
        assert achievement is not None
    
    def test_streak_achievements(self, db_session: Session, test_user: User, gamification_service: GamificationService):
        """Test that streak achievements are awarded"""
        # 7-day streak
        for i in range(7):
            gamification_service.update_streak(
                test_user.id,
                StreakType.CHECKIN,
                date.today() + timedelta(days=i)
            )
        
        # Check for bronze consistency achievement
        achievement = db_session.query(UserAchievement).join(Achievement).filter(
            UserAchievement.user_id == test_user.id,
            Achievement.code == "CONSISTENCY_BRONZE"
        ).first()
        
        assert achievement is not None


class TestAchievementSeeding:
    """Test achievement seeding"""
    
    def test_seed_achievements(self, db_session: Session):
        """Test that achievements are seeded correctly"""
        seed_achievements(db_session)
        
        count = db_session.query(Achievement).count()
        assert count >= 10
        
        # Check specific achievements
        first_cat = db_session.query(Achievement).filter(
            Achievement.code == "FIRST_CATEGORIZATION"
        ).first()
        assert first_cat is not None
        assert first_cat.name == "First Steps"
    
    def test_seed_idempotent(self, db_session: Session):
        """Test that seeding is idempotent"""
        seed_achievements(db_session)
        count1 = db_session.query(Achievement).count()
        
        seed_achievements(db_session)
        count2 = db_session.query(Achievement).count()
        
        assert count1 == count2
