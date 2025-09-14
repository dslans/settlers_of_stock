"""
Database integration tests for GCP Cloud SQL setup.
"""

import pytest
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import DatabaseManager, Base, get_db
from app.core.config import get_settings
from app.models import User, Watchlist, WatchlistItem, Alert, ChatSession, ChatMessage

# Test database URL - using SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_settlers_of_stock.db"
TEST_SYNC_DATABASE_URL = "sqlite:///./test_settlers_of_stock.db"

@pytest.fixture
async def test_db_manager():
    """Create a test database manager with SQLite."""
    # Override settings for testing
    settings = get_settings()
    original_db_url = settings.DATABASE_URL
    settings.DATABASE_URL = TEST_DATABASE_URL
    
    # Create test database manager
    db_manager = DatabaseManager()
    await db_manager.initialize_database()
    
    # Create all tables
    async with db_manager.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield db_manager
    
    # Cleanup
    async with db_manager.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await db_manager.close_connections()
    settings.DATABASE_URL = original_db_url

@pytest.fixture
async def test_session(test_db_manager):
    """Create a test database session."""
    async for session in test_db_manager.get_async_session():
        yield session

class TestDatabaseConnection:
    """Test database connection and basic operations."""
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, test_db_manager):
        """Test that database manager initializes correctly."""
        assert test_db_manager.async_engine is not None
        assert test_db_manager.AsyncSessionLocal is not None
    
    @pytest.mark.asyncio
    async def test_database_session_creation(self, test_session):
        """Test that database sessions can be created."""
        assert isinstance(test_session, AsyncSession)
        
        # Test basic query
        result = await test_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    
    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self, test_db_manager):
        """Test that database transactions can be rolled back."""
        async for session in test_db_manager.get_async_session():
            # Create a user
            user = User(
                email="test@example.com",
                hashed_password="hashed_password",
                full_name="Test User"
            )
            session.add(user)
            await session.flush()  # Flush to get ID but don't commit
            
            user_id = user.id
            assert user_id is not None
            
            # Simulate an error to trigger rollback
            try:
                raise Exception("Simulated error")
            except Exception:
                # Session should rollback automatically
                pass
        
        # Verify user was not saved due to rollback
        async for session in test_db_manager.get_async_session():
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            assert count == 0

