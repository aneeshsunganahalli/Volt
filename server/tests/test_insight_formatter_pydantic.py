"""
Tests for Pydantic-based InsightFormatter (Refactored)

Tests type safety, validation, business logic separation, and error handling.
"""
import pytest
from typing import Dict, Any
from pydantic import ValidationError

from app.services.insight_formatter_v2 import InsightFormatter
from app.services.insight_calculator import InsightCalculator
from app.config.insight_config import InsightConfig, InsightThresholds
from app.schemas.insights import (
    ScenarioInsight, QuickWin, Warning,
    BehaviorSummary, QuickWinOpportunity, RiskWarning
)
from app.models.behaviour import BehaviourModel


# Mock BehaviourModel for testing
class MockBehaviourModel:
    """Mock behavior model with configurable attributes."""
    
    def __init__(
        self,
        transaction_count: int = 100,
        impulse_score: float = 0.3,
        categories: Dict[str, Dict[str, Any]] = None,
        elasticity: Dict[str, float] = None
    ):
        self.transaction_count = transaction_count
        self.impulse_score = impulse_score
        self.elasticity = elasticity or {}
        self.categories = categories or {}
        
        # Mock category data if not provided
        if not self.categories:
            self.categories = {
                'GROCERIES': {
                    'mean': 500.0,
                    'std': 50.0,
                    'count': 30,
                    'total': 15000.0
                },
                'DINING': {
                    'mean': 300.0,
                    'std': 80.0,
                    'count': 25,
                    'total': 7500.0
                },
                'RENT': {
                    'mean': 1500.0,
                    'std': 10.0,
                    'count': 12,
                    'total': 18000.0
                }
            }
        
        if not self.elasticity:
            self.elasticity = {
                'GROCERIES': 0.7,
                'DINING': 0.8,
                'RENT': 0.1
            }
        
        # Create category_stats from categories (required by get_category_summary)
        self.category_stats = {}
        for cat, data in self.categories.items():
            self.category_stats[cat] = {
                'mean': data.get('mean', 0),
                'std_dev': data.get('std', 0),
                'count': data.get('count', 0),
                'min': data.get('mean', 0) * 0.5,
                'max': data.get('mean', 0) * 1.5,
                'total': data.get('total', data.get('mean', 0) * data.get('count', 1))
            }


