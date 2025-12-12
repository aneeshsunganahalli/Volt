from datetime import datetime
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.oauth2 import get_current_user
from app.schemas.goal_schema import (
    GoalCreate, 
    GoalUpdate, 
    GoalResponse, 
    GoalProgress,
    GoalDetailedResponse,
    GoalContributionResponse
)
from app.services.goal_service import GoalService

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal: GoalCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Create a new savings goal for the current user."""
    new_goal = GoalService.create_goal(db, current_user.id, goal)
    return new_goal


@router.get("/", response_model=List[GoalResponse])
async def get_all_goals(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    active_only: bool = False
):
    """Get all goals for the current user. Set active_only=true to get only active goals."""
    if active_only:
        goals = GoalService.get_active_goals(db, current_user.id)
    else:
        goals = GoalService.get_all_goals(db, current_user.id)
    return goals


@router.get("/progress", response_model=List[GoalProgress])
async def get_goals_with_progress(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    active_only: bool = False
):
    """Get all goals with calculated progress metrics."""
    if active_only:
        goals = GoalService.get_active_goals(db, current_user.id)
    else:
        goals = GoalService.get_all_goals(db, current_user.id)
    
    goals_with_progress = []
    for goal in goals:
        progress = GoalService.calculate_progress(goal)
        goals_with_progress.append(
            GoalProgress(
                id=goal.id,
                title=goal.title,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                progress_percentage=progress['progress_percentage'],
                days_remaining=progress['days_remaining'],
                is_achieved=goal.is_achieved,
                is_active=goal.is_active,
                is_overdue=progress['is_overdue'],
                total_contributions=progress['total_contributions']
            )
        )
    
    return goals_with_progress


@router.get("/{goal_id}", response_model=GoalDetailedResponse)
async def get_goal(
    goal_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Get a specific goal with detailed information including contribution history."""
    goal = GoalService.get_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with id {goal_id} not found"
        )
    
    # Calculate progress
    progress = GoalService.calculate_progress(goal)
    
    # Build detailed response
    return GoalDetailedResponse(
        id=goal.id,
        user_id=goal.user_id,
        title=goal.title,
        description=goal.description,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        end_date=goal.end_date,
        is_active=goal.is_active,
        is_achieved=goal.is_achieved,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
        contributions=[
            GoalContributionResponse(
                id=c.id,
                goal_id=c.goal_id,
                transaction_id=c.transaction_id,
                amount=c.amount,
                contribution_type=c.contribution_type,
                created_at=c.created_at
            ) for c in goal.contributions
        ] if hasattr(goal, 'contributions') else [],
        progress_percentage=progress['progress_percentage'],
        days_remaining=progress['days_remaining'],
        is_overdue=progress['is_overdue']
    )


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    goal_update: GoalUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Update a goal."""
    updated_goal = GoalService.update_goal(db, goal_id, current_user.id, goal_update)
    if not updated_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with id {goal_id} not found"
        )
    return updated_goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Delete a goal."""
    success = GoalService.delete_goal(db, goal_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with id {goal_id} not found"
        )


@router.post("/{goal_id}/activate", response_model=GoalResponse)
async def activate_goal(
    goal_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Activate a goal to start tracking contributions."""
    goal = GoalService.get_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with id {goal_id} not found"
        )
    
    goal.is_active = True
    db.commit()
    db.refresh(goal)
    return goal


@router.post("/{goal_id}/deactivate", response_model=GoalResponse)
async def deactivate_goal(
    goal_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Deactivate a goal to stop tracking contributions."""
    goal = GoalService.get_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with id {goal_id} not found"
        )
    
    goal.is_active = False
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/{goal_id}/contributions", response_model=List[GoalContributionResponse])
async def get_goal_contributions(
    goal_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Get all contributions for a specific goal."""
    goal = GoalService.get_goal(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with id {goal_id} not found"
        )
    
    if not hasattr(goal, 'contributions'):
        return []
    
    return [
        GoalContributionResponse(
            id=c.id,
            goal_id=c.goal_id,
            transaction_id=c.transaction_id,
            amount=c.amount,
            contribution_type=c.contribution_type,
            created_at=c.created_at
        ) for c in goal.contributions
    ]
