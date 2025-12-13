"""
Business logic calculator for insights.

Separates calculation logic from formatting logic for testability and maintainability.
All business rules are configurable through InsightThresholds.
"""
from typing import Literal, Optional, Tuple
import logging

from app.config.insight_config import InsightThresholds, TimelineConfig

logger = logging.getLogger(__name__)


class InsightCalculator:
    """
    Business logic for calculating insights, scores, and recommendations.
    
    This class is stateless except for configuration and can be easily tested.
    """
    
    # Difficulty weight mapping for quick win scoring
    DIFFICULTY_WEIGHTS = {
        'easy': 1,
        'moderate': 2,
        'challenging': 3
    }
    
    def __init__(
        self,
        thresholds: Optional[InsightThresholds] = None,
        timelines: Optional[TimelineConfig] = None
    ):
        """
        Initialize calculator with optional custom configuration.
        
        Args:
            thresholds: Custom business rule thresholds (default: standard values)
            timelines: Custom timeline messages (default: standard messages)
        """
        self.thresholds = thresholds or InsightThresholds()
        self.timelines = timelines or TimelineConfig()
    
    def calculate_confidence_level(
        self,
        achievable_percent: float,
        target_percent: float
    ) -> Tuple[Literal['high', 'moderate', 'low'], str]:
        """
        Determine confidence level and reason based on achievability.
        
        Args:
            achievable_percent: Percentage achievable (0-100)
            target_percent: Target percentage (0-100)
            
        Returns:
            Tuple of (confidence_level, reason_text)
            
        Example:
            >>> calc = InsightCalculator()
            >>> level, reason = calc.calculate_confidence_level(90, 100)
            >>> level
            'high'
            >>> 'consistent' in reason.lower()
            True
        """
        if target_percent <= 0:
            return 'low', 'No target specified'
        
        ratio = achievable_percent / target_percent
        
        if ratio >= self.thresholds.confidence_high_threshold:
            return 'high', 'Based on your consistent spending patterns'
        elif ratio >= self.thresholds.confidence_moderate_threshold:
            return 'moderate', 'Achievable with some lifestyle adjustments'
        else:
            return 'low', 'Requires significant behavior changes'
    
    def calculate_quick_win_score(
        self,
        monthly_savings: float,
        difficulty: Literal['easy', 'moderate', 'challenging']
    ) -> float:
        """
        Calculate quick win score: high impact + low difficulty = best opportunity.
        
        Formula: impact / difficulty²
        - Easy (1²=1): Full impact score (100%)
        - Moderate (2²=4): 25% of impact score
        - Challenging (3²=9): 11% of impact score
        
        Args:
            monthly_savings: Monthly savings amount (can be negative)
            difficulty: Difficulty level
            
        Returns:
            Quick win score (higher = better opportunity)
            
        Example:
            >>> calc = InsightCalculator()
            >>> calc.calculate_quick_win_score(500, 'easy')
            500.0
            >>> calc.calculate_quick_win_score(500, 'moderate')
            125.0
            >>> calc.calculate_quick_win_score(500, 'challenging')
            55.55555555555556
        """
        difficulty_score = self.DIFFICULTY_WEIGHTS.get(difficulty, 2)
        return abs(monthly_savings) / (difficulty_score ** 2)
    
    def calculate_potential_savings(
        self,
        monthly_avg: float,
        elasticity: float
    ) -> float:
        """
        Calculate potential savings for a category based on elasticity and spending.
        
        Uses conservative reduction percentage (default 15%) for high-elasticity
        categories above minimum spending threshold.
        
        Args:
            monthly_avg: Average monthly spending
            elasticity: Spending elasticity/flexibility (0-1)
            
        Returns:
            Potential monthly savings amount
            
        Example:
            >>> calc = InsightCalculator()
            >>> calc.calculate_potential_savings(200.0, 0.7)  # High elasticity
            30.0
            >>> calc.calculate_potential_savings(200.0, 0.3)  # Low elasticity
            0.0
            >>> calc.calculate_potential_savings(30.0, 0.7)   # Below threshold
            0.0
        """
        if (elasticity > self.thresholds.elasticity_high_flexibility and
            monthly_avg > self.thresholds.quick_win_min_spending):
            return monthly_avg * self.thresholds.quick_win_reduction_percent
        return 0.0
    
    def estimate_timeline(self, confidence_ratio: float) -> str:
        """
        Estimate timeline for achieving scenario based on confidence ratio.
        
        Args:
            confidence_ratio: Ratio of achievable to target (0-1+)
            
        Returns:
            Timeline message string
            
        Example:
            >>> calc = InsightCalculator()
            >>> calc.estimate_timeline(0.95)
            'Achievable within 2-3 weeks'
            >>> calc.estimate_timeline(0.75)
            'Achievable within 1-2 months'
            >>> calc.estimate_timeline(0.50)
            'Requires 3+ months of habit adjustment'
        """
        if confidence_ratio >= self.thresholds.confidence_high_threshold:
            return self.timelines.high_confidence_timeline
        elif confidence_ratio >= self.thresholds.confidence_moderate_threshold:
            return self.timelines.moderate_confidence_timeline
        else:
            return self.timelines.low_confidence_timeline
    
    def assess_income_volatility(
        self,
        volatility: float
    ) -> Tuple[Literal['stable', 'moderate', 'variable'], str, int]:
        """
        Assess income health based on coefficient of variation.
        
        Args:
            volatility: Income volatility coefficient (CV = std/mean)
            
        Returns:
            Tuple of (status, message, recommended_emergency_months)
            
        Example:
            >>> calc = InsightCalculator()
            >>> status, msg, months = calc.assess_income_volatility(0.5)
            >>> status
            'variable'
            >>> months
            6
        """
        if volatility > self.thresholds.volatility_high_threshold:
            return (
                'variable',
                'Income varies significantly month-to-month',
                self.thresholds.emergency_fund_months_high_volatility
            )
        elif volatility > self.thresholds.volatility_moderate_threshold:
            return (
                'moderate',
                'Income has some variation',
                self.thresholds.emergency_fund_months_moderate_volatility
            )
        else:
            return (
                'stable',
                'Income is consistent',
                self.thresholds.emergency_fund_months_stable
            )
    
    def get_difficulty_label(
        self,
        score: int
    ) -> Literal['easy', 'moderate', 'challenging']:
        """
        Convert numeric difficulty score to label.
        
        Args:
            score: Difficulty score (0-100)
            
        Returns:
            Difficulty label
            
        Example:
            >>> calc = InsightCalculator()
            >>> calc.get_difficulty_label(25)
            'easy'
            >>> calc.get_difficulty_label(45)
            'moderate'
            >>> calc.get_difficulty_label(75)
            'challenging'
        """
        if score <= self.thresholds.difficulty_easy_max:
            return 'easy'
        elif score <= self.thresholds.difficulty_moderate_max:
            return 'moderate'
        else:
            return 'challenging'
    
    def get_impulse_level(
        self,
        score: float
    ) -> Tuple[Literal['low', 'moderate', 'high'], str, Optional[str]]:
        """
        Assess impulse spending level and provide interpretation.
        
        Args:
            score: Impulse score (0-1)
            
        Returns:
            Tuple of (level, message, recommendation)
            
        Example:
            >>> calc = InsightCalculator()
            >>> level, msg, rec = calc.get_impulse_level(0.8)
            >>> level
            'high'
            >>> '24-hour' in rec
            True
        """
        if score > self.thresholds.impulse_high_threshold:
            return (
                'high',
                'You have frequent impulse purchases',
                'Consider implementing a 24-hour waiting rule for non-essential purchases'
            )
        elif score > self.thresholds.impulse_moderate_threshold:
            return (
                'moderate',
                'Occasional impulse purchases detected',
                'Try tracking purchases before buying to increase awareness'
            )
        else:
            return (
                'low',
                'Your spending is well-planned',
                None
            )
    
    def calculate_emergency_fund_target(
        self,
        monthly_spending: float,
        volatility: float
    ) -> Tuple[float, int]:
        """
        Calculate recommended emergency fund amount.
        
        Args:
            monthly_spending: Average monthly spending
            volatility: Income volatility coefficient
            
        Returns:
            Tuple of (target_amount, months_coverage)
            
        Example:
            >>> calc = InsightCalculator()
            >>> amount, months = calc.calculate_emergency_fund_target(3500, 0.5)
            >>> months
            6
            >>> amount
            21000.0
        """
        _, _, months = self.assess_income_volatility(volatility)
        return monthly_spending * months, months
    
    def assess_data_quality(
        self,
        transaction_count: int,
        reliable_categories: int,
        total_categories: int
    ) -> Tuple[Literal['high', 'building', 'low'], str]:
        """
        Assess data quality and confidence based on transaction history.
        
        Args:
            transaction_count: Number of transactions
            reliable_categories: Number of reliable/established categories
            total_categories: Total categories tracked
            
        Returns:
            Tuple of (confidence_level, message)
            
        Example:
            >>> calc = InsightCalculator()
            >>> conf, msg = calc.assess_data_quality(100, 8, 10)
            >>> conf
            'high'
        """
        if transaction_count >= self.thresholds.min_transactions_for_high_confidence:
            reliability_ratio = reliable_categories / total_categories if total_categories > 0 else 0
            if reliability_ratio >= 0.7:
                return 'high', f'Strong data quality with {transaction_count} transactions'
            else:
                return 'building', f'Good data volume, building category patterns'
        elif transaction_count >= self.thresholds.min_transactions_for_building_confidence:
            return 'building', f'Building your profile with {transaction_count} transactions'
        else:
            return 'low', f'Limited data ({transaction_count} transactions) - insights will improve over time'
    
    def is_category_flexible(self, elasticity: float) -> bool:
        """
        Determine if a category has high spending flexibility.
        
        Args:
            elasticity: Category elasticity score (0-1)
            
        Returns:
            True if high flexibility, False otherwise
        """
        return elasticity > self.thresholds.elasticity_high_flexibility
    
    def is_category_essential(self, elasticity: float) -> bool:
        """
        Determine if a category is essential (low flexibility).
        
        Args:
            elasticity: Category elasticity score (0-1)
            
        Returns:
            True if essential/low flexibility, False otherwise
        """
        return elasticity < self.thresholds.elasticity_low_flexibility
    
    def calculate_annual_impact(self, monthly_change: float) -> float:
        """
        Calculate annual financial impact from monthly change.
        
        Args:
            monthly_change: Monthly amount (positive or negative)
            
        Returns:
            Annual impact (monthly * 12)
        """
        return monthly_change * 12
    
    def format_currency(self, amount: float) -> str:
        """
        Format amount as currency string.
        
        Args:
            amount: Amount to format
            
        Returns:
            Formatted string like "₹1,234" or "₹1,234.50"
            
        Example:
            >>> calc = InsightCalculator()
            >>> calc.format_currency(1234.56)
            '₹1,235'
            >>> calc.format_currency(1234500)
            '₹1,234,500'
        """
        return f"₹{abs(amount):,.0f}"
