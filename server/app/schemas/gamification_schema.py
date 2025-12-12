from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class StreakSchema(BaseModel):
    type: str  # e.g., "checkin", "categorization", "no_spend"
    count: int
    last_date: str
    next_bonus_in: Optional[int] = None  # days to next bonus threshold


class BadgeSchema(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    tier: Optional[str] = None  # Bronze/Silver/Gold/Platinum
    earned_at: Optional[datetime] = None  # None if locked
    icon: Optional[str] = None

    class Config:
        from_attributes = True


class GamificationProfileResponse(BaseModel):
    xp_total: int
    level: int
    next_level_xp: int
    xp_to_next_level: int  # remaining XP needed
    streaks: List[StreakSchema] = []
    badges: List[BadgeSchema] = []


class GamificationEventResponse(BaseModel):
    id: int
    event_type: str
    xp_awarded: int
    message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GamificationFeedResponse(BaseModel):
    events: List[GamificationEventResponse]
    total_count: int


class AwardEventRequest(BaseModel):
    event_type: str
    metadata: Optional[dict] = None
