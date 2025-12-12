"""
Lean Week Predictor Service
Forecasts cash flow challenges and provides income smoothing recommendations for freelancers/gig workers

Features:
- Predicts lean periods (weeks/months with negative cash flow)
- Forecasts upcoming cash flow
- Recommends income smoothing strategies
- Provides early warnings for cash crunches
"""
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
import math
from app.models.transactions import Transaction
from app.services.income_forecast import IncomeForecastService


class LeanWeekPredictor:
    """Predicts lean periods and provides income smoothing recommendations"""
    
    def __init__(self):
        self.forecast_service = IncomeForecastService()
    
    @staticmethod
    def get_monthly_cash_flow(db: Session, user_id: int, months: int = 6) -> List[Dict]:
        """
        Get historical monthly cash flow (income - expenses)
        
        Args:
            db: Database session
            user_id: User ID
            months: Number of past months to analyze
            
        Returns:
            List of monthly cash flow data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
        
        # Get all transactions grouped by month
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.timestamp >= cutoff_date,
            Transaction.timestamp.isnot(None)
        ).order_by(Transaction.timestamp.asc()).all()
        
        # Group by month
        monthly_data = {}
        for txn in transactions:
            if not txn.timestamp or not txn.amount:
                continue
                
            month_key = txn.timestamp.strftime('%Y-%m')
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'month': month_key,
                    'income': 0.0,
                    'expenses': 0.0,
                    'net_flow': 0.0,
                    'income_count': 0,
                    'expense_count': 0,
                    'income_sources': set(),
                    'start_date': txn.timestamp
                }
            
            amount = float(txn.amount)
            
            if txn.type == 'credit':
                monthly_data[month_key]['income'] += amount
                monthly_data[month_key]['income_count'] += 1
                if txn.merchant:
                    monthly_data[month_key]['income_sources'].add(txn.merchant)
            else:
                monthly_data[month_key]['expenses'] += amount
                monthly_data[month_key]['expense_count'] += 1
        
        # Calculate net flow and convert to list
        result = []
        for month_key in sorted(monthly_data.keys()):
            data = monthly_data[month_key]
            data['net_flow'] = data['income'] - data['expenses']
            data['income_sources'] = len(data['income_sources'])
            result.append(data)
        
        return result
    
    @staticmethod
    def get_weekly_cash_flow(db: Session, user_id: int, weeks: int = 12) -> List[Dict]:
        """
        Get historical weekly cash flow for more granular analysis
        
        Args:
            db: Database session
            user_id: User ID
            weeks: Number of past weeks to analyze
            
        Returns:
            List of weekly cash flow data
        """
        cutoff_date = datetime.utcnow() - timedelta(weeks=weeks)
        
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.timestamp >= cutoff_date,
            Transaction.timestamp.isnot(None)
        ).order_by(Transaction.timestamp.asc()).all()
        
        # Group by week (ISO week number)
        weekly_data = {}
        for txn in transactions:
            if not txn.timestamp or not txn.amount:
                continue
            
            # Get ISO week
            iso_year, iso_week, _ = txn.timestamp.isocalendar()
            week_key = f"{iso_year}-W{iso_week:02d}"
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    'week': week_key,
                    'income': 0.0,
                    'expenses': 0.0,
                    'net_flow': 0.0,
                    'start_date': txn.timestamp
                }
            
            amount = float(txn.amount)
            
            if txn.type == 'credit':
                weekly_data[week_key]['income'] += amount
            else:
                weekly_data[week_key]['expenses'] += amount
        
        # Calculate net flow
        result = []
        for week_key in sorted(weekly_data.keys()):
            data = weekly_data[week_key]
            data['net_flow'] = data['income'] - data['expenses']
            result.append(data)
        
        return result
    
    def identify_lean_periods(
        self,
        cash_flow_history: List[Dict],
        threshold_percentile: float = 0.25
    ) -> Dict:
        """
        Identify historical lean periods based on cash flow
        
        Args:
            cash_flow_history: Historical cash flow data
            threshold_percentile: Percentile below which periods are considered "lean"
            
        Returns:
            Analysis of lean periods
        """
        if not cash_flow_history:
            return {
                'lean_periods': [],
                'lean_frequency': 0.0,
                'avg_lean_severity': 0.0,
                'pattern_detected': {'has_pattern': False, 'pattern_type': None, 'description': 'No data available'},
                'threshold': 0.0
            }
        
        # Extract net flows
        net_flows = [period['net_flow'] for period in cash_flow_history]
        
        # Calculate threshold
        sorted_flows = sorted(net_flows)
        threshold_idx = int(len(sorted_flows) * threshold_percentile)
        threshold = sorted_flows[threshold_idx] if threshold_idx < len(sorted_flows) else sorted_flows[0]
        
        # Identify lean periods
        lean_periods = []
        for period in cash_flow_history:
            if period['net_flow'] <= threshold:
                severity = abs(period['net_flow']) if period['net_flow'] < 0 else 0
                lean_periods.append({
                    'period': period.get('month') or period.get('week'),
                    'net_flow': period['net_flow'],
                    'income': period['income'],
                    'expenses': period['expenses'],
                    'severity': severity,
                    'start_date': period.get('start_date')
                })
        
        # Calculate frequency and severity
        lean_frequency = len(lean_periods) / len(cash_flow_history) if cash_flow_history else 0
        avg_severity = sum(p['severity'] for p in lean_periods) / len(lean_periods) if lean_periods else 0
        
        # Detect patterns (monthly/seasonal)
        pattern_detected = self._detect_lean_pattern(lean_periods)
        
        return {
            'lean_periods': lean_periods,
            'lean_frequency': lean_frequency,
            'avg_lean_severity': avg_severity,
            'pattern_detected': pattern_detected,
            'threshold': threshold
        }
    
    def _detect_lean_pattern(self, lean_periods: List[Dict]) -> Dict:
        """
        Detect if lean periods follow a pattern (e.g., every month-end, quarterly)
        """
        if len(lean_periods) < 3:
            return {'has_pattern': False, 'pattern_type': None, 'description': 'Insufficient data'}
        
        # Check for monthly pattern
        if all(p.get('start_date') for p in lean_periods):
            days_of_month = [p['start_date'].day for p in lean_periods]
            
            # Check if they cluster around certain days
            avg_day = sum(days_of_month) / len(days_of_month)
            std_dev = math.sqrt(sum((d - avg_day) ** 2 for d in days_of_month) / len(days_of_month))
            
            if std_dev < 7:  # Within a week variance
                if 1 <= avg_day <= 7:
                    return {
                        'has_pattern': True,
                        'pattern_type': 'month_start',
                        'description': 'Lean periods typically occur at the beginning of the month'
                    }
                elif 23 <= avg_day <= 31:
                    return {
                        'has_pattern': True,
                        'pattern_type': 'month_end',
                        'description': 'Lean periods typically occur at the end of the month'
                    }
        
        return {'has_pattern': False, 'pattern_type': None, 'description': 'No clear pattern detected'}
    
    def forecast_cash_flow(
        self,
        db: Session,
        user_id: int,
        forecast_periods: int = 3,
        current_balance: float = 0.0
    ) -> Dict:
        """
        Forecast future cash flow for next N periods (months)
        
        Args:
            db: Database session
            user_id: User ID
            forecast_periods: Number of future periods to forecast
            current_balance: Current account balance
            
        Returns:
            Cash flow forecast with warnings
        """
        # Get historical data
        monthly_history = self.get_monthly_cash_flow(db, user_id, months=6)
        
        if len(monthly_history) < 2:
            return {
                'forecasts': [],
                'warnings': ['Insufficient transaction history for accurate forecasting'],
                'confidence': 0.0
            }
        
        # Extract income and expense patterns
        income_history = [m['income'] for m in monthly_history]
        expense_history = [m['expenses'] for m in monthly_history]
        
        # Calculate averages and volatility
        avg_income = sum(income_history) / len(income_history)
        avg_expenses = sum(expense_history) / len(expense_history)
        
        income_std = math.sqrt(sum((x - avg_income) ** 2 for x in income_history) / len(income_history))
        expense_std = math.sqrt(sum((x - avg_expenses) ** 2 for x in expense_history) / len(expense_history))
        
        income_volatility = income_std / avg_income if avg_income > 0 else 0
        
        # Forecast using exponential smoothing
        income_forecast, income_confidence = self.forecast_service.exponential_smoothing_forecast(income_history)
        
        # Simple expense forecast (assume relatively stable)
        expense_forecast = avg_expenses
        
        # Generate forecasts for future periods
        forecasts = []
        running_balance = current_balance
        warnings = []
        
        for i in range(forecast_periods):
            period_num = i + 1
            
            # Forecast with uncertainty bands
            forecast_income_best = income_forecast * (1 + income_volatility * 0.5)
            forecast_income_worst = max(0, income_forecast * (1 - income_volatility * 1.5))
            forecast_income_likely = income_forecast
            
            forecast_expense_best = avg_expenses * 0.9  # Optimistic
            forecast_expense_worst = avg_expenses * 1.1  # Pessimistic
            forecast_expense_likely = avg_expenses
            
            # Calculate scenarios
            best_case_net = forecast_income_best - forecast_expense_best
            worst_case_net = forecast_income_worst - forecast_expense_worst
            likely_net = forecast_income_likely - forecast_expense_likely
            
            # Update running balance
            best_balance = running_balance + best_case_net
            worst_balance = running_balance + worst_case_net
            likely_balance = running_balance + likely_net
            
            # Check for warnings
            is_lean = worst_case_net < 0
            balance_risk = worst_balance < 0
            
            if is_lean:
                warnings.append(f"Month {period_num}: Potential lean period - worst case deficit of ${abs(worst_case_net):,.2f}")
            
            if balance_risk:
                warnings.append(f"Month {period_num}: CRITICAL - Balance may go negative (${worst_balance:,.2f})")
            
            forecasts.append({
                'period': period_num,
                'month_offset': i + 1,
                'income': {
                    'best': round(forecast_income_best, 2),
                    'likely': round(forecast_income_likely, 2),
                    'worst': round(forecast_income_worst, 2)
                },
                'expenses': {
                    'best': round(forecast_expense_best, 2),
                    'likely': round(forecast_expense_likely, 2),
                    'worst': round(forecast_expense_worst, 2)
                },
                'net_cash_flow': {
                    'best': round(best_case_net, 2),
                    'likely': round(likely_net, 2),
                    'worst': round(worst_case_net, 2)
                },
                'projected_balance': {
                    'best': round(best_balance, 2),
                    'likely': round(likely_balance, 2),
                    'worst': round(worst_balance, 2)
                },
                'is_lean_period': is_lean,
                'balance_at_risk': balance_risk
            })
            
            # Use likely scenario for next period
            running_balance = likely_balance
        
        return {
            'forecasts': forecasts,
            'warnings': warnings,
            'confidence': income_confidence,
            'income_volatility': round(income_volatility, 3),
            'avg_monthly_income': round(avg_income, 2),
            'avg_monthly_expenses': round(avg_expenses, 2)
        }
    
    def calculate_income_smoothing_recommendation(
        self,
        db: Session,
        user_id: int,
        current_balance: float = 0.0,
        target_months_buffer: int = 3
    ) -> Dict:
        """
        Calculate how much to save during good months to smooth income volatility
        
        Args:
            db: Database session
            user_id: User ID
            current_balance: Current savings/emergency fund
            target_months_buffer: Target number of months of expenses to maintain
            
        Returns:
            Income smoothing recommendations
        """
        monthly_history = self.get_monthly_cash_flow(db, user_id, months=6)
        
        if not monthly_history:
            return {
                'status': 'insufficient_data',
                'message': 'Need transaction history to provide recommendations'
            }
        
        # Calculate income statistics
        income_values = [m['income'] for m in monthly_history]
        expense_values = [m['expenses'] for m in monthly_history]
        net_flows = [m['net_flow'] for m in monthly_history]
        
        avg_income = sum(income_values) / len(income_values)
        avg_expenses = sum(expense_values) / len(expense_values)
        
        income_std = math.sqrt(sum((x - avg_income) ** 2 for x in income_values) / len(income_values))
        income_volatility = income_std / avg_income if avg_income > 0 else 0
        
        # Identify good vs bad months
        good_months = [m for m in monthly_history if m['net_flow'] > avg_income * 0.1]  # 10% above breakeven
        lean_months = [m for m in monthly_history if m['net_flow'] < 0]
        
        # Calculate target emergency fund
        target_emergency_fund = avg_expenses * target_months_buffer
        emergency_fund_gap = max(0, target_emergency_fund - current_balance)
        
        # Calculate recommended savings rate
        if good_months:
            avg_good_month_surplus = sum(m['net_flow'] for m in good_months) / len(good_months)
            
            # Recommend saving % of good month income
            if avg_good_month_surplus > 0:
                recommended_save_rate = min(0.5, emergency_fund_gap / (avg_good_month_surplus * 12))  # Cap at 50%
            else:
                recommended_save_rate = 0.3  # Default 30%
        else:
            recommended_save_rate = 0.3
        
        # Calculate how much to save per good month
        if good_months:
            avg_good_month_income = sum(m['income'] for m in good_months) / len(good_months)
            monthly_save_amount = avg_good_month_income * recommended_save_rate
        else:
            monthly_save_amount = avg_income * 0.3
        
        # Estimate time to reach target
        months_to_target = emergency_fund_gap / monthly_save_amount if monthly_save_amount > 0 else float('inf')
        
        # Generate strategy
        strategy = self._generate_smoothing_strategy(
            income_volatility,
            len(good_months),
            len(lean_months),
            len(monthly_history),
            emergency_fund_gap
        )
        
        return {
            'current_balance': round(current_balance, 2),
            'target_emergency_fund': round(target_emergency_fund, 2),
            'emergency_fund_gap': round(emergency_fund_gap, 2),
            'avg_monthly_income': round(avg_income, 2),
            'avg_monthly_expenses': round(avg_expenses, 2),
            'income_volatility': round(income_volatility, 3),
            'good_months_count': len(good_months),
            'lean_months_count': len(lean_months),
            'recommended_save_rate': round(recommended_save_rate, 3),
            'monthly_save_amount': round(monthly_save_amount, 2),
            'months_to_target': round(months_to_target, 1) if months_to_target != float('inf') else None,
            'strategy': strategy
        }
    
    def _generate_smoothing_strategy(
        self,
        volatility: float,
        good_months: int,
        lean_months: int,
        total_months: int,
        fund_gap: float
    ) -> Dict:
        """Generate personalized income smoothing strategy"""
        
        lean_frequency = lean_months / total_months if total_months > 0 else 0
        
        if volatility < 0.2:
            volatility_level = 'low'
            strategy = 'Your income is relatively stable. Focus on consistent monthly savings.'
        elif volatility < 0.4:
            volatility_level = 'moderate'
            strategy = 'Your income varies moderately. Save aggressively during good months.'
        else:
            volatility_level = 'high'
            strategy = 'Your income is highly variable. Prioritize building a large emergency fund.'
        
        # Specific recommendations
        recommendations = []
        
        if lean_frequency > 0.3:
            recommendations.append('You experience lean periods frequently (>30% of months). Build 6 months of expenses as emergency fund.')
        else:
            recommendations.append('Lean periods are occasional. Maintain 3-4 months of expenses as buffer.')
        
        if good_months > 0:
            recommendations.append(f'You had {good_months} good months in the last {total_months} months. Use these to build reserves.')
        
        if fund_gap > 0:
            if fund_gap > 5000:
                recommendations.append(f'Emergency fund gap is ${fund_gap:,.2f}. Make this your top priority.')
            else:
                recommendations.append(f'You\'re close to your target. Just ${fund_gap:,.2f} more needed.')
        else:
            recommendations.append('Emergency fund target reached! Consider investing surplus.')
        
        # Action items
        action_items = [
            'Set up automatic transfer to savings account on income days',
            'Track good vs lean months to refine your savings pattern',
            'Review and adjust monthly after 3 months'
        ]
        
        if volatility > 0.4:
            action_items.insert(0, 'Diversify income sources to reduce volatility')
        
        return {
            'volatility_level': volatility_level,
            'strategy_summary': strategy,
            'lean_frequency': round(lean_frequency, 2),
            'recommendations': recommendations,
            'action_items': action_items
        }
    
    def get_complete_lean_analysis(
        self,
        db: Session,
        user_id: int,
        current_balance: float = 0.0
    ) -> Dict:
        """
        Get comprehensive lean week analysis including history, forecasts, and recommendations
        
        Args:
            db: Database session
            user_id: User ID
            current_balance: Current balance
            
        Returns:
            Complete lean week analysis
        """
        # Get historical cash flow
        monthly_history = self.get_monthly_cash_flow(db, user_id, months=6)
        weekly_history = self.get_weekly_cash_flow(db, user_id, weeks=12)
        
        # Identify historical lean periods
        lean_analysis_monthly = self.identify_lean_periods(monthly_history)
        lean_analysis_weekly = self.identify_lean_periods(weekly_history, threshold_percentile=0.2)
        
        # Forecast future cash flow
        forecast = self.forecast_cash_flow(db, user_id, forecast_periods=3, current_balance=current_balance)
        
        # Get income smoothing recommendations
        smoothing = self.calculate_income_smoothing_recommendation(db, user_id, current_balance)
        
        # Overall risk assessment
        risk_level = self._assess_overall_risk(
            lean_analysis_monthly,
            forecast,
            smoothing,
            current_balance
        )
        
        return {
            'summary': {
                'risk_level': risk_level['level'],
                'risk_message': risk_level['message'],
                'immediate_action_needed': risk_level['immediate_action']
            },
            'historical_analysis': {
                'monthly': lean_analysis_monthly,
                'weekly': lean_analysis_weekly
            },
            'cash_flow_forecast': forecast,
            'income_smoothing': smoothing,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _assess_overall_risk(
        self,
        lean_analysis: Dict,
        forecast: Dict,
        smoothing: Dict,
        current_balance: float
    ) -> Dict:
        """Assess overall financial risk level"""
        
        risk_factors = []
        score = 0
        
        # Factor 1: Lean period frequency
        lean_freq = lean_analysis.get('lean_frequency', 0)
        if lean_freq > 0.4:
            score += 3
            risk_factors.append('High frequency of lean periods')
        elif lean_freq > 0.25:
            score += 2
            risk_factors.append('Moderate lean period frequency')
        
        # Factor 2: Upcoming forecasted issues
        warnings = forecast.get('warnings', [])
        critical_warnings = [w for w in warnings if 'CRITICAL' in w]
        if critical_warnings:
            score += 4
            risk_factors.append('Critical cash flow issues forecasted')
        elif warnings:
            score += 2
            risk_factors.append('Potential cash flow challenges ahead')
        
        # Factor 3: Emergency fund status
        fund_gap = smoothing.get('emergency_fund_gap', 0)
        target = smoothing.get('target_emergency_fund', 1)
        fund_coverage = (target - fund_gap) / target if target > 0 else 0
        
        if fund_coverage < 0.3:
            score += 3
            risk_factors.append('Insufficient emergency fund (<30% of target)')
        elif fund_coverage < 0.6:
            score += 1
            risk_factors.append('Emergency fund needs improvement')
        
        # Factor 4: Income volatility
        volatility = smoothing.get('income_volatility', 0)
        if volatility > 0.5:
            score += 2
            risk_factors.append('Very high income volatility')
        elif volatility > 0.3:
            score += 1
            risk_factors.append('Elevated income volatility')
        
        # Determine risk level
        if score >= 7:
            level = 'CRITICAL'
            message = 'Immediate action required to avoid cash crisis'
            immediate = True
        elif score >= 5:
            level = 'HIGH'
            message = 'Significant financial stress - urgent attention needed'
            immediate = True
        elif score >= 3:
            level = 'MODERATE'
            message = 'Some financial challenges - proactive management recommended'
            immediate = False
        elif score >= 1:
            level = 'LOW'
            message = 'Minor concerns - continue monitoring'
            immediate = False
        else:
            level = 'MINIMAL'
            message = 'Financial situation appears stable'
            immediate = False
        
        return {
            'level': level,
            'message': message,
            'immediate_action': immediate,
            'risk_score': score,
            'risk_factors': risk_factors
        }
