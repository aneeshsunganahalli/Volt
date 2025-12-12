from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List


class GoalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    target_amount: Decimal = Field(..., gt=0, decimal_places=2)
    end_date: datetime


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    target_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    current_amount: Optional[Decimal] = Field(None, decimal_places=2)
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_achieved: Optional[bool] = None


class GoalContributionResponse(BaseModel):
    id: int
    goal_id: int
    transaction_id: int
    amount: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True


class GoalResponse(GoalBase):
    id: int
    user_id: int
    current_amount: Decimal
    is_active: bool
    is_achieved: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GoalProgress(BaseModel):
    """Response model for goal progress tracking"""
    id: int
    title: str
    target_amount: Decimal
    current_amount: Decimal
    progress_percentage: float
    days_remaining: int
    is_achieved: bool
    is_active: bool
    is_overdue: bool
    total_contributions: int
    
    class Config:
        from_attributes = True


class GoalDetailedResponse(GoalResponse):
    """Detailed response including contribution history"""
    contributions: List[GoalContributionResponse] = []
    progress_percentage: float
    days_remaining: int
    is_overdue: bool
    
    class Config:
        from_attributes = True