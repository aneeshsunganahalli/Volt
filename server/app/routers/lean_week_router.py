"""
Lean Week Predictor API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from app.database import get_db
from app.models.user import User
from app.oauth2 import get_current_user
from app.services.lean_week_predictor import LeanWeekPredictor
from app.schemas.lean_week_schemas import (
    LeanWeekAnalysisResponse,
    CashFlowForecast,
    IncomeSmoothingRecommendation
)

router = APIRouter(prefix="/lean-week", tags=["Lean Week Predictor"])

# Initialize service
lean_predictor = LeanWeekPredictor()


@router.get(
    "/analysis",
    response_model=LeanWeekAnalysisResponse,
    summary="Get complete lean week analysis",
    description="Comprehensive analysis of cash flow challenges, forecasts, and income smoothing recommendations"
)
async def get_lean_week_analysis(
    current_user: Annotated[User, Depends(get_current_user)],
    current_balance: Optional[float] = Query(None, description="Current account balance. Uses user.savings if not provided"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive lean week analysis including:
    - Historical lean period identification
    - Cash flow forecasting (3 months ahead)
    - Income smoothing recommendations
    - Risk assessment and warnings
    """
    # Use provided balance or fall back to user's savings
    balance = current_balance if current_balance is not None else float(current_user.savings or 0)
    
    try:
        analysis = lean_predictor.get_complete_lean_analysis(
            db=db,
            user_id=current_user.id,
            current_balance=balance
        )
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating lean week analysis: {str(e)}"
        )


@router.get(
    "/forecast",
    response_model=CashFlowForecast,
    summary="Get cash flow forecast",
    description="Forecast cash flow for upcoming months with best/worst/likely scenarios"
)
async def get_cash_flow_forecast(
    current_user: Annotated[User, Depends(get_current_user)],
    periods: int = Query(3, ge=1, le=12, description="Number of future periods (months) to forecast"),
    current_balance: Optional[float] = Query(None, description="Current account balance"),
    db: Session = Depends(get_db)
):
    """
    Forecast future cash flow with scenario analysis:
    - Best case scenario
    - Likely scenario
    - Worst case scenario
    
    Includes warnings for potential lean periods and balance risks.
    """
    balance = current_balance if current_balance is not None else float(current_user.savings or 0)
    
    try:
        forecast = lean_predictor.forecast_cash_flow(
            db=db,
            user_id=current_user.id,
            forecast_periods=periods,
            current_balance=balance
        )
        return forecast
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating forecast: {str(e)}"
        )


@router.get(
    "/smoothing-recommendations",
    response_model=IncomeSmoothingRecommendation,
    summary="Get income smoothing recommendations",
    description="Calculate how much to save during good months to smooth income volatility"
)
async def get_income_smoothing_recommendations(
    current_user: Annotated[User, Depends(get_current_user)],
    current_balance: Optional[float] = Query(None, description="Current savings/emergency fund"),
    target_months: int = Query(3, ge=1, le=12, description="Target months of expenses to maintain as buffer"),
    db: Session = Depends(get_db)
):
    """
    Get personalized income smoothing strategy:
    - Target emergency fund size
    - Recommended savings rate for good months
    - Time to reach emergency fund target
    - Specific action items based on income volatility
    """
    balance = current_balance if current_balance is not None else float(current_user.savings or 0)
    
    try:
        recommendations = lean_predictor.calculate_income_smoothing_recommendation(
            db=db,
            user_id=current_user.id,
            current_balance=balance,
            target_months_buffer=target_months
        )
        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )
