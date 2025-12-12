from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.oauth2 import get_current_user
from app.models.user import User
from app.models.gamification import EventType, StreakType
from app.services.gamification_service import GamificationService, seed_achievements
from app.schemas.gamification_schema import (
    GamificationProfileResponse,
    GamificationFeedResponse,
    AwardEventRequest
)

router = APIRouter(prefix="/gamification", tags=["Gamification"])


@router.get("/profile", response_model=GamificationProfileResponse)
async def get_gamification_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Get the current user's gamification profile including:
    - Total XP and level
    - XP needed for next level
    - Active streaks
    - Earned and locked badges
    """
    service = GamificationService(db)
    
    # Award daily check-in
    service.award_event(current_user.id, EventType.DAILY_CHECKIN)
    service.update_streak(current_user.id, StreakType.CHECKIN)
    
    return service.get_profile(current_user.id)


@router.get("/feed", response_model=GamificationFeedResponse)
async def get_gamification_feed(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    limit: int = 20
):
    """
    Get recent gamification events for the current user.
    Shows XP earned and achievement unlocks.
    """
    service = GamificationService(db)
    return service.get_recent_events(current_user.id, limit=limit)


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def award_event(
    event_request: AwardEventRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Manually award a gamification event (internal use or testing).
    Validates event type and applies daily caps.
    """
    try:
        event_type = EventType(event_request.event_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type: {event_request.event_type}"
        )
    
    service = GamificationService(db)
    event = service.award_event(
        current_user.id, 
        event_type, 
        event_request.metadata
    )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily XP cap reached for this event type"
        )
    
    return {
        "message": "Event awarded successfully",
        "xp_awarded": event.xp_awarded,
        "event_id": event.id
    }


@router.post("/admin/seed-achievements", status_code=status.HTTP_201_CREATED)
async def seed_achievements_endpoint(
    db: Session = Depends(get_db)
):
    """
    Seed the database with default achievements.
    Should be called once during initial setup.
    """
    seed_achievements(db)
    return {"message": "Achievements seeded successfully"}
