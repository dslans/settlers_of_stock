"""
Comprehensive database integration tests.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem
from app.models.alert import Alert
from app.models.analysis import AnalysisResult
from app.services.auth_service import AuthService
from app.services.watchlist_service import WatchlistService
from app.services.alert_service import AlertService
from tests.test_factories import UserFactory, WatchlistFactory, AlertFactory


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseConstraints:
    """Test database constraints and relationships."""
    
    def test_user_email_uniqueness(self, db_session):
        """Test that user emails must be unique."""
        user1 = UserFactory(email="unique@example.com")
        user2 = UserFactory(email="unique@example.com")
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_watchlist_user_relationship(self, db_session, test_user):
        """Test watchlist-user relationship constraints."""
        watchlist = Watchlist(
            user_id=test_user.id,
            name="Test Watchlist",
            description="Test description"
        )
        
        db_session.add(watchlist)
        db_session.commit()
        
        # Test cascade delete
        db_session.delete(test_user)
        db_session.commit()
        
        # Watchlist should be deleted too
        remaining_watchlists = db_session.query(Watchlist).filter(
            Watchlist.user_id == test_user.id
        ).all()
        assert len(remaining_watchlists) == 0
    
    def test_watchlist_item_constraints(self, db_session, test_watchlist):
        """Test watchlist item constraints."""
        # Test symbol uniqueness within watchlist
        item1 = WatchlistItem(
            watchlist_id=test_watchlist.id,
            symbol="AAPL",
            company_name="Apple Inc."
        )
        
        item2 = WatchlistItem(
            watchlist_id=test_watchlist.id,
            symbol="AAPL",  # Same symbol
            company_name="Apple Inc."
        )
        
        db_session.add(item1)
        db_session.commit()
        
        db_session.add(item2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_alert_user_relationship(self, db_session, test_user):
        """Test alert-user relationship constraints."""
        alert = Alert(
            user_id=test_user.id,
            symbol="AAPL",
            alert_type="price_above",
            condition_value=200.00
        )
        
        db_session.add(alert)
        db_session.commit()
        
        # Test foreign key constraint
        alert.user_id = 99999  # Non-existent user
        with pytest.raises(IntegrityError):
            db_session.commit()


@pytest.mark.integration
@pytest.mark.database
class TestDatabasePerformance:
    """Test database performance and optimization."""
    
    def test_user_query_with_indexes(self, db_session):
        """Test that user queries use proper indexes."""
        # Create multiple users
        users = [UserFactory() for _ in range(100)]
        db_session.add_all(users)
        db_session.commit()
        
        # Query by email (should use index)
        start_time = datetime.utcnow()
        user = db_session.query(User).filter(User.email == users[50].email).first()
        end_time = datetime.utcnow()
        
        assert user is not None
        query_time = (end_time - start_time).total_seconds()
        assert query_time < 0.1  # Should be very fast with index
    
    def test_watchlist_query_optimization(self, db_session, test_user):
        """Test watchlist queries are optimized."""
        # Create watchlists with items
        watchlists = []
        for i in range(10):
            watchlist = Watchlist(
                user_id=test_user.id,
                name=f"Watchlist {i}",
                description=f"Description {i}"
            )
            db_session.add(watchlist)
            db_session.flush()
            
            # Add items to each watchlist
            for j in range(20):
                item = WatchlistItem(
                    watchlist_id=watchlist.id,
                    symbol=f"STOCK{i}{j}",
                    company_name=f"Company {i}-{j}"
                )
                db_session.add(item)
            
            watchlists.append(watchlist)
        
        db_session.commit()
        
        # Query with join (should be optimized)
        start_time = datetime.utcnow()
        result = db_session.query(Watchlist).filter(
            Watchlist.user_id == test_user.id
        ).all()
        end_time = datetime.utcnow()
        
        assert len(result) == 10
        query_time = (end_time - start_time).total_seconds()
        assert query_time < 0.5  # Should be reasonably fast
    
    def test_bulk_operations_performance(self, db_session):
        """Test bulk database operations performance."""
        # Bulk insert test
        users_data = [
            {
                'email': f'bulk{i}@example.com',
                'full_name': f'Bulk User {i}',
                'hashed_password': 'test_hash',
                'is_active': True,
                'is_verified': True
            }
            for i in range(1000)
        ]
        
        start_time = datetime.utcnow()
        db_session.bulk_insert_mappings(User, users_data)
        db_session.commit()
        end_time = datetime.utcnow()
        
        bulk_time = (end_time - start_time).total_seconds()
        assert bulk_time < 2.0  # Bulk insert should be fast
        
        # Verify all users were inserted
        count = db_session.query(User).filter(User.email.like('bulk%')).count()
        assert count == 1000


@pytest.mark.integration
@pytest.mark.database
class TestTransactionManagement:
    """Test database transaction management."""
    
    def test_successful_transaction(self, db_session, test_user):
        """Test successful transaction commits all changes."""
        initial_watchlist_count = db_session.query(Watchlist).count()
        initial_item_count = db_session.query(WatchlistItem).count()
        
        try:
            db_session.begin()
            
            # Create watchlist
            watchlist = Watchlist(
                user_id=test_user.id,
                name="Transaction Test",
                description="Testing transactions"
            )
            db_session.add(watchlist)
            db_session.flush()
            
            # Create items
            for i in range(5):
                item = WatchlistItem(
                    watchlist_id=watchlist.id,
                    symbol=f"TXN{i}",
                    company_name=f"Transaction Test {i}"
                )
                db_session.add(item)
            
            db_session.commit()
            
        except Exception:
            db_session.rollback()
            raise
        
        # Verify all changes were committed
        final_watchlist_count = db_session.query(Watchlist).count()
        final_item_count = db_session.query(WatchlistItem).count()
        
        assert final_watchlist_count == initial_watchlist_count + 1
        assert final_item_count == initial_item_count + 5
    
    def test_failed_transaction_rollback(self, db_session, test_user):
        """Test failed transaction rolls back all changes."""
        initial_watchlist_count = db_session.query(Watchlist).count()
        initial_item_count = db_session.query(WatchlistItem).count()
        
        try:
            db_session.begin()
            
            # Create watchlist
            watchlist = Watchlist(
                user_id=test_user.id,
                name="Rollback Test",
                description="Testing rollback"
            )
            db_session.add(watchlist)
            db_session.flush()
            
            # Create valid item
            item1 = WatchlistItem(
                watchlist_id=watchlist.id,
                symbol="ROLL1",
                company_name="Rollback Test 1"
            )
            db_session.add(item1)
            
            # Create invalid item (duplicate symbol)
            item2 = WatchlistItem(
                watchlist_id=watchlist.id,
                symbol="ROLL1",  # Duplicate symbol
                company_name="Rollback Test 2"
            )
            db_session.add(item2)
            
            db_session.commit()  # This should fail
            
        except IntegrityError:
            db_session.rollback()
        
        # Verify no changes were committed
        final_watchlist_count = db_session.query(Watchlist).count()
        final_item_count = db_session.query(WatchlistItem).count()
        
        assert final_watchlist_count == initial_watchlist_count
        assert final_item_count == initial_item_count
    
    def test_nested_transaction_handling(self, db_session, test_user):
        """Test nested transaction handling."""
        service = WatchlistService(db_session)
        
        # This should work as a complete transaction
        watchlist_data = {
            "name": "Nested Transaction Test",
            "description": "Testing nested transactions",
            "items": [
                {"symbol": "NEST1", "company_name": "Nested Test 1"},
                {"symbol": "NEST2", "company_name": "Nested Test 2"},
                {"symbol": "NEST3", "company_name": "Nested Test 3"},
            ]
        }
        
        watchlist = service.create_watchlist_with_items(test_user.id, watchlist_data)
        
        assert watchlist is not None
        assert len(watchlist.items) == 3
        
        # Verify all items were created
        items = db_session.query(WatchlistItem).filter(
            WatchlistItem.watchlist_id == watchlist.id
        ).all()
        assert len(items) == 3


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseMigrations:
    """Test database migration scenarios."""
    
    def test_schema_version_tracking(self, db_session):
        """Test that schema version is properly tracked."""
        # Check alembic version table exists
        result = db_session.execute(
            text("SELECT version_num FROM alembic_version")
        ).fetchone()
        
        assert result is not None
        assert result[0] is not None  # Should have a version number
    
    def test_table_existence(self, db_session):
        """Test that all required tables exist."""
        required_tables = [
            'users',
            'watchlists',
            'watchlist_items',
            'alerts',
            'analysis_results',
            'chat_messages',
            'earnings_events',
            'educational_content'
        ]
        
        for table_name in required_tables:
            result = db_session.execute(
                text(f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}'")
            ).fetchone()
            assert result is not None, f"Table {table_name} does not exist"
    
    def test_column_constraints(self, db_session):
        """Test that column constraints are properly applied."""
        # Test NOT NULL constraints
        user = User(
            email=None,  # Should fail
            full_name="Test User",
            hashed_password="test_hash"
        )
        
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseBackupRestore:
    """Test database backup and restore scenarios."""
    
    def test_data_consistency_after_operations(self, db_session, test_user):
        """Test data consistency after various operations."""
        # Create initial data
        watchlist = Watchlist(
            user_id=test_user.id,
            name="Consistency Test",
            description="Testing data consistency"
        )
        db_session.add(watchlist)
        db_session.commit()
        
        # Perform various operations
        watchlist.name = "Updated Consistency Test"
        db_session.commit()
        
        # Add items
        item = WatchlistItem(
            watchlist_id=watchlist.id,
            symbol="CONS",
            company_name="Consistency Test Company"
        )
        db_session.add(item)
        db_session.commit()
        
        # Verify data integrity
        db_session.refresh(watchlist)
        assert watchlist.name == "Updated Consistency Test"
        assert len(watchlist.items) == 1
        assert watchlist.items[0].symbol == "CONS"
    
    def test_concurrent_access_handling(self, db_session, test_user, multiple_users):
        """Test handling of concurrent database access."""
        # Simulate concurrent watchlist creation
        watchlists = []
        
        for i, user in enumerate(multiple_users[:3]):
            watchlist = Watchlist(
                user_id=user.id,
                name=f"Concurrent Test {i}",
                description=f"Testing concurrent access {i}"
            )
            watchlists.append(watchlist)
        
        # Add all at once (simulating concurrent access)
        db_session.add_all(watchlists)
        db_session.commit()
        
        # Verify all were created successfully
        for watchlist in watchlists:
            db_session.refresh(watchlist)
            assert watchlist.id is not None
        
        # Verify no data corruption
        total_watchlists = db_session.query(Watchlist).filter(
            Watchlist.user_id.in_([u.id for u in multiple_users[:3]])
        ).count()
        assert total_watchlists == 3