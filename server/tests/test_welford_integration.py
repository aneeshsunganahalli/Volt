"""
Integration tests for Welford statistics with real transactions and behavior engine.

Tests incremental learning, edge cases, and validates statistical accuracy.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base
from app.models.user import User
from app.models.transactions import Transaction
from app.models.behaviour import BehaviourModel
from app.services.behavior_engine import BehaviorEngine
from app.services.categorization import CategorizationService
from app.services.statistics import StatisticsService


# Test database setup
@pytest.fixture(scope="function")
def test_db():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def test_user(test_db: Session):
    """Create a test user."""
    user = User(
        email="test@welford.com",
        name="Test User",
        phone_number="+1234567890",
        hashed_password="test_hash"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def behavior_engine():
    """Create behavior engine with mock categorization service."""
    # Use a mock categorization service that doesn't require API key
    class MockCategorizationService:
        async def categorize(self, merchant, amount, raw_msg, tx_type):
            # Simple rule-based categorization for tests
            merchant_lower = merchant.lower()
            if "grocery" in merchant_lower or "walmart" in merchant_lower:
                return "GROCERIES", 0.95
            elif "rent" in merchant_lower or "apartment" in merchant_lower:
                return "HOUSING", 0.95
            elif "gas" in merchant_lower or "shell" in merchant_lower:
                return "TRANSPORTATION", 0.90
            elif "restaurant" in merchant_lower or "cafe" in merchant_lower:
                return "DINING", 0.90
            else:
                return "OTHER", 0.50
    
    return BehaviorEngine(MockCategorizationService())


class TestWelfordIntegration:
    """Integration tests for Welford statistics with transactions."""
    
    def test_single_transaction_initialization(self, test_db, test_user, behavior_engine):
        """Test that first transaction properly initializes stats."""
        # Create first transaction
        tx = Transaction(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            merchant="Walmart",
            category="GROCERIES",
            type="debit",
            timestamp=datetime.utcnow(),
            transactionId="TX001"
        )
        test_db.add(tx)
        test_db.commit()
        test_db.refresh(tx)
        
        # Update behavior model
        asyncio.run(behavior_engine.update_model(test_db, test_user.id, tx))
        test_db.commit()
        
        # Verify model was created and stats are correct
        model = test_db.query(BehaviourModel).filter_by(user_id=test_user.id).first()
        
        assert model is not None
        assert model.transaction_count == 1
        assert "GROCERIES" in model.category_stats
        
        stats = model.category_stats["GROCERIES"]
        assert stats["count"] == 1
        assert stats["mean"] == 100.0
        assert stats["variance"] == 0.0
        assert stats["std_dev"] == 0.0
        assert stats["min"] == 100.0, f"Expected min=100.0, got {stats['min']}"
        assert stats["max"] == 100.0, f"Expected max=100.0, got {stats['max']}"
        assert stats["sum"] == 100.0
    
    def test_incremental_welford_updates(self, test_db, test_user, behavior_engine):
        """Test that Welford stats update correctly with multiple transactions."""
        # Add transactions incrementally: 100, 200, 300
        amounts = [100.00, 200.00, 300.00]
        
        for i, amount in enumerate(amounts):
            tx = Transaction(
                user_id=test_user.id,
                amount=Decimal(str(amount)),
                merchant="Walmart",
                category="GROCERIES",
                type="debit",
                timestamp=datetime.utcnow() + timedelta(days=i),
                transactionId=f"TX{i+1:03d}"
            )
            test_db.add(tx)
            test_db.commit()
            test_db.refresh(tx)
            
            asyncio.run(behavior_engine.update_model(test_db, test_user.id, tx))
            test_db.commit()
        
        # Verify final stats
        model = test_db.query(BehaviourModel).filter_by(user_id=test_user.id).first()
        stats = model.category_stats["GROCERIES"]
        
        assert stats["count"] == 3
        assert stats["mean"] == 200.0, f"Expected mean=200.0, got {stats['mean']}"
        assert stats["min"] == 100.0, f"Expected min=100.0, got {stats['min']}"
        assert stats["max"] == 300.0, f"Expected max=300.0, got {stats['max']}"
        assert stats["sum"] == 600.0
        
        # Check variance/std_dev (sample variance for [100, 200, 300])
        # Variance = ((100-200)^2 + (200-200)^2 + (300-200)^2) / 3 = (10000 + 0 + 10000) / 3 = 6666.67
        # But Welford uses population variance (n not n-1), so it's different
        assert stats["std_dev"] > 0, "Standard deviation should be > 0 for varying amounts"
        assert 80 < stats["std_dev"] < 85, f"Expected std_dev ~81.65, got {stats['std_dev']}"
    
    def test_multiple_categories(self, test_db, test_user, behavior_engine):
        """Test that multiple categories are tracked independently."""
        transactions = [
            ("Walmart", "GROCERIES", 100.00),
            ("Rent Payment", "HOUSING", 1200.00),
            ("Walmart", "GROCERIES", 150.00),
            ("Shell Gas", "TRANSPORTATION", 50.00),
            ("Apartment Complex", "HOUSING", 1200.00),
        ]
        
        for i, (merchant, category, amount) in enumerate(transactions):
            tx = Transaction(
                user_id=test_user.id,
                amount=Decimal(str(amount)),
                merchant=merchant,
                category=category,
                type="debit",
                timestamp=datetime.utcnow() + timedelta(days=i),
                transactionId=f"TX{i+1:03d}"
            )
            test_db.add(tx)
            test_db.commit()
            test_db.refresh(tx)
            
            asyncio.run(behavior_engine.update_model(test_db, test_user.id, tx))
            test_db.commit()
        
        # Verify each category
        model = test_db.query(BehaviourModel).filter_by(user_id=test_user.id).first()
        
        # GROCERIES: 2 transactions (100, 150)
        groceries = model.category_stats["GROCERIES"]
        assert groceries["count"] == 2
        assert groceries["mean"] == 125.0
        assert groceries["min"] == 100.0
        assert groceries["max"] == 150.0
        
        # HOUSING: 2 transactions (1200, 1200)
        housing = model.category_stats["HOUSING"]
        assert housing["count"] == 2
        assert housing["mean"] == 1200.0
        assert housing["min"] == 1200.0
        assert housing["max"] == 1200.0
        assert housing["std_dev"] == 0.0  # No variance
        
        # TRANSPORTATION: 1 transaction (50)
        transport = model.category_stats["TRANSPORTATION"]
        assert transport["count"] == 1
        assert transport["mean"] == 50.0
        assert transport["min"] == 50.0
        assert transport["max"] == 50.0
    
    def test_edge_case_zero_amount(self, test_db, test_user, behavior_engine):
        """Test handling of zero-amount transactions."""
        tx = Transaction(
            user_id=test_user.id,
            amount=Decimal("0.00"),
            merchant="Free Sample",
            category="OTHER",
            type="debit",
            timestamp=datetime.utcnow(),
            transactionId="TX001"
        )
        test_db.add(tx)
        test_db.commit()
        test_db.refresh(tx)
        
        asyncio.run(behavior_engine.update_model(test_db, test_user.id, tx))
        test_db.commit()
        
        model = test_db.query(BehaviourModel).filter_by(user_id=test_user.id).first()
        stats = model.category_stats["OTHER"]
        
        assert stats["count"] == 1
        assert stats["mean"] == 0.0
        assert stats["min"] == 0.0
        assert stats["max"] == 0.0
    
    def test_edge_case_very_large_amount(self, test_db, test_user, behavior_engine):
        """Test handling of very large amounts."""
        # Start with normal amount, then add very large amount
        amounts = [100.00, 10000.00]
        
        for i, amount in enumerate(amounts):
            tx = Transaction(
                user_id=test_user.id,
                amount=Decimal(str(amount)),
                merchant="Store",
                category="SHOPPING",
                type="debit",
                timestamp=datetime.utcnow() + timedelta(days=i),
                transactionId=f"TX{i+1:03d}"
            )
            test_db.add(tx)
            test_db.commit()
            test_db.refresh(tx)
            
            asyncio.run(behavior_engine.update_model(test_db, test_user.id, tx))
            test_db.commit()
        
        model = test_db.query(BehaviourModel).filter_by(user_id=test_user.id).first()
        stats = model.category_stats["SHOPPING"]
        
        assert stats["count"] == 2
        assert stats["mean"] == 5050.0
        assert stats["min"] == 100.0
        assert stats["max"] == 10000.0
        assert stats["std_dev"] > 0
    
    def test_edge_case_negative_amount(self, test_db, test_user, behavior_engine):
        """Test handling of negative amounts (refunds)."""
        # Add normal purchase then refund
        amounts = [100.00, -50.00, 80.00]
        
        for i, amount in enumerate(amounts):
            tx = Transaction(
                user_id=test_user.id,
                amount=Decimal(str(amount)),
                merchant="Store",
                category="SHOPPING",
                type="debit",
                timestamp=datetime.utcnow() + timedelta(days=i),
                transactionId=f"TX{i+1:03d}"
            )
            test_db.add(tx)
            test_db.commit()
            test_db.refresh(tx)
            
            asyncio.run(behavior_engine.update_model(test_db, test_user.id, tx))
            test_db.commit()
        
        model = test_db.query(BehaviourModel).filter_by(user_id=test_user.id).first()
        stats = model.category_stats["SHOPPING"]
        
        assert stats["count"] == 3
        # Mean should be (100 - 50 + 80) / 3 = 43.33
        assert 43.0 < stats["mean"] < 44.0
        assert stats["min"] == -50.0
        assert stats["max"] == 100.0
    
    def test_edge_case_decimal_precision(self, test_db, test_user, behavior_engine):
        """Test that decimal precision is maintained."""
        # Use amounts with many decimal places
        amounts = [12.345, 23.456, 34.567]
        
        for i, amount in enumerate(amounts):
            tx = Transaction(
                user_id=test_user.id,
                amount=Decimal(str(amount)),
                merchant="Store",
                category="OTHER",
                type="debit",
                timestamp=datetime.utcnow() + timedelta(days=i),
                transactionId=f"TX{i+1:03d}"
            )
            test_db.add(tx)
            test_db.commit()
            test_db.refresh(tx)
            
            asyncio.run(behavior_engine.update_model(test_db, test_user.id, tx))
            test_db.commit()
        
        model = test_db.query(BehaviourModel).filter_by(user_id=test_user.id).first()
        stats = model.category_stats["OTHER"]
        
        assert stats["count"] == 3
        # Mean should be (12.345 + 23.456 + 34.567) / 3 = 23.456
        # Allow wider tolerance for float conversion from Decimal (loses some precision)
        assert 23.4 < stats["mean"] < 23.5, f"Expected mean≈23.456, got {stats['mean']}"
        assert 12.3 < stats["min"] < 12.4, f"Expected min≈12.345, got {stats['min']}"
        assert 34.5 < stats["max"] < 34.6, f"Expected max≈34.567, got {stats['max']}"
    
    def test_income_tracking_freelancer(self, test_db, test_user, behavior_engine):
        """Test income tracking for freelancers with variable income."""
        # Add multiple income transactions (credit type)
        income_data = [
            ("Client A - Web Design", 3500.00, "credit"),
            ("Client B - Content", 2200.00, "credit"),
            ("Upwork Project", 1500.00, "credit"),
        ]
        
        for i, (merchant, amount, tx_type) in enumerate(income_data):
            tx = Transaction(
                user_id=test_user.id,
                amount=Decimal(str(amount)),
                merchant=merchant,
                category="INCOME",
                type=tx_type,
                timestamp=datetime.utcnow() + timedelta(days=i*5),
                transactionId=f"INC{i+1:03d}"
            )
            test_db.add(tx)
            test_db.commit()
            test_db.refresh(tx)
            
            asyncio.run(behavior_engine.update_model(test_db, test_user.id, tx))
            test_db.commit()
        
        # Verify income stats
        model = test_db.query(BehaviourModel).filter_by(user_id=test_user.id).first()
        
        assert model.monthly_patterns is not None
        assert "income_stats" in model.monthly_patterns
        
        income_stats = model.monthly_patterns["income_stats"]
        assert income_stats["count"] == 3
        
        # Mean should be (3500 + 2200 + 1500) / 3 = 2400
        assert 2399 < income_stats["mean"] < 2401
        assert income_stats["min"] == 1500.0
        assert income_stats["max"] == 3500.0
        assert income_stats["sum"] == 7200.0
        
        # Check sources
        assert "sources" in income_stats
        assert len(income_stats["sources"]) == 3  # 3 different clients
    
    def test_mixed_income_and_expenses(self, test_db, test_user, behavior_engine):
        """Test that income and expense tracking work together."""
        transactions = [
            ("Client A", 5000.00, "credit", "INCOME"),
            ("Walmart", 100.00, "debit", "GROCERIES"),
            ("Rent Payment", 1200.00, "debit", "HOUSING"),
            ("Client B", 3000.00, "credit", "INCOME"),
            ("Gas Station", 50.00, "debit", "TRANSPORTATION"),
        ]
        
        for i, (merchant, amount, tx_type, category) in enumerate(transactions):
            tx = Transaction(
                user_id=test_user.id,
                amount=Decimal(str(amount)),
                merchant=merchant,
                category=category,
                type=tx_type,
                timestamp=datetime.utcnow() + timedelta(days=i),
                transactionId=f"TX{i+1:03d}"
            )
            test_db.add(tx)
            test_db.commit()
            test_db.refresh(tx)
            
            asyncio.run(behavior_engine.update_model(test_db, test_user.id, tx))
            test_db.commit()
        
        model = test_db.query(BehaviourModel).filter_by(user_id=test_user.id).first()
        
        # Check expense categories
        assert "GROCERIES" in model.category_stats
        assert "HOUSING" in model.category_stats
        assert "TRANSPORTATION" in model.category_stats
        
        # Check income tracking
        assert "income_stats" in model.monthly_patterns
        income_stats = model.monthly_patterns["income_stats"]
        assert income_stats["count"] == 2
        assert income_stats["mean"] == 4000.0  # (5000 + 3000) / 2
    
    def test_welford_statistical_accuracy(self, test_db, test_user, behavior_engine):
        """Test that Welford algorithm produces statistically accurate results."""
        # Use a known dataset with calculable statistics
        # Dataset: [10, 20, 30, 40, 50]
        # Mean: 30
        # Population variance: 200
        # Population std dev: 14.14
        amounts = [10.0, 20.0, 30.0, 40.0, 50.0]
        
        for i, amount in enumerate(amounts):
            tx = Transaction(
                user_id=test_user.id,
                amount=Decimal(str(amount)),
                merchant="Test Store",
                category="TEST",
                type="debit",
                timestamp=datetime.utcnow() + timedelta(days=i),
                transactionId=f"TX{i+1:03d}"
            )
            test_db.add(tx)
            test_db.commit()
            test_db.refresh(tx)
            
            asyncio.run(behavior_engine.update_model(test_db, test_user.id, tx))
            test_db.commit()
        
        model = test_db.query(BehaviourModel).filter_by(user_id=test_user.id).first()
        stats = model.category_stats["TEST"]
        
        # Verify against known values
        assert stats["count"] == 5
        assert stats["mean"] == 30.0, f"Expected mean=30.0, got {stats['mean']}"
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
        assert stats["sum"] == 150.0
        
        # Population variance = 200
        assert 199.9 < stats["variance"] < 200.1, f"Expected variance≈200, got {stats['variance']}"
        
        # Population std dev = sqrt(200) ≈ 14.14
        assert 14.13 < stats["std_dev"] < 14.15, f"Expected std_dev≈14.14, got {stats['std_dev']}"


class TestStatisticsServiceDirect:
    """Direct unit tests for StatisticsService edge cases."""
    
    def test_welford_with_identical_values(self):
        """Test Welford with all identical values."""
        service = StatisticsService()
        stats = {"count": 0, "sum": 0.0, "mean": 0.0, "variance": 0.0, "std_dev": 0.0, "m2": 0.0, "min": 0, "max": 0}
        
        for _ in range(10):
            stats = service.update_welford_stats(stats, 100.0)
        
        assert stats["count"] == 10
        assert stats["mean"] == 100.0
        assert stats["variance"] == 0.0
        assert stats["std_dev"] == 0.0
        assert stats["min"] == 100.0
        assert stats["max"] == 100.0
    
    def test_welford_numerical_stability(self):
        """Test Welford's numerical stability with large numbers."""
        service = StatisticsService()
        stats = {"count": 0, "sum": 0.0, "mean": 0.0, "variance": 0.0, "std_dev": 0.0, "m2": 0.0, "min": 0, "max": 0}
        
        # Large base with small variations (tests numerical stability)
        base = 1e9
        values = [base + 1, base + 2, base + 3, base + 4, base + 5]
        
        for val in values:
            stats = service.update_welford_stats(stats, val)
        
        assert stats["count"] == 5
        assert abs(stats["mean"] - (base + 3)) < 1e-6
        assert stats["min"] == base + 1
        assert stats["max"] == base + 5
        # Should maintain precision even with large numbers
        assert stats["variance"] > 0


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_welford_integration.py -v
    pytest.main([__file__, "-v"])
