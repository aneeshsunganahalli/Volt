"""
Pydantic models for insight responses.

These models provide type safety, validation, and clear contracts for the
InsightFormatter service and frontend API consumers.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Literal, Optional, List
from decimal import Decimal


class QuickWin(BaseModel):
    """A single quick win opportunity for the user."""
    
    category: str = Field(..., description="Display name (e.g., 'Groceries')", min_length=1)
    category_key: str = Field(..., description="Internal key (e.g., 'GROCERIES')", min_length=1)
    action: str = Field(..., description="Action description (e.g., 'Cut by 15%')", min_length=1)
    monthly_impact: float = Field(..., ge=0, description="Monthly savings amount")
    annual_impact: float = Field(..., ge=0, description="Annual savings amount")
    difficulty: Literal['easy', 'moderate', 'challenging']
    current_spending: float = Field(..., ge=0, description="Current average spending")
    new_spending: float = Field(..., ge=0, description="Target spending after change")
    reason: Optional[str] = Field(None, description="Why this is a quick win")
    
    model_config = ConfigDict(frozen=True)  # Immutable for safety


class Warning(BaseModel):
    """A warning or alert for the user."""
    
    type: str = Field(
        ..., 
        description="Warning type (e.g., 'income_risk', 'optimization', 'emergency_fund')",
        min_length=1
    )
    message: str = Field(..., min_length=1, description="Warning message text")
    severity: Literal['info', 'warning', 'error']
    metric: Optional[str] = Field(None, description="Related metric (e.g., '42% volatility')")
    recommendation: Optional[str] = Field(None, description="Suggested action")
    
    model_config = ConfigDict(frozen=True)


class ScenarioInsight(BaseModel):
    """Complete insight package for a scenario simulation."""
    
    headline: str = Field(..., min_length=1, description="Plain-English summary headline")
    confidence: Literal['high', 'moderate', 'low']
    confidence_reason: str = Field(..., min_length=1, description="Why this confidence level")
    quick_wins: List[QuickWin] = Field(default_factory=list, description="Top quick win opportunities")
    warnings: List[Warning] = Field(default_factory=list, description="Risk warnings and alerts")
    timeline: str = Field(..., min_length=1, description="Estimated timeline to achieve")
    visual_suggestion: str = Field(
        default='category_breakdown_bar_chart',
        description="Suggested chart type for frontend"
    )
    annual_impact: str = Field(..., description="Formatted string like '₹12,000'")
    annual_impact_value: float = Field(..., description="Raw numeric value for calculations")
    achievability_score: int = Field(..., ge=0, le=100, description="Achievability percentage")
    total_categories_affected: int = Field(..., ge=0, description="Number of categories changed")
    
    model_config = ConfigDict(frozen=True)


class CategorySpending(BaseModel):
    """Spending details for a single category."""
    
    category: str = Field(..., description="Display name", min_length=1)
    category_key: str = Field(..., description="Internal key", min_length=1)
    monthly_avg: float = Field(..., ge=0, description="Average monthly spending")
    transaction_count: int = Field(..., ge=0, description="Number of transactions")
    reliability_score: float = Field(..., ge=0, le=1, description="Reliability score (0-1)")
    
    model_config = ConfigDict(frozen=True)


class FlexibilityCategory(BaseModel):
    """Category with spending flexibility metrics."""
    
    category: str = Field(..., description="Display name", min_length=1)
    category_key: str = Field(..., description="Internal key", min_length=1)
    monthly_avg: float = Field(..., ge=0, description="Average monthly spending")
    elasticity: float = Field(..., ge=0, le=1, description="Elasticity/flexibility score (0-1)")
    flexibility_label: Literal['high', 'low'] = Field(..., description="High or low flexibility")
    
    model_config = ConfigDict(frozen=True)


class ImpulseScore(BaseModel):
    """Impulse spending metrics and interpretation."""
    
    value: float = Field(..., ge=0, le=1, description="Impulse score (0-1)")
    level: Literal['low', 'moderate', 'high']
    message: str = Field(..., min_length=1, description="Interpretation message")
    recommendation: Optional[str] = Field(None, description="Suggested improvement action")
    
    model_config = ConfigDict(frozen=True)


class IncomeHealth(BaseModel):
    """Income health metrics for freelancers."""
    
    status: Literal['stable', 'moderate', 'variable']
    message: str = Field(..., min_length=1, description="Health status message")
    volatility_percent: int = Field(..., ge=0, le=100, description="Volatility percentage")
    avg_monthly: float = Field(..., ge=0, description="Average monthly income")
    recommendation: str = Field(..., min_length=1, description="Personalized recommendation")
    emergency_fund_target: float = Field(..., ge=0, description="Recommended emergency fund amount")
    emergency_fund_months: int = Field(..., ge=1, description="Months of coverage recommended")
    
    model_config = ConfigDict(frozen=True)


class DataQuality(BaseModel):
    """Data quality and confidence metrics."""
    
    reliable_categories: int = Field(..., ge=0, description="Number of reliable categories")
    total_categories: int = Field(..., ge=0, description="Total categories tracked")
    transaction_count: int = Field(..., ge=0, description="Total transactions")
    confidence: Literal['high', 'building', 'low']
    message: str = Field(..., min_length=1, description="Data quality message")
    
    model_config = ConfigDict(frozen=True)
    
    @field_validator('reliable_categories')
    @classmethod
    def validate_reliable_not_exceed_total(cls, v, info):
        """Ensure reliable_categories <= total_categories."""
        if 'total_categories' in info.data and v > info.data['total_categories']:
            raise ValueError('reliable_categories cannot exceed total_categories')
        return v


class BehaviorSummary(BaseModel):
    """Complete behavior summary for dashboard."""
    
    total_monthly_spending: float = Field(..., ge=0, description="Total monthly spending")
    transaction_count: int = Field(..., ge=0, description="Total transactions")
    categories_tracked: int = Field(..., ge=0, description="Number of categories")
    top_categories: List[CategorySpending] = Field(
        default_factory=list,
        max_length=10,
        description="Top spending categories"
    )
    high_flexibility_categories: List[FlexibilityCategory] = Field(
        default_factory=list,
        description="Categories with high spending flexibility"
    )
    low_flexibility_categories: List[FlexibilityCategory] = Field(
        default_factory=list,
        description="Categories with low flexibility (essential)"
    )
    impulse_score: ImpulseScore = Field(..., description="Impulse spending metrics")
    income_health: Optional[IncomeHealth] = Field(None, description="Income health metrics (freelancers)")
    data_quality: DataQuality = Field(..., description="Data quality metrics")
    rare_categories_count: int = Field(..., ge=0, description="Number of rare/unreliable categories")
    
    model_config = ConfigDict(frozen=True)


class RecommendationInsight(BaseModel):
    """Recommended scenario insight for comparison screen."""
    
    type: Literal['recommendation'] = Field(default='recommendation')
    title: str = Field(..., min_length=1, description="Insight title")
    subtitle: str = Field(..., min_length=1, description="Insight subtitle")
    monthly_savings: float = Field(..., ge=0, description="Monthly savings amount")
    annual_savings: float = Field(..., ge=0, description="Annual savings amount")
    difficulty_score: int = Field(..., ge=0, le=100, description="Difficulty score")
    difficulty_label: Literal['easy', 'moderate', 'challenging']
    confidence: Literal['high', 'moderate', 'low']
    top_categories: List[str] = Field(default_factory=list, max_length=5, description="Affected categories")
    
    model_config = ConfigDict(frozen=True)


class ScenarioOption(BaseModel):
    """A single scenario option in a comparison."""
    
    name: str = Field(..., min_length=1, description="Scenario name")
    monthly_savings: float = Field(..., ge=0, description="Monthly savings")
    annual_savings: float = Field(..., ge=0, description="Annual savings")
    difficulty_score: int = Field(..., ge=0, le=100, description="Difficulty score")
    label: str = Field(..., min_length=1, description="Descriptive label")
    
    model_config = ConfigDict(frozen=True)


class TradeOffInsight(BaseModel):
    """Trade-off comparison between easy and impactful scenarios."""
    
    type: Literal['trade_off'] = Field(default='trade_off')
    title: str = Field(default='Easiest vs Most Impactful', description="Section title")
    subtitle: str = Field(default='Two paths to consider', description="Section subtitle")
    easy_option: ScenarioOption = Field(..., description="Easiest scenario option")
    impact_option: ScenarioOption = Field(..., description="Highest impact scenario option")
    
    model_config = ConfigDict(frozen=True)


class DifficultyScenarioItem(BaseModel):
    """Individual scenario in difficulty breakdown."""
    
    name: str = Field(..., min_length=1, description="Scenario name")
    difficulty_score: int = Field(..., ge=0, le=100, description="Difficulty score")
    difficulty_label: Literal['easy', 'moderate', 'challenging']
    
    model_config = ConfigDict(frozen=True)


class DifficultyBreakdown(BaseModel):
    """Difficulty breakdown for all scenarios."""
    
    type: Literal['difficulty_breakdown'] = Field(default='difficulty_breakdown')
    title: str = Field(default='Effort Required', description="Section title")
    scenarios: List[DifficultyScenarioItem] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Scenarios with difficulty info"
    )
    
    model_config = ConfigDict(frozen=True)


class ComparisonInsightUnion(BaseModel):
    """Union type for different comparison insight types."""
    
    insights: List[RecommendationInsight | TradeOffInsight | DifficultyBreakdown] = Field(
        ...,
        description="Mixed list of insight types"
    )
    
    model_config = ConfigDict(frozen=True)


class RiskWarning(BaseModel):
    """Detailed risk warning with severity and recommendations."""
    
    type: str = Field(
        ...,
        description="Warning type: income_volatility, emergency_fund, impulse_spending, data_quality",
        min_length=1
    )
    severity: Literal['info', 'warning', 'high']
    title: str = Field(..., min_length=1, description="Warning title")
    message: str = Field(..., min_length=1, description="Warning message")
    recommendation: str = Field(..., min_length=1, description="Recommended action")
    metric: Optional[str] = Field(None, description="Related metric value")
    
    model_config = ConfigDict(frozen=True)


class QuickWinOpportunity(BaseModel):
    """Extended quick win with additional context."""
    
    category: str = Field(..., min_length=1, description="Display name")
    category_key: str = Field(..., min_length=1, description="Internal key")
    action: str = Field(..., min_length=1, description="Action description")
    monthly_savings: float = Field(..., ge=0, description="Monthly savings")
    annual_savings: float = Field(..., ge=0, description="Annual savings")
    difficulty: Literal['easy', 'moderate', 'challenging']
    reason: str = Field(..., min_length=1, description="Why this is a quick win")
    current_spending: float = Field(..., ge=0, description="Current spending")
    quick_win_score: float = Field(..., ge=0, description="Score for ranking (higher = better)")
    
    model_config = ConfigDict(frozen=True)


class DashboardInsight(BaseModel):
    """Complete dashboard insight response."""
    
    behavior_summary: BehaviorSummary = Field(..., description="User behavior overview")
    quick_wins: List[QuickWinOpportunity] = Field(
        default_factory=list,
        max_length=5,
        description="Top 3-5 quick win opportunities"
    )
    risk_warnings: List[RiskWarning] = Field(
        default_factory=list,
        description="Risk warnings and alerts"
    )
    recommended_actions: List[str] = Field(
        default_factory=list,
        max_length=5,
        description="Prioritized action items"
    )
    
    model_config = ConfigDict(frozen=True)


# Type aliases for clarity
ComparisonInsight = RecommendationInsight | TradeOffInsight | DifficultyBreakdown


# API Response Models
class DashboardInsightResponse(BaseModel):
    """API response for dashboard insights endpoint."""
    
    behavior_summary: BehaviorSummary
    quick_wins: List[QuickWinOpportunity]
    risk_warnings: List[RiskWarning]
    recommended_actions: List[str]
    
    model_config = ConfigDict(frozen=True)


class ScenarioSummary(BaseModel):
    """Summary of a scenario for comparison."""
    
    name: str
    monthly_impact: float
    annual_impact: float
    difficulty_score: int
    top_categories: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(frozen=True)


class ComparisonInsightResponse(BaseModel):
    """API response for scenario comparison insights."""
    
    recommendation: Optional[RecommendationInsight] = None
    trade_off: Optional[TradeOffInsight] = None
    difficulty_breakdown: Optional[DifficultyBreakdown] = None
    scenarios: List[ScenarioSummary] = Field(default_factory=list)
    
    model_config = ConfigDict(frozen=True)


class BehaviorSummaryResponse(BaseModel):
    """API response for behavior summary endpoint."""
    
    behavior_summary: BehaviorSummary
    
    model_config = ConfigDict(frozen=True)
