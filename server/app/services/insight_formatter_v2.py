"""
Insight Formatter Service (Refactored with Pydantic)

Converts behavior models and simulation results into type-safe, frontend-friendly insights.
Now uses Pydantic models for validation and InsightCalculator for business logic separation.
"""
from typing import Optional, List, Dict, Any
from pydantic import ValidationError
import logging

from app.schemas.insights import (
    ScenarioInsight, QuickWin, Warning,
    CategorySpending, FlexibilityCategory, ImpulseScore,
    IncomeHealth, DataQuality, BehaviorSummary,
    RecommendationInsight, TradeOffInsight, DifficultyBreakdown,
    ScenarioOption, DifficultyScenarioItem, QuickWinOpportunity,
    RiskWarning, DashboardInsight, ComparisonInsight
)
from app.services.insight_calculator import InsightCalculator
from app.config.insight_config import InsightThresholds, InsightConfig
from app.models.behaviour import BehaviourModel
from app.utils.category_utils import (
    get_category_reliability_score,
    identify_rare_categories,
    get_category_summary
)

logger = logging.getLogger(__name__)


class InsightFormatter:
    """
    Formats behavior models and simulation results into frontend-ready insights.
    
    Now type-safe with Pydantic models and separated business logic.
    All outputs are validated Pydantic models with guaranteed type safety.
    """
    
    def __init__(
        self,
        calculator: Optional[InsightCalculator] = None,
        config: Optional[InsightConfig] = None
    ):
        """
        Initialize formatter with optional custom configuration.
        
        Args:
            calculator: Business logic calculator (default: new instance with standard config)
            config: Complete insight configuration (default: standard values)
        """
        self.config = config or InsightConfig()
        self.calculator = calculator or InsightCalculator(
            thresholds=self.config.thresholds,
            timelines=self.config.timelines
        )
    
    def format_scenario_summary(
        self,
        simulation_result: Dict[str, Any],
        user_model: Optional[BehaviourModel] = None,
        income_stats: Optional[Dict[str, Any]] = None
    ) -> ScenarioInsight:
        """
        Convert simulation response into actionable frontend insights.
        
        Args:
            simulation_result: Raw simulation result dict
            user_model: User's behavior model for context
            income_stats: Income statistics for freelancers
            
        Returns:
            Type-safe ScenarioInsight with all required fields validated
            
        Raises:
            ValueError: If required fields missing from simulation_result
            ValidationError: If output data doesn't match Pydantic schema
            
        Example:
            >>> formatter = InsightFormatter()
            >>> result = formatter.format_scenario_summary({
            ...     'total_change': -500,
            ...     'achievable_percent': 85,
            ...     'target_percent': 100,
            ...     'feasibility': 'highly_achievable',
            ...     'category_breakdown': {}
            ... })
            >>> isinstance(result, ScenarioInsight)
            True
            >>> result.confidence
            'moderate'
        """
        # Validate inputs
        self._validate_simulation_result(simulation_result)
        
        # Extract values with safe defaults
        total_change = float(simulation_result.get('total_change', 0))
        achievable_percent = float(simulation_result.get('achievable_percent', 0))
        target_percent = float(simulation_result.get('target_percent', 0))
        feasibility = simulation_result.get('feasibility', 'unknown')
        category_breakdown = simulation_result.get('category_breakdown', {})
        
        # Use calculator for business logic
        confidence, confidence_reason = self.calculator.calculate_confidence_level(
            achievable_percent,
            target_percent
        )
        
        # Generate headline
        action_word = "Save" if total_change < 0 else "Increase"
        effort_level = feasibility.replace('_', ' ').title()
        headline = f"{action_word} ₹{abs(total_change):.0f}/month with {effort_level} changes"
        
        # Build quick wins with validation
        quick_wins = self._build_quick_wins(category_breakdown)
        
        # Build warnings with validation
        warnings = self._build_warnings(
            category_breakdown,
            income_stats,
            user_model
        )
        
        # Calculate timeline
        confidence_ratio = achievable_percent / target_percent if target_percent > 0 else 0
        timeline = self.calculator.estimate_timeline(confidence_ratio)
        
        # Calculate annual impact
        annual_impact_value = self.calculator.calculate_annual_impact(abs(total_change))
        annual_impact = self.calculator.format_currency(annual_impact_value)
        
        # Build and validate output
        try:
            return ScenarioInsight(
                headline=headline,
                confidence=confidence,
                confidence_reason=confidence_reason,
                quick_wins=quick_wins,
                warnings=warnings,
                timeline=timeline,
                visual_suggestion='category_breakdown_bar_chart',
                annual_impact=annual_impact,
                annual_impact_value=annual_impact_value,
                achievability_score=int(min(confidence_ratio * 100, 100)),
                total_categories_affected=len([
                    c for c in category_breakdown.values()
                    if float(c.get('monthly_savings', 0)) != 0
                ])
            )
        except ValidationError as e:
            logger.error(f"Failed to create ScenarioInsight: {e}")
            raise
    
    def format_comparison_insights(
        self,
        comparison_result: Dict[str, Any]
    ) -> List[ComparisonInsight]:
        """
        Format scenario comparison for frontend decision-making.
        
        Args:
            comparison_result: ScenarioComparisonResponse dict
            
        Returns:
            List of validated insight objects (recommendation, trade_off, difficulty_breakdown)
            
        Raises:
            ValidationError: If output doesn't match schemas
        """
        insights: List[ComparisonInsight] = []
        scenarios = comparison_result.get('scenarios', [])
        recommended_id = comparison_result.get('recommended_scenario_id')
        
        if not scenarios:
            logger.warning("No scenarios in comparison result")
            return insights
        
        # Find recommended scenario
        recommended = next(
            (s for s in scenarios if s.get('scenario_id') == recommended_id),
            scenarios[0]
        )
        
        # Build recommendation insight
        try:
            difficulty_score = int(recommended.get('difficulty_score', 50))
            difficulty_label = self.calculator.get_difficulty_label(difficulty_score)
            confidence = 'high' if recommended.get('feasibility') == 'highly_achievable' else 'moderate'
            
            recommendation = RecommendationInsight(
                title=f"We recommend: {recommended.get('name', 'Moderate Plan')}",
                subtitle=recommended.get('key_insight', 'Best balance of impact and feasibility'),
                monthly_savings=abs(float(recommended.get('total_change', 0))),
                annual_savings=abs(float(recommended.get('annual_impact', 0))),
                difficulty_score=difficulty_score,
                difficulty_label=difficulty_label,
                confidence=confidence,
                top_categories=recommended.get('top_affected_categories', [])[:3]
            )
            insights.append(recommendation)
        except (ValidationError, KeyError) as e:
            logger.warning(f"Failed to create recommendation insight: {e}")
        
        # Build trade-off insight
        try:
            easiest = min(scenarios, key=lambda s: s.get('difficulty_score', 100))
            most_impact = max(scenarios, key=lambda s: abs(float(s.get('annual_impact', 0))))
            
            if easiest.get('scenario_id') != most_impact.get('scenario_id'):
                trade_off = TradeOffInsight(
                    easy_option=ScenarioOption(
                        name=easiest.get('name', 'Easy Path'),
                        monthly_savings=abs(float(easiest.get('total_change', 0))),
                        annual_savings=abs(float(easiest.get('annual_impact', 0))),
                        difficulty_score=int(easiest.get('difficulty_score', 0)),
                        label='Low effort, steady progress'
                    ),
                    impact_option=ScenarioOption(
                        name=most_impact.get('name', 'Maximum Impact'),
                        monthly_savings=abs(float(most_impact.get('total_change', 0))),
                        annual_savings=abs(float(most_impact.get('annual_impact', 0))),
                        difficulty_score=int(most_impact.get('difficulty_score', 0)),
                        label='Higher effort, bigger reward'
                    )
                )
                insights.append(trade_off)
        except (ValidationError, KeyError, ValueError) as e:
            logger.warning(f"Failed to create trade-off insight: {e}")
        
        # Build difficulty breakdown
        try:
            difficulty_items = []
            for scenario in scenarios:
                difficulty_score = int(scenario.get('difficulty_score', 50))
                difficulty_label = self.calculator.get_difficulty_label(difficulty_score)
                
                difficulty_items.append(DifficultyScenarioItem(
                    name=scenario.get('name', 'Scenario'),
                    difficulty_score=difficulty_score,
                    difficulty_label=difficulty_label
                ))
            
            if difficulty_items:
                difficulty_breakdown = DifficultyBreakdown(scenarios=difficulty_items)
                insights.append(difficulty_breakdown)
        except (ValidationError, KeyError) as e:
            logger.warning(f"Failed to create difficulty breakdown: {e}")
        
        return insights
    
    def format_behavior_summary(
        self,
        model: BehaviourModel,
        income_stats: Optional[Dict[str, Any]] = None
    ) -> BehaviorSummary:
        """
        Format user's behavior model into dashboard insights.
        
        Args:
            model: User's BehaviourModel
            income_stats: Optional income statistics
            
        Returns:
            Validated BehaviorSummary with all metrics
            
        Raises:
            ValidationError: If output doesn't match schema
        """
        category_summary = get_category_summary(model)
        rare_categories = identify_rare_categories(model)
        
        # Build top categories
        top_categories = self._build_top_categories(category_summary)
        
        # Build flexibility categories
        high_flex, low_flex = self._build_flexibility_categories(category_summary, model)
        
        # Build impulse score
        impulse_score = self._build_impulse_score(model.impulse_score)
        
        # Build income health (if available)
        income_health = None
        if income_stats:
            income_health = self._build_income_health(income_stats, category_summary)
        
        # Build data quality
        data_quality = self._build_data_quality(model, category_summary)
        
        # Calculate total spending
        total_monthly = sum(
            stats.get('mean', 0)
            for stats in category_summary.values()
            if not stats.get('is_rare', False)
        )
        
        try:
            return BehaviorSummary(
                total_monthly_spending=total_monthly,
                transaction_count=model.transaction_count,
                categories_tracked=len(category_summary),
                top_categories=top_categories,
                high_flexibility_categories=high_flex,
                low_flexibility_categories=low_flex,
                impulse_score=impulse_score,
                income_health=income_health,
                data_quality=data_quality,
                rare_categories_count=len(rare_categories)
            )
        except ValidationError as e:
            logger.error(f"Failed to create BehaviorSummary: {e}")
            raise
    
    def get_quick_wins(
        self,
        model: BehaviourModel
    ) -> List[QuickWinOpportunity]:
        """
        Identify top quick win opportunities for the user.
        
        Args:
            model: User's BehaviourModel
            
        Returns:
            List of up to 5 validated QuickWinOpportunity objects
        """
        category_summary = get_category_summary(model)
        quick_wins = []
        
        for cat, stats in category_summary.items():
            if stats.get('is_rare', False) or not stats.get('include_in_simulation', False):
                continue
            
            elasticity = model.elasticity.get(cat, 0) if model.elasticity else 0
            monthly_avg = stats.get('mean', 0)
            
            # Use calculator for potential savings
            potential_savings = self.calculator.calculate_potential_savings(monthly_avg, elasticity)
            
            if potential_savings > 0:
                # Determine difficulty based on elasticity
                if elasticity > self.config.thresholds.elasticity_high_flexibility:
                    difficulty = 'easy'
                elif elasticity > self.config.thresholds.elasticity_low_flexibility:
                    difficulty = 'moderate'
                else:
                    difficulty = 'challenging'
                
                # Calculate quick win score
                score = self.calculator.calculate_quick_win_score(potential_savings, difficulty)
                
                try:
                    quick_win = QuickWinOpportunity(
                        category=cat.replace('_', ' ').title(),
                        category_key=cat,
                        action=f"Reduce by {int(self.config.thresholds.quick_win_reduction_percent * 100)}%",
                        monthly_savings=potential_savings,
                        annual_savings=self.calculator.calculate_annual_impact(potential_savings),
                        difficulty=difficulty,
                        reason=f"High flexibility in this category",
                        current_spending=monthly_avg,
                        quick_win_score=score
                    )
                    quick_wins.append(quick_win)
                except ValidationError as e:
                    logger.warning(f"Invalid quick win for {cat}: {e}")
                    continue
        
        # Sort by score and return top N
        quick_wins.sort(key=lambda x: x.quick_win_score, reverse=True)
        return quick_wins[:self.config.thresholds.quick_win_max_results]
    
    def get_risk_warnings(
        self,
        model: BehaviourModel,
        income_stats: Optional[Dict[str, Any]] = None
    ) -> List[RiskWarning]:
        """
        Identify financial risks and generate warnings.
        
        Args:
            model: User's BehaviourModel
            income_stats: Optional income statistics
            
        Returns:
            List of validated RiskWarning objects
        """
        warnings = []
        
        # Income volatility warning
        if income_stats:
            volatility = income_stats.get('volatility_coefficient', 0)
            avg_income = income_stats.get('mean', 0)
            status, message, months = self.calculator.assess_income_volatility(volatility)
            
            if status in ['variable', 'moderate']:
                severity = 'high' if status == 'variable' else 'warning'
                emergency_months = (self.config.thresholds.emergency_fund_months_high_volatility 
                                   if volatility > self.config.thresholds.volatility_high_threshold 
                                   else self.config.thresholds.emergency_fund_months_moderate_volatility)
                target_fund = avg_income * emergency_months
                
                try:
                    warning = RiskWarning(
                        type='income_volatility',
                        severity=severity,
                        title='High Income Variability' if status == 'variable' else 'Moderate Income Variability',
                        message=f"Your income varies by {volatility:.0%} month-to-month",
                        recommendation=f"Build a {emergency_months}-month emergency fund (₹{target_fund:,.0f}). Save extra during high-income months to buffer lean periods.",
                        metric=f"{volatility * 100:.0f}% income volatility"
                    )
                    warnings.append(warning)
                except ValidationError as e:
                    logger.warning(f"Invalid income warning: {e}")
        
        # High impulse score warning
        if model.impulse_score > self.config.thresholds.impulse_high_threshold:
            level, message, recommendation = self.calculator.get_impulse_level(model.impulse_score)
            
            try:
                warning = RiskWarning(
                    type='impulse_spending',
                    severity='warning',
                    title='Frequent Impulse Purchases',
                    message=message,
                    recommendation=recommendation or 'Track purchases before buying'
                )
                warnings.append(warning)
            except ValidationError as e:
                logger.warning(f"Invalid impulse warning: {e}")
        
        # Limited data warning
        if model.transaction_count < self.config.thresholds.min_transactions_for_building_confidence:
            confidence, message = self.calculator.assess_data_quality(
                model.transaction_count,
                0,  # Will be calculated properly in full implementation
                0
            )
            
            try:
                warning = RiskWarning(
                    type='data_quality',
                    severity='info',
                    title='Building Your Profile',
                    message=message,
                    recommendation='Continue using the app for better personalized insights'
                )
                warnings.append(warning)
            except ValidationError as e:
                logger.warning(f"Invalid data quality warning: {e}")
        
        return warnings
    
    # Private helper methods
    
    def _validate_simulation_result(self, result: Dict[str, Any]) -> None:
        """Validate simulation result has required fields."""
        if not result:
            raise ValueError("simulation_result cannot be None or empty")
        
        required_fields = ['total_change', 'achievable_percent', 'target_percent']
        missing = [f for f in required_fields if f not in result]
        
        if missing:
            raise ValueError(
                f"simulation_result missing required fields: {missing}"
            )
    
    def _build_quick_wins(
        self,
        category_breakdown: Dict[str, Any]
    ) -> List[QuickWin]:
        """
        Build list of quick win opportunities from category breakdown.
        
        Returns:
            List of up to 3 validated QuickWin objects, sorted by quick win score
        """
        quick_wins = []
        category_items = []
        
        for cat_name, analysis in category_breakdown.items():
            difficulty = analysis.get('difficulty', 'moderate')
            monthly_savings = float(analysis.get('monthly_savings', 0))
            
            if monthly_savings == 0:
                continue
            
            # Use calculator for scoring
            score = self.calculator.calculate_quick_win_score(monthly_savings, difficulty)
            category_items.append((cat_name, analysis, score))
        
        # Sort by score
        category_items.sort(key=lambda x: x[2], reverse=True)
        
        # Build QuickWin objects for top 3
        for cat_name, analysis, _ in category_items[:3]:
            try:
                monthly_impact = abs(float(analysis.get('monthly_savings', 0)))
                quick_win = QuickWin(
                    category=cat_name.replace('_', ' ').title(),
                    category_key=cat_name,
                    action=f"Cut by {analysis.get('achievable_reduction_pct', 0):.0f}%",
                    monthly_impact=monthly_impact,
                    annual_impact=self.calculator.calculate_annual_impact(monthly_impact),
                    difficulty=analysis.get('difficulty', 'moderate'),
                    current_spending=float(analysis.get('current_avg', 0)),
                    new_spending=float(analysis.get('new_avg', 0))
                )
                quick_wins.append(quick_win)
            except ValidationError as e:
                logger.warning(f"Invalid quick win for {cat_name}: {e}")
                continue
        
        return quick_wins
    
    def _build_warnings(
        self,
        category_breakdown: Dict[str, Any],
        income_stats: Optional[Dict[str, Any]],
        user_model: Optional[BehaviourModel]
    ) -> List[Warning]:
        """Build list of warnings from various data sources."""
        warnings = []
        
        # Category optimization warnings
        for cat_name, analysis in category_breakdown.items():
            if analysis.get('difficulty') == 'challenging':
                try:
                    warning = Warning(
                        type='optimization',
                        message=f"{cat_name.replace('_', ' ').title()} is already optimized - limited savings possible",
                        severity='info'
                    )
                    warnings.append(warning)
                except ValidationError as e:
                    logger.warning(f"Invalid warning for {cat_name}: {e}")
        
        # Income volatility warnings
        if income_stats:
            volatility = income_stats.get('volatility_coefficient', 0)
            status, message, months = self.calculator.assess_income_volatility(volatility)
            
            if status in ['variable', 'moderate']:
                severity = 'warning' if status == 'variable' else 'info'
                try:
                    warning = Warning(
                        type='income_risk',
                        message=f"{message} - prioritize {months}-month emergency fund",
                        severity=severity,
                        metric=f"{volatility * 100:.0f}% income volatility"
                    )
                    warnings.append(warning)
                except ValidationError as e:
                    logger.warning(f"Invalid income warning: {e}")
        
        return warnings
    
    def _build_top_categories(
        self,
        category_summary: Dict[str, Any]
    ) -> List[CategorySpending]:
        """Build top spending categories list."""
        categories = []
        
        for cat, stats in category_summary.items():
            if stats.get('is_rare', False):
                continue
            
            try:
                category = CategorySpending(
                    category=cat.replace('_', ' ').title(),
                    category_key=cat,
                    monthly_avg=stats.get('mean', 0),
                    transaction_count=stats.get('count', 0),
                    reliability_score=stats.get('reliability_score', 0)
                )
                categories.append(category)
            except ValidationError as e:
                logger.warning(f"Invalid category {cat}: {e}")
        
        # Sort by spending and return top 5
        categories.sort(key=lambda x: x.monthly_avg, reverse=True)
        return categories[:5]
    
    def _build_flexibility_categories(
        self,
        category_summary: Dict[str, Any],
        model: BehaviourModel
    ) -> tuple[List[FlexibilityCategory], List[FlexibilityCategory]]:
        """Build high and low flexibility category lists."""
        high_flex = []
        low_flex = []
        
        for cat, stats in category_summary.items():
            if stats.get('is_rare', False):
                continue
            
            reliability = stats.get('reliability_score', 0)
            if reliability <= self.config.thresholds.reliability_established_threshold:
                continue
            
            elasticity = model.elasticity.get(cat, 0) if model.elasticity else 0
            
            try:
                flex_cat = FlexibilityCategory(
                    category=cat.replace('_', ' ').title(),
                    category_key=cat,
                    monthly_avg=stats.get('mean', 0),
                    elasticity=elasticity,
                    flexibility_label='high' if self.calculator.is_category_flexible(elasticity) else 'low'
                )
                
                if self.calculator.is_category_flexible(elasticity):
                    high_flex.append(flex_cat)
                elif self.calculator.is_category_essential(elasticity):
                    low_flex.append(flex_cat)
            except ValidationError as e:
                logger.warning(f"Invalid flexibility category {cat}: {e}")
        
        return high_flex[:3], low_flex[:3]
    
    def _build_impulse_score(self, score: float) -> ImpulseScore:
        """Build impulse score object."""
        level, message, recommendation = self.calculator.get_impulse_level(score)
        
        return ImpulseScore(
            value=score,
            level=level,
            message=message,
            recommendation=recommendation
        )
    
    def _build_income_health(
        self,
        income_stats: Dict[str, Any],
        category_summary: Dict[str, Any]
    ) -> IncomeHealth:
        """Build income health object."""
        volatility = income_stats.get('volatility_coefficient', 0)
        avg_income = income_stats.get('avg_monthly_income', 0)
        status, message, months = self.calculator.assess_income_volatility(volatility)
        
        # Calculate total monthly expenses
        total_expenses = sum(
            stats.get('mean', 0)
            for stats in category_summary.values()
            if not stats.get('is_rare', False)
        )
        
        # Calculate emergency fund target
        target, _ = self.calculator.calculate_emergency_fund_target(total_expenses, volatility)
        
        return IncomeHealth(
            status=status,
            message=message,
            volatility_percent=int(volatility * 100),
            avg_monthly=avg_income,
            recommendation=f"Target emergency fund: ₹{target:,.0f} ({months} months coverage)",
            emergency_fund_target=target,
            emergency_fund_months=months
        )
    
    def _build_data_quality(
        self,
        model: BehaviourModel,
        category_summary: Dict[str, Any]
    ) -> DataQuality:
        """Build data quality object."""
        reliable_count = len([
            c for c in category_summary.values()
            if c.get('is_established', False)
        ])
        total_count = len(category_summary)
        
        confidence, message = self.calculator.assess_data_quality(
            model.transaction_count,
            reliable_count,
            total_count
        )
        
        return DataQuality(
            reliable_categories=reliable_count,
            total_categories=total_count,
            transaction_count=model.transaction_count,
            confidence=confidence,
            message=message
        )
