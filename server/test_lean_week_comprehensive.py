#!/usr/bin/env python3
"""
Comprehensive test for Lean Week Predictor
Tests with actual database connection
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.models.transactions import Transaction
from app.models.behaviour import BehaviourModel  # Import to resolve relationships
from app.models.goal import Goal, GoalContribution  # Import to resolve relationships
from app.services.lean_week_predictor import LeanWeekPredictor
from datetime import datetime, timedelta
import json

def test_lean_week_predictor():
    """Test the lean week predictor service"""
    
    print("=" * 60)
    print("LEAN WEEK PREDICTOR - COMPREHENSIVE TEST")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Get user with transactions (prefer user with most transactions)
        users_with_txns = db.query(User).join(Transaction).distinct().all()
        
        if not users_with_txns:
            print("\n⚠️  No users with transactions found in database.")
            print("Creating test scenario with user ID 5...")
            user = db.query(User).filter(User.id == 5).first()
            if not user:
                print("❌ User not found. Cannot proceed with test.")
                return False
        else:
            # Get user with most transactions
            user = max(users_with_txns, key=lambda u: db.query(Transaction).filter(Transaction.user_id == u.id).count())
        
        print(f"\n✓ Testing with User: {user.email} (ID: {user.id})")
        
        # Check for transactions
        txn_count = db.query(Transaction).filter(Transaction.user_id == user.id).count()
        print(f"✓ Found {txn_count} transactions for this user")
        
        if txn_count < 5:
            print("⚠️  Warning: Less than 5 transactions. Results may be limited.")
        
        # Initialize service
        predictor = LeanWeekPredictor()
        print("\n✓ LeanWeekPredictor initialized")
        
        # Test 1: Monthly Cash Flow Analysis
        print("\n" + "-" * 60)
        print("TEST 1: Monthly Cash Flow Analysis")
        print("-" * 60)
        
        monthly_flow = predictor.get_monthly_cash_flow(db, user.id, months=6)
        print(f"✓ Retrieved {len(monthly_flow)} months of data")
        
        if monthly_flow:
            print("\nMonthly Summary:")
            for month_data in monthly_flow[-3:]:  # Last 3 months
                print(f"  {month_data['month']}: Income=${month_data['income']:,.2f}, "
                      f"Expenses=${month_data['expenses']:,.2f}, "
                      f"Net=${month_data['net_flow']:,.2f}")
        
        # Test 2: Lean Period Identification
        print("\n" + "-" * 60)
        print("TEST 2: Lean Period Identification")
        print("-" * 60)
        
        lean_analysis = predictor.identify_lean_periods(monthly_flow)
        print(f"✓ Lean Frequency: {lean_analysis['lean_frequency']:.1%}")
        print(f"✓ Identified {len(lean_analysis['lean_periods'])} lean periods")
        
        if lean_analysis['lean_periods']:
            print("\nLean Periods:")
            for period in lean_analysis['lean_periods'][:3]:
                print(f"  {period['period']}: Net=${period['net_flow']:,.2f} (Severity: ${period['severity']:,.2f})")
        
        pattern = lean_analysis['pattern_detected']
        print(f"\nPattern Detection: {pattern['description']}")
        
        # Test 3: Cash Flow Forecast
        print("\n" + "-" * 60)
        print("TEST 3: Cash Flow Forecast (3 months)")
        print("-" * 60)
        
        current_balance = float(user.savings or 5000)
        forecast = predictor.forecast_cash_flow(db, user.id, forecast_periods=3, current_balance=current_balance)
        
        print(f"✓ Forecast Confidence: {forecast['confidence']:.1%}")
        print(f"✓ Income Volatility: {forecast['income_volatility']:.1%}")
        print(f"✓ Avg Monthly Income: ${forecast['avg_monthly_income']:,.2f}")
        print(f"✓ Avg Monthly Expenses: ${forecast['avg_monthly_expenses']:,.2f}")
        
        if forecast['warnings']:
            print(f"\n⚠️  Warnings ({len(forecast['warnings'])}):")
            for warning in forecast['warnings']:
                print(f"  - {warning}")
        
        if forecast['forecasts']:
            print("\nForecast Summary:")
            for fc in forecast['forecasts']:
                print(f"\n  Period {fc['period']} (Month +{fc['month_offset']}):")
                print(f"    Net Flow: ${fc['net_cash_flow']['likely']:,.2f} "
                      f"(Best: ${fc['net_cash_flow']['best']:,.2f}, "
                      f"Worst: ${fc['net_cash_flow']['worst']:,.2f})")
                print(f"    Balance: ${fc['projected_balance']['likely']:,.2f}")
                if fc['is_lean_period']:
                    print(f"    ⚠️  LEAN PERIOD WARNING")
        
        # Test 4: Income Smoothing Recommendations
        print("\n" + "-" * 60)
        print("TEST 4: Income Smoothing Recommendations")
        print("-" * 60)
        
        smoothing = predictor.calculate_income_smoothing_recommendation(
            db, user.id, current_balance=current_balance, target_months_buffer=3
        )
        
        if smoothing.get('status') == 'insufficient_data':
            print("⚠️  " + smoothing['message'])
        else:
            print(f"✓ Current Balance: ${smoothing['current_balance']:,.2f}")
            print(f"✓ Target Emergency Fund: ${smoothing['target_emergency_fund']:,.2f}")
            print(f"✓ Gap: ${smoothing['emergency_fund_gap']:,.2f}")
            print(f"✓ Recommended Save Rate: {smoothing['recommended_save_rate']:.1%}")
            print(f"✓ Monthly Save Amount: ${smoothing['monthly_save_amount']:,.2f}")
            
            if smoothing['months_to_target']:
                print(f"✓ Time to Target: {smoothing['months_to_target']:.1f} months")
            
            strategy = smoothing['strategy']
            print(f"\nStrategy Level: {strategy['volatility_level'].upper()}")
            print(f"Summary: {strategy['strategy_summary']}")
            
            print("\nRecommendations:")
            for rec in strategy['recommendations']:
                print(f"  • {rec}")
            
            print("\nAction Items:")
            for action in strategy['action_items']:
                print(f"  ✓ {action}")
        
        # Test 5: Complete Analysis
        print("\n" + "-" * 60)
        print("TEST 5: Complete Lean Week Analysis")
        print("-" * 60)
        
        complete_analysis = predictor.get_complete_lean_analysis(db, user.id, current_balance)
        
        summary = complete_analysis['summary']
        print(f"\n🎯 RISK LEVEL: {summary['risk_level']}")
        print(f"   Message: {summary['risk_message']}")
        print(f"   Immediate Action Needed: {summary['immediate_action_needed']}")
        
        print("\n✅ All tests completed successfully!")
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"User: {user.email}")
        print(f"Transactions: {txn_count}")
        print(f"Monthly Data Points: {len(monthly_flow)}")
        print(f"Lean Frequency: {lean_analysis['lean_frequency']:.1%}")
        print(f"Risk Level: {summary['risk_level']}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    success = test_lean_week_predictor()
    sys.exit(0 if success else 1)
