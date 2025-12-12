"""
Lean Week Predictor Schemas
"""
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class CashFlowPeriod(BaseModel):
    """Cash flow for a single period"""
    period: str
    income: float
    expenses: float
    net_flow: float
    start_date: Optional[datetime] = None


class LeanPeriod(BaseModel):
    """Identified lean period"""
    period: str
    net_flow: float
    income: float
    expenses: float
    severity: float
    start_date: Optional[datetime] = None


class LeanPattern(BaseModel):
    """Pattern detection result"""
    has_pattern: bool
    pattern_type: Optional[str]
    description: str


class LeanAnalysis(BaseModel):
    """Historical lean period analysis"""
    lean_periods: List[LeanPeriod]
    lean_frequency: float
    avg_lean_severity: float
    pattern_detected: LeanPattern
    threshold: float


class CashFlowScenario(BaseModel):
    """Cash flow scenario (best/likely/worst)"""
    best: float
    likely: float
    worst: float


class ForecastPeriod(BaseModel):
    """Forecast for a single period"""
    period: int
    month_offset: int
    income: CashFlowScenario
    expenses: CashFlowScenario
    net_cash_flow: CashFlowScenario
    projected_balance: CashFlowScenario
    is_lean_period: bool
    balance_at_risk: bool


class CashFlowForecast(BaseModel):
    """Cash flow forecast response"""
    forecasts: List[ForecastPeriod]
    warnings: List[str]
    confidence: float
    income_volatility: float
    avg_monthly_income: float
    avg_monthly_expenses: float


class SmoothingStrategy(BaseModel):
    """Income smoothing strategy"""
    volatility_level: str
    strategy_summary: str
    lean_frequency: float
    recommendations: List[str]
    action_items: List[str]


class IncomeSmoothingRecommendation(BaseModel):
    """Income smoothing recommendations"""
    current_balance: float
    target_emergency_fund: float
    emergency_fund_gap: float
    avg_monthly_income: float
    avg_monthly_expenses: float
    income_volatility: float
    good_months_count: int
    lean_months_count: int
    recommended_save_rate: float
    monthly_save_amount: float
    months_to_target: Optional[float]
    strategy: SmoothingStrategy


class RiskSummary(BaseModel):
    """Overall risk assessment summary"""
    risk_level: str
    risk_message: str
    immediate_action_needed: bool


class HistoricalAnalysis(BaseModel):
    """Historical lean period analysis"""
    monthly: LeanAnalysis
    weekly: LeanAnalysis


class LeanWeekAnalysisResponse(BaseModel):
    """Complete lean week analysis response"""
    summary: RiskSummary
    historical_analysis: HistoricalAnalysis
    cash_flow_forecast: CashFlowForecast
    income_smoothing: IncomeSmoothingRecommendation
    generated_at: str
    
    class Config:
        from_attributes = True
