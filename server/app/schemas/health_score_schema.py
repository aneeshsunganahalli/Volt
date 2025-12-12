"""
Financial Health Score schemas for API responses.
Provides a comprehensive, easy-to-understand financial health metric.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional, Dict, List
from datetime import datetime


class HealthScoreBreakdown(BaseModel):
    """Individual component scores that make up the overall health score."""
    
    income_stability: float = Field(..., ge=0, le=100, description="Score based on income volatility (0-100)")
    spending_discipline: float = Field(..., ge=0, le=100, description="Score based on impulse spending and budget adherence")
    emergency_fund: float = Field(..., ge=0, le=100, description="Score based on emergency fund adequacy")
    savings_rate: float = Field(..., ge=0, le=100, description="Score based on percentage of income saved")
    debt_health: float = Field(..., ge=0, le=100, description="Score based on debt-to-income ratio")
    diversification: float = Field(..., ge=0, le=100, description="Score based on income source diversity")
    
    model_config = ConfigDict(frozen=True)


class HealthScoreFactors(BaseModel):
    """Detailed factors that contributed to the score."""
    
    positive_factors: List[str] = Field(default_factory=list, description="Things you're doing well")
    negative_factors: List[str] = Field(default_factory=list, description="Areas for improvement")
    critical_issues: List[str] = Field(default_factory=list, description="Urgent items needing attention")
    
    model_config = ConfigDict(frozen=True)


class HealthScoreTrend(BaseModel):
    """Historical trend of health score."""
    
    date: datetime = Field(..., description="Date of the score")
    score: float = Field(..., ge=0, le=100, description="Health score at this date")
    change: Optional[float] = Field(None, description="Change from previous period")
    
    model_config = ConfigDict(frozen=True)


class HealthScoreComparison(BaseModel):
    """How user compares to others (can be simulated for demo)."""
    
    percentile: int = Field(..., ge=0, le=100, description="User's percentile (0-100)")
    comparison_text: str = Field(..., description="Human-readable comparison")
    avg_score: float = Field(..., ge=0, le=100, description="Average score of all users")
    
    model_config = ConfigDict(frozen=True)


class HealthScoreRecommendations(BaseModel):
    """Top 3 recommendations to improve health score."""
    
    priority: Literal['high', 'medium', 'low']
    action: str = Field(..., description="Recommended action")
    impact: str = Field(..., description="Expected impact on score")
    difficulty: Literal['easy', 'moderate', 'challenging']
    estimated_score_gain: float = Field(..., ge=0, description="Estimated score increase if completed")
    
    model_config = ConfigDict(frozen=True)


class FinancialHealthScore(BaseModel):
    """Complete financial health score response."""
    
    overall_score: float = Field(..., ge=0, le=100, description="Overall financial health score (0-100)")
    grade: Literal['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F'] = Field(..., description="Letter grade")
    score_description: str = Field(..., description="Plain-English description of health status")
    breakdown: HealthScoreBreakdown = Field(..., description="Component scores")
    factors: HealthScoreFactors = Field(..., description="Contributing factors")
    comparison: Optional[HealthScoreComparison] = Field(None, description="Comparison with other users")
    trend: List[HealthScoreTrend] = Field(default_factory=list, description="Historical trend (last 6 months)")
    recommendations: List[HealthScoreRecommendations] = Field(default_factory=list, description="Top improvement recommendations")
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="When this score was calculated")
    data_quality: Literal['excellent', 'good', 'fair', 'poor'] = Field(..., description="Quality of underlying data")
    
    model_config = ConfigDict(frozen=True)
