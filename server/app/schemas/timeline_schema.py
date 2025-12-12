"""
Animated Cash Flow Timeline schemas for visual demonstrations.
Shows week-by-week or month-by-month cash flow with animation support.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional, List
from datetime import datetime, date


class CashFlowPeriod(BaseModel):
    """A single period in the cash flow timeline."""
    
    period_key: str = Field(..., description="Period identifier (e.g., '2025-W01' or '2025-01')")
    start_date: date = Field(..., description="Start date of the period")
    end_date: date = Field(..., description="End date of the period")
    income: float = Field(..., ge=0, description="Total income for this period")
    expenses: float = Field(..., ge=0, description="Total expenses for this period")
    net_flow: float = Field(..., description="Net cash flow (income - expenses)")
    is_lean: bool = Field(default=False, description="Whether this is a lean period")
    severity: Optional[float] = Field(None, ge=0, description="Severity score if lean period")
    income_sources: int = Field(default=0, ge=0, description="Number of distinct income sources")
    transaction_count: int = Field(default=0, ge=0, description="Total transactions in period")
    
    # Animation hints
    animation_delay: int = Field(default=0, ge=0, description="Animation delay in ms")
    highlight: bool = Field(default=False, description="Whether to highlight this period")
    
    model_config = ConfigDict(frozen=True)


class ForecastPeriod(BaseModel):
    """A forecasted future period with multiple scenarios."""
    
    period_key: str = Field(..., description="Period identifier")
    start_date: date = Field(..., description="Start date of the period")
    end_date: date = Field(..., description="End date of the period")
    
    # Three scenarios
    best_case: float = Field(..., description="Best case scenario net flow")
    likely_case: float = Field(..., description="Most likely scenario net flow")
    worst_case: float = Field(..., description="Worst case scenario net flow")
    
    confidence: float = Field(..., ge=0, le=1, description="Confidence in prediction (0-1)")
    is_predicted_lean: bool = Field(default=False, description="Whether likely case suggests lean period")
    
    model_config = ConfigDict(frozen=True)


class TimelineStatistics(BaseModel):
    """Summary statistics for the timeline."""
    
    total_income: float = Field(..., ge=0, description="Total income across all periods")
    total_expenses: float = Field(..., ge=0, description="Total expenses across all periods")
    total_net_flow: float = Field(..., description="Total net flow")
    avg_net_flow: float = Field(..., description="Average net flow per period")
    lean_period_count: int = Field(..., ge=0, description="Number of lean periods detected")
    lean_frequency: float = Field(..., ge=0, le=1, description="Frequency of lean periods (0-1)")
    volatility: float = Field(..., ge=0, description="Income volatility measure")
    
    model_config = ConfigDict(frozen=True)


class WelfordCalculation(BaseModel):
    """Shows the Welford's algorithm calculation in action."""
    
    sample_count: int = Field(..., ge=0, description="Number of samples processed")
    running_mean: float = Field(..., description="Current running mean")
    running_variance: float = Field(..., ge=0, description="Current running variance")
    running_std_dev: float = Field(..., ge=0, description="Current running standard deviation")
    
    # For educational purposes in demo
    algorithm_name: str = Field(default="Welford's Online Algorithm", description="Algorithm used")
    is_numerically_stable: bool = Field(default=True, description="Whether calculation is numerically stable")
    
    model_config = ConfigDict(frozen=True)


class AnimatedTimeline(BaseModel):
    """Complete animated cash flow timeline response."""
    
    timeline_type: Literal['weekly', 'monthly'] = Field(..., description="Type of timeline")
    historical_periods: List[CashFlowPeriod] = Field(..., description="Historical cash flow periods")
    forecast_periods: List[ForecastPeriod] = Field(default_factory=list, description="Forecasted periods")
    statistics: TimelineStatistics = Field(..., description="Summary statistics")
    welford_stats: Optional[WelfordCalculation] = Field(None, description="Welford's algorithm stats for demo")
    
    # Animation configuration
    animation_duration_ms: int = Field(default=2000, description="Duration for smooth scrolling animation")
    highlight_lean_periods: bool = Field(default=True, description="Whether to highlight lean periods")
    
    # Context
    user_id: int = Field(..., description="User ID for this timeline")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When timeline was generated")
    period_count: int = Field(..., ge=0, description="Total number of periods included")
    
    model_config = ConfigDict(frozen=True)
