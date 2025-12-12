from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum as SQLEnum, Date, Index
from sqlalchemy.sql import func
from app.database import Base
import enum


class EventType(str, enum.Enum):
    TRANSACTION_IMPORTED = "TRANSACTION_IMPORTED"
    TRANSACTION_CATEGORIZED = "TRANSACTION_CATEGORIZED"
    GOAL_CREATED = "GOAL_CREATED"
    GOAL_MILESTONE_REACHED = "GOAL_MILESTONE_REACHED"
    GOAL_COMPLETED = "GOAL_COMPLETED"
    DAILY_CHECKIN = "DAILY_CHECKIN"
    NO_SPEND_DAY = "NO_SPEND_DAY"
    BUDGET_UNDER_TARGET = "BUDGET_UNDER_TARGET"
    SPENDING_REVIEW_COMPLETED = "SPENDING_REVIEW_COMPLETED"


class StreakType(str, enum.Enum):
    CHECKIN = "checkin"
    CATEGORIZATION = "categorization"
    NO_SPEND = "no_spend"


class BadgeTier(str, enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class GamificationEvent(Base):
    """Log all gamification events for a user"""
    __tablename__ = "gamification_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(SQLEnum(EventType), nullable=False)
    xp_awarded = Column(Integer, default=0, nullable=False)
    event_metadata = Column(JSON, nullable=True)  # Store event-specific data (renamed from metadata)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index('ix_gamification_events_user_type_date', 'user_id', 'event_type', 'created_at'),
    )


class UserPoints(Base):
    """Track user's total XP and level"""
    __tablename__ = "user_points"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    xp_total = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserStreak(Base):
    """Track user's streaks"""
    __tablename__ = "user_streaks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    streak_type = Column(SQLEnum(StreakType), nullable=False)
    count = Column(Integer, default=0, nullable=False)
    last_date = Column(Date, nullable=False)  # Last date the streak was updated
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_user_streaks_user_type', 'user_id', 'streak_type', unique=True),
    )


class Achievement(Base):
    """Define all possible achievements"""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    tier = Column(SQLEnum(BadgeTier), nullable=True)
    criteria = Column(JSON, nullable=False)  # Define achievement requirements
    icon = Column(String, nullable=True)  # Icon name or URL
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserAchievement(Base):
    """Track which achievements users have earned"""
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    
    earned_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_user_achievements_user_achievement', 'user_id', 'achievement_id', unique=True),
    )