class TestInsightCalculator:
    """Test business logic calculator methods."""
    
    @pytest.fixture
    def calculator(self):
        """Standard calculator with default config."""
        return InsightCalculator()
    
    def test_calculate_confidence_high(self, calculator):
        """Test high confidence calculation."""
        level, reason = calculator.calculate_confidence_level(95, 100)
        assert level == 'high'
        assert 'consistent spending patterns' in reason.lower()
    
    def test_calculate_confidence_moderate(self, calculator):
        """Test moderate confidence calculation."""
        level, reason = calculator.calculate_confidence_level(75, 100)
        assert level == 'moderate'
        assert 'achievable' in reason.lower()
    
    def test_calculate_confidence_low(self, calculator):
        """Test low confidence calculation."""
        level, reason = calculator.calculate_confidence_level(40, 100)
        assert level == 'low'
        assert 'significant' in reason.lower() or 'challenging' in reason.lower()
    
    def test_quick_win_score_easy_high_impact(self, calculator):
        """Test quick win scoring for easy high-impact changes."""
        score = calculator.calculate_quick_win_score(200, 'easy')
        assert score > 150  # High score for easy high-impact win
    
    def test_quick_win_score_challenging_low_impact(self, calculator):
        """Test quick win scoring for challenging low-impact changes."""
        score = calculator.calculate_quick_win_score(50, 'challenging')
        # challenging difficulty = 3, so score = 50/(3²) = 50/9 ≈ 5.56
        assert score < 10  # Low score for hard low-impact change
    
    def test_potential_savings_high_elasticity(self, calculator):
        """Test savings calculation for flexible categories."""
        savings = calculator.calculate_potential_savings(1000, 0.8)
        assert savings == pytest.approx(150.0, rel=0.01)  # 15% of 1000 (not multiplied by elasticity)
    
    def test_potential_savings_low_elasticity(self, calculator):
        """Test savings calculation for inflexible categories."""
        savings = calculator.calculate_potential_savings(1000, 0.1)
        assert savings == 0  # Below minimum threshold
    
    def test_potential_savings_below_threshold(self, calculator):
        """Test savings calculation below minimum spending."""
        savings = calculator.calculate_potential_savings(30, 0.9)
        assert savings == 0  # Below ₹50 threshold
    
    def test_income_volatility_stable(self, calculator):
        """Test stable income assessment."""
        status, message, months = calculator.assess_income_volatility(0.15)
        assert status == 'stable'
        assert months == 3
    
    def test_income_volatility_variable(self, calculator):
        """Test high volatility assessment."""
        status, message, months = calculator.assess_income_volatility(0.5)
        assert status == 'variable'
        assert months == 6
    
    def test_difficulty_label_mapping(self, calculator):
        """Test difficulty score to label mapping."""
        assert calculator.get_difficulty_label(20) == 'easy'
        assert calculator.get_difficulty_label(45) == 'moderate'
        assert calculator.get_difficulty_label(70) == 'challenging'
    
    def test_impulse_level_low(self, calculator):
        """Test low impulse score assessment."""
        level, message, rec = calculator.get_impulse_level(0.2)
        assert level == 'low'
        assert 'planned' in message.lower() or 'controlled' in message.lower()
    
    def test_impulse_level_high(self, calculator):
        """Test high impulse score assessment."""
        level, message, rec = calculator.get_impulse_level(0.8)
        assert level == 'high'
        assert rec is not None
    
    def test_emergency_fund_calculation(self, calculator):
        """Test emergency fund target calculation."""
        target, months = calculator.calculate_emergency_fund_target(2000, 0.5)
        assert target == 12000  # 6 months for high volatility
        assert months == 6
    
    def test_data_quality_high_confidence(self, calculator):
        """Test high confidence data quality."""
        confidence, message = calculator.assess_data_quality(200, 8, 10)
        assert confidence == 'high'
        assert 'strong' in message.lower()
    
    def test_data_quality_building(self, calculator):
        """Test low transaction count data quality."""
        confidence, message = calculator.assess_data_quality(30, 3, 5)
        assert confidence in ['building', 'moderate']
        assert 'building' in message.lower() or 'growing' in message.lower()
    
    def test_currency_formatting(self, calculator):
        """Test currency formatter."""
        assert calculator.format_currency(1234.56) == "₹1,235"
        assert calculator.format_currency(999999) == "₹999,999"
    
    def test_annual_impact(self, calculator):
        """Test annual impact calculation."""
        assert calculator.calculate_annual_impact(100) == 1200
        assert calculator.calculate_annual_impact(250.5) == 3006