class TestUserModel:
    """Test User model operations."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, test_session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            is_active=True,
            is_verified=False
        )
        
        test_session.add(user)
        await test_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_user_preferences_json(self, test_session):
        """Test that user preferences are stored as JSON."""
        preferences = {
            "risk_tolerance": "high",
            "investment_horizon": "long",
            "notification_settings": {
                "email_alerts": False,
                "push_notifications": True
            }
        }
        
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            preferences=preferences
        )
        
        test_session.add(user)
        await test_session.commit()
        
        # Refresh from database
        await test_session.refresh(user)
        assert user.preferences["risk_tolerance"] == "high"
        assert user.preferences["notification_settings"]["email_alerts"] is False

class TestWatchlistModel:
    """Test Watchlist and WatchlistItem model operations."""
    
    @pytest.mark.asyncio
    async def test_create_watchlist_with_items(self, test_session):
        """Test creating a watchlist with items."""
        # Create user first
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )
        test_session.add(user)
        await test_session.flush()
        
        # Create watchlist
        watchlist = Watchlist(
            user_id=user.id,
            name="My Stocks",
            description="My favorite stocks",
            is_default=True
        )
        test_session.add(watchlist)
        await test_session.flush()
        
        # Add items to watchlist
        item1 = WatchlistItem(
            watchlist_id=watchlist.id,
            symbol="AAPL",
            company_name="Apple Inc.",
            target_price=150.00,
            notes="Great company"
        )
        
        item2 = WatchlistItem(
            watchlist_id=watchlist.id,
            symbol="GOOGL",
            company_name="Alphabet Inc.",
            target_price=2500.00
        )
        
        test_session.add_all([item1, item2])
        await test_session.commit()
        
        # Verify relationships
        await test_session.refresh(watchlist)
        assert len(watchlist.items) == 2
        assert watchlist.items[0].symbol in ["AAPL", "GOOGL"]
        assert watchlist.user.email == "test@example.com"

class TestAlertModel:
    """Test Alert model operations."""
    
    @pytest.mark.asyncio
    async def test_create_price_alert(self, test_session):
        """Test creating a price alert."""
        # Create user first
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )
        test_session.add(user)
        await test_session.flush()
        
        # Create alert
        from app.models.alert import AlertType, AlertStatus
        
        alert = Alert(
            user_id=user.id,
            symbol="AAPL",
            alert_type=AlertType.PRICE_ABOVE,
            status=AlertStatus.ACTIVE,
            condition_value=150.00,
            condition_operator=">",
            name="AAPL Price Alert",
            description="Alert when AAPL goes above $150",
            notify_email=True,
            notify_push=False,
            max_triggers=1,
            cooldown_minutes=60
        )
        
        test_session.add(alert)
        await test_session.commit()
        
        assert alert.id is not None
        assert alert.alert_type == AlertType.PRICE_ABOVE
        assert alert.status == AlertStatus.ACTIVE
        assert float(alert.condition_value) == 150.00

class TestChatModel:
    """Test Chat model operations."""
    
    @pytest.mark.asyncio
    async def test_create_chat_session_with_messages(self, test_session):
        """Test creating a chat session with messages."""
        # Create user first
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )
        test_session.add(user)
        await test_session.flush()
        
        # Create chat session
        session = ChatSession(
            user_id=user.id,
            title="Stock Analysis Chat",
            description="Discussing AAPL analysis",
            primary_symbols=["AAPL", "GOOGL"],
            analysis_types=["fundamental", "technical"]
        )
        test_session.add(session)
        await test_session.flush()
        
        # Add messages
        from app.models.chat import MessageType, MessageStatus
        
        user_message = ChatMessage(
            session_id=session.id,
            message_type=MessageType.USER,
            content="What do you think about AAPL?",
            status=MessageStatus.COMPLETED,
            symbols_mentioned=["AAPL"]
        )
        
        assistant_message = ChatMessage(
            session_id=session.id,
            message_type=MessageType.ASSISTANT,
            content="AAPL is showing strong fundamentals...",
            status=MessageStatus.COMPLETED,
            symbols_mentioned=["AAPL"],
            analysis_performed=["fundamental"],
            processing_time_ms=1500,
            token_count=45
        )
        
        test_session.add_all([user_message, assistant_message])
        await test_session.commit()
        
        # Verify relationships
        await test_session.refresh(session)
        assert len(session.messages) == 2
        assert session.messages[0].message_type in [MessageType.USER, MessageType.ASSISTANT]
        assert session.user.email == "test@example.com"

class TestDatabaseIntegration:
    """Test database integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_complex_query_with_joins(self, test_session):
        """Test complex queries with joins across multiple tables."""
        # Create user
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User"
        )
        test_session.add(user)
        await test_session.flush()
        
        # Create watchlist with items
        watchlist = Watchlist(
            user_id=user.id,
            name="Tech Stocks",
            is_default=True
        )
        test_session.add(watchlist)
        await test_session.flush()
        
        item = WatchlistItem(
            watchlist_id=watchlist.id,
            symbol="AAPL",
            company_name="Apple Inc."
        )
        test_session.add(item)
        
        # Create alert for same symbol
        from app.models.alert import AlertType, AlertStatus
        alert = Alert(
            user_id=user.id,
            symbol="AAPL",
            alert_type=AlertType.PRICE_ABOVE,
            status=AlertStatus.ACTIVE,
            name="AAPL Alert",
            condition_value=150.00,
            max_triggers=1
        )
        test_session.add(alert)
        
        await test_session.commit()
        
        # Query user with all related data
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        stmt = select(User).options(
            selectinload(User.watchlists).selectinload(Watchlist.items),
            selectinload(User.alerts)
        ).where(User.email == "test@example.com")
        
        result = await test_session.execute(stmt)
        loaded_user = result.scalar_one()
        
        assert loaded_user.full_name == "Test User"
        assert len(loaded_user.watchlists) == 1
        assert len(loaded_user.watchlists[0].items) == 1
        assert loaded_user.watchlists[0].items[0].symbol == "AAPL"
        assert len(loaded_user.alerts) == 1
        assert loaded_user.alerts[0].symbol == "AAPL"
    
    @pytest.mark.asyncio
    async def test_cascade_delete(self, test_session):
        """Test that cascade deletes work correctly."""
        # Create user with related data
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )
        test_session.add(user)
        await test_session.flush()
        
        # Create watchlist with items
        watchlist = Watchlist(
            user_id=user.id,
            name="Test Watchlist"
        )
        test_session.add(watchlist)
        await test_session.flush()
        
        item = WatchlistItem(
            watchlist_id=watchlist.id,
            symbol="AAPL"
        )
        test_session.add(item)
        await test_session.commit()
        
        # Delete user - should cascade to watchlist and items
        await test_session.delete(user)
        await test_session.commit()
        
        # Verify all related data was deleted
        watchlist_count = await test_session.execute(text("SELECT COUNT(*) FROM watchlists"))
        item_count = await test_session.execute(text("SELECT COUNT(*) FROM watchlist_items"))
        
        assert watchlist_count.scalar() == 0
        assert item_count.scalar() == 0

# Run tests with pytest-asyncio
if __name__ == "__main__":
    pytest.main([__file__, "-v"])