class TestInsightFormatterPydantic:
    """Test Pydantic-based InsightFormatter."""
    
    @pytest.fixture
    def formatter(self):
        """Standard formatter with default config."""
        return InsightFormatter()
    
    @pytest.fixture
    def custom_formatter(self):
        """Formatter with custom thresholds."""
        config = InsightConfig(
            thresholds=InsightThresholds(
                confidence_high_threshold=0.85,
                quick_win_min_spending=100.0
            )
        )
        return InsightFormatter(config=config)
    
    @pytest.fixture
    def valid_simulation_result(self):
        """Valid simulation result for testing."""
        return {
            'total_change': -500,
            'achievable_percent': 85,
            'target_percent': 100,
            'feasibility': 'highly_achievable',
            'category_breakdown': {
                'GROCERIES': {
                    'current_avg': 500,
                    'new_avg': 400,
                    'monthly_savings': -100,
                    'achievable_reduction_pct': 20,
                    'difficulty': 'easy'
                },
                'DINING': {
                    'current_avg': 300,
                    'new_avg': 200,
                    'monthly_savings': -100,
                    'achievable_reduction_pct': 33,
                    'difficulty': 'moderate'
                }
            }
        }
    
    def test_format_scenario_summary_returns_pydantic_model(self, formatter, valid_simulation_result):
        """Test that format_scenario_summary returns ScenarioInsight."""
        result = formatter.format_scenario_summary(valid_simulation_result)
        assert isinstance(result, ScenarioInsight)
    
    def test_format_scenario_summary_validates_output(self, formatter, valid_simulation_result):
        """Test output validation with Pydantic."""
        result = formatter.format_scenario_summary(valid_simulation_result)
        
        # Pydantic ensures these are validated
        assert result.confidence in ['high', 'moderate', 'low']
        assert isinstance(result.quick_wins, list)
        assert isinstance(result.warnings, list)
        assert result.achievability_score >= 0
        assert result.achievability_score <= 100
    
    def test_format_scenario_summary_missing_required_field(self, formatter):
        """Test error handling for missing required fields."""
        invalid_result = {'total_change': -500}
        
        with pytest.raises(ValueError) as exc_info:
            formatter.format_scenario_summary(invalid_result)
        
        assert 'missing required fields' in str(exc_info.value)
    
    def test_format_scenario_summary_empty_input(self, formatter):
        """Test error handling for empty input."""
        with pytest.raises(ValueError) as exc_info:
            formatter.format_scenario_summary({})
        
        assert 'cannot be None or empty' in str(exc_info.value)
    
    def test_quick_wins_are_validated_pydantic_models(self, formatter, valid_simulation_result):
        """Test that quick wins are validated QuickWin objects."""
        result = formatter.format_scenario_summary(valid_simulation_result)
        
        for qw in result.quick_wins:
            assert isinstance(qw, QuickWin)
            assert qw.monthly_impact >= 0
            assert qw.difficulty in ['easy', 'moderate', 'challenging']
            assert qw.current_spending >= 0
    
    def test_quick_wins_sorted_by_score(self, formatter, valid_simulation_result):
        """Test quick wins are sorted by calculated score."""
        result = formatter.format_scenario_summary(valid_simulation_result)
        
        # Extract scores (easy difficulty should score higher)
        if len(result.quick_wins) >= 2:
            scores = [
                formatter.calculator.calculate_quick_win_score(qw.monthly_impact, qw.difficulty)
                for qw in result.quick_wins
            ]
            assert scores == sorted(scores, reverse=True)
    
    def test_warnings_are_validated_pydantic_models(self, formatter, valid_simulation_result):
        """Test that warnings are validated Warning objects."""
        result = formatter.format_scenario_summary(valid_simulation_result)
        
        for warning in result.warnings:
            assert isinstance(warning, Warning)
            assert warning.type in ['optimization', 'income_risk', 'data_quality']
            assert warning.severity in ['info', 'warning', 'high']
    
    def test_custom_thresholds_affect_confidence(self, custom_formatter, valid_simulation_result):
        """Test that custom thresholds change behavior."""
        result = custom_formatter.format_scenario_summary(valid_simulation_result)
        
        # With 85% threshold, 85% achievable should be high confidence
        assert result.confidence == 'high'
    
    def test_format_behavior_summary_returns_pydantic_model(self, formatter):
        """Test behavior summary returns validated model."""
        model = MockBehaviourModel(transaction_count=150)
        result = formatter.format_behavior_summary(model)
        
        assert isinstance(result, BehaviorSummary)
        assert result.transaction_count == 150
        assert result.categories_tracked > 0
    
    def test_format_behavior_summary_with_income_stats(self, formatter):
        """Test behavior summary includes income health."""
        model = MockBehaviourModel()
        income_stats = {
            'avg_monthly_income': 5000,
            'volatility_coefficient': 0.35
        }
        
        result = formatter.format_behavior_summary(model, income_stats)
        assert result.income_health is not None
        assert result.income_health.avg_monthly == 5000
        assert result.income_health.status in ['stable', 'moderate', 'variable']
    
    def test_get_quick_wins_returns_list_of_pydantic_models(self, formatter):
        """Test quick wins returns validated QuickWinOpportunity objects."""
        model = MockBehaviourModel()
        results = formatter.get_quick_wins(model)
        
        assert isinstance(results, list)
        for qw in results:
            assert isinstance(qw, QuickWinOpportunity)
            assert qw.monthly_savings >= 0
            assert qw.annual_savings >= 0
    
    def test_get_quick_wins_filters_low_spending(self, formatter):
        """Test quick wins filters categories below threshold."""
        model = MockBehaviourModel()
        model.categories['LOW_SPENDING'] = {
            'mean': 20.0,  # Below ₹50 threshold
            'std': 5.0,
            'count': 10,
            'total': 200.0
        }
        model.elasticity['LOW_SPENDING'] = 0.9
        
        results = formatter.get_quick_wins(model)
        
        # Should not include LOW_SPENDING
        assert all(qw.category_key != 'LOW_SPENDING' for qw in results)
    
    def test_get_risk_warnings_returns_pydantic_models(self, formatter):
        """Test risk warnings returns validated RiskWarning objects."""
        model = MockBehaviourModel(impulse_score=0.8)
        results = formatter.get_risk_warnings(model)
        
        assert isinstance(results, list)
        for warning in results:
            assert isinstance(warning, RiskWarning)
            assert warning.severity in ['info', 'warning', 'high']
    
    def test_risk_warnings_include_income_volatility(self, formatter):
        """Test income volatility generates warning."""
        model = MockBehaviourModel()
        income_stats = {'volatility_coefficient': 0.5}
        
        warnings = formatter.get_risk_warnings(model, income_stats)
        
        # Should have income volatility warning
        assert any(w.type == 'income_volatility' for w in warnings)
    
    def test_risk_warnings_include_impulse_spending(self, formatter):
        """Test high impulse score generates warning."""
        model = MockBehaviourModel(impulse_score=0.85)
        
        warnings = formatter.get_risk_warnings(model)
        
        # Should have impulse warning
        assert any(w.type == 'impulse_spending' for w in warnings)
    
    def test_risk_warnings_include_data_quality(self, formatter):
        """Test low transaction count generates info."""
        model = MockBehaviourModel(transaction_count=20)
        
        warnings = formatter.get_risk_warnings(model)
        
        # Should have data quality info
        assert any(w.type == 'data_quality' for w in warnings)
    
    def test_pydantic_validation_catches_bad_data(self, formatter):
        """Test Pydantic validation prevents invalid data."""
        # This should fail validation if we try to create invalid QuickWin
        with pytest.raises(ValidationError):
            QuickWin(
                category="Test",
                category_key="TEST",
                action="Reduce",
                monthly_impact=-50,  # Negative not allowed
                annual_impact=600,
                difficulty='invalid',  # Not a valid literal
                difficulty_color='#00FF00',
                icon='🛒',
                current_spending=100,
                new_spending=50
            )
    
    def test_format_comparison_insights_returns_pydantic_models(self, formatter):
        """Test comparison insights returns validated models."""
        comparison_result = {
            'scenarios': [
                {
                    'scenario_id': 'moderate',
                    'name': 'Moderate Savings',
                    'total_change': -400,
                    'annual_impact': -4800,
                    'difficulty_score': 35,
                    'feasibility': 'highly_achievable',
                    'key_insight': 'Balanced approach',
                    'top_affected_categories': ['GROCERIES', 'DINING']
                },
                {
                    'scenario_id': 'aggressive',
                    'name': 'Aggressive Savings',
                    'total_change': -800,
                    'annual_impact': -9600,
                    'difficulty_score': 65,
                    'feasibility': 'moderate',
                    'key_insight': 'High impact',
                    'top_affected_categories': ['GROCERIES', 'DINING', 'ENTERTAINMENT']
                }
            ],
            'recommended_scenario_id': 'moderate'
        }
        
        insights = formatter.format_comparison_insights(comparison_result)
        
        assert isinstance(insights, list)
        assert len(insights) > 0
        
        # Should include recommendation
        from app.schemas.insights import RecommendationInsight
        assert any(isinstance(i, RecommendationInsight) for i in insights)
    
    def test_error_logging_doesnt_crash_on_invalid_item(self, formatter, valid_simulation_result, caplog):
        """Test that invalid items are logged but don't crash the formatter."""
        # Add invalid category data with ValidationError (not ValueError)
        valid_simulation_result['category_breakdown']['INVALID'] = {
            'current_avg': 500,
            'new_avg': 400,
            'monthly_savings': -100,
            'achievable_reduction_pct': 20,
            'difficulty': 'invalid_difficulty'  # This will cause ValidationError
        }
        
        # Should still complete successfully
        result = formatter.format_scenario_summary(valid_simulation_result)
        assert isinstance(result, ScenarioInsight)
        
        # Should have logged warning
        assert any('Invalid quick win' in record.message for record in caplog.records)
    
    def test_frozen_models_are_immutable(self, formatter, valid_simulation_result):
        """Test that returned models are immutable."""
        result = formatter.format_scenario_summary(valid_simulation_result)
        
        # Try to modify frozen model
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            result.confidence = 'modified'
    
    def test_calculator_can_be_injected(self):
        """Test that custom calculator can be injected."""
        custom_calc = InsightCalculator(
            thresholds=InsightThresholds(confidence_high_threshold=0.95)
        )
        formatter = InsightFormatter(calculator=custom_calc)
        
        assert formatter.calculator is custom_calc
        assert formatter.calculator.thresholds.confidence_high_threshold == 0.95


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""
    
    @pytest.fixture
    def formatter(self):
        return InsightFormatter()
    
    def test_complete_dashboard_workflow(self, formatter):
        """Test complete dashboard data generation."""
        model = MockBehaviourModel(
            transaction_count=150,
            impulse_score=0.4
        )
        income_stats = {
            'avg_monthly_income': 5000,
            'volatility_coefficient': 0.25
        }
        
        # Generate all dashboard components
        summary = formatter.format_behavior_summary(model, income_stats)
        quick_wins = formatter.get_quick_wins(model)
        warnings = formatter.get_risk_warnings(model, income_stats)
        
        # Verify all are Pydantic models
        assert isinstance(summary, BehaviorSummary)
        assert all(isinstance(qw, QuickWinOpportunity) for qw in quick_wins)
        assert all(isinstance(w, RiskWarning) for w in warnings)
        
        # Verify data completeness
        assert summary.total_monthly_spending > 0
        assert summary.income_health is not None
        assert len(quick_wins) > 0
    
    def test_simulation_to_frontend_workflow(self, formatter):
        """Test complete simulation response formatting."""
        simulation_result = {
            'total_change': -600,
            'achievable_percent': 90,
            'target_percent': 100,
            'feasibility': 'highly_achievable',
            'category_breakdown': {
                'GROCERIES': {
                    'current_avg': 600,
                    'new_avg': 450,
                    'monthly_savings': -150,
                    'achievable_reduction_pct': 25,
                    'difficulty': 'easy'
                },
                'ENTERTAINMENT': {
                    'current_avg': 400,
                    'new_avg': 250,
                    'monthly_savings': -150,
                    'achievable_reduction_pct': 37.5,
                    'difficulty': 'moderate'
                }
            }
        }
        
        result = formatter.format_scenario_summary(simulation_result)
        
        # Verify structure is frontend-ready
        assert isinstance(result, ScenarioInsight)
        assert '₹' in result.headline
        assert len(result.quick_wins) > 0
        assert result.annual_impact.startswith('₹')
        assert 0 <= result.achievability_score <= 100
