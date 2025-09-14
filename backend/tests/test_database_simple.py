"""
Simple database integration tests for GCP Cloud SQL setup.
"""

import pytest
import asyncio
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.database import DatabaseManager, Base
from app.models import User, Watchlist, Alert
from app.models.alert import AlertType, AlertStatus

# Test database URL - using SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_settlers_of_stock.db"

class TestDatabaseSetup:
    """Test basic database setup and operations."""
    
    @pytest.mark.asyncio
    async def test_database_manager_creation(self):
        """Test that database manager can be created and initialized."""
        # Create a test database manager
        db_manager = DatabaseManager()
        
        # Override the database URL for testing
        original_url = db_manager._detect_cloud_sql_environment
        db_manager._is_cloud_sql = False
        
        # Set test database URL
        from app.core.config import get_settings
        settings = get_settings()
        original_db_url = settings.DATABASE_URL
        settings.DATABASE_URL = TEST_DATABASE_URL
        
        try:
            # Initialize database
            await db_manager.initialize_database()
            
            # Verify engines were created
            assert db_manager.async_engine is not None
            assert db_manager.AsyncSessionLocal is not None
            
            # Create tables
            async with db_manager.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Test basic connection
            async for session in db_manager.get_async_session():
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1
                break
            
        finally:
            # Cleanup
            if db_manager.async_engine:
                async with db_manager.async_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await db_manager.close_connections()
            
            # Restore original settings
            settings.DATABASE_URL = original_db_url
    
    @pytest.mark.asyncio
    async def test_user_model_operations(self):
        """Test basic User model operations."""
        # Setup test database
        db_manager = DatabaseManager()
        db_manager._is_cloud_sql = False
        
        from app.core.config import get_settings
        settings = get_settings()
        original_db_url = settings.DATABASE_URL
        settings.DATABASE_URL = TEST_DATABASE_URL
        
        try:
            await db_manager.initialize_database()
            
            # Create tables
            async with db_manager.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Test user creation
            async for session in db_manager.get_async_session():
                user = User(
                    email="test@example.com",
                    hashed_password="hashed_password",
                    full_name="Test User",
                    is_active=True,
                    is_verified=False
                )
                
                session.add(user)
                await session.commit()
                
                assert user.id is not None
                assert user.email == "test@example.com"
                assert user.created_at is not None
                break
            
        finally:
            # Cleanup
            if db_manager.async_engine:
                async with db_manager.async_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await db_manager.close_connections()
            
            settings.DATABASE_URL = original_db_url
    
    @pytest.mark.asyncio
    async def test_alert_model_operations(self):
        """Test basic Alert model operations."""
        # Setup test database
        db_manager = DatabaseManager()
        db_manager._is_cloud_sql = False
        
        from app.core.config import get_settings
        settings = get_settings()
        original_db_url = settings.DATABASE_URL
        settings.DATABASE_URL = TEST_DATABASE_URL
        
        try:
            await db_manager.initialize_database()
            
            # Create tables
            async with db_manager.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Test alert creation
            async for session in db_manager.get_async_session():
                # Create user first
                user = User(
                    email="test@example.com",
                    hashed_password="hashed_password"
                )
                session.add(user)
                await session.flush()
                
                # Create alert
                alert = Alert(
                    user_id=user.id,
                    symbol="AAPL",
                    alert_type=AlertType.PRICE_ABOVE,
                    status=AlertStatus.ACTIVE,
                    condition_value=150.00,
                    condition_operator=">",
                    name="AAPL Price Alert",
                    max_triggers=1,
                    cooldown_minutes=60
                )
                
                session.add(alert)
                await session.commit()
                
                assert alert.id is not None
                assert alert.alert_type == AlertType.PRICE_ABOVE
                assert alert.status == AlertStatus.ACTIVE
                assert float(alert.condition_value) == 150.00
                break
            
        finally:
            # Cleanup
            if db_manager.async_engine:
                async with db_manager.async_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await db_manager.close_connections()
            
            settings.DATABASE_URL = original_db_url
    
    @pytest.mark.asyncio
    async def test_relationships(self):
        """Test model relationships work correctly."""
        # Setup test database
        db_manager = DatabaseManager()
        db_manager._is_cloud_sql = False
        
        from app.core.config import get_settings
        settings = get_settings()
        original_db_url = settings.DATABASE_URL
        settings.DATABASE_URL = TEST_DATABASE_URL
        
        try:
            await db_manager.initialize_database()
            
            # Create tables
            async with db_manager.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Test relationships
            async for session in db_manager.get_async_session():
                # Create user
                user = User(
                    email="test@example.com",
                    hashed_password="hashed_password"
                )
                session.add(user)
                await session.flush()
                
                # Create watchlist
                watchlist = Watchlist(
                    user_id=user.id,
                    name="My Stocks",
                    is_default=True
                )
                session.add(watchlist)
                
                # Create alert
                alert = Alert(
                    user_id=user.id,
                    symbol="AAPL",
                    alert_type=AlertType.PRICE_ABOVE,
                    status=AlertStatus.ACTIVE,
                    name="AAPL Alert",
                    condition_value=150.00,
                    max_triggers=1
                )
                session.add(alert)
                
                await session.commit()
                
                # Test relationships
                await session.refresh(user)
                assert len(user.watchlists) == 1
                assert len(user.alerts) == 1
                assert user.watchlists[0].name == "My Stocks"
                assert user.alerts[0].symbol == "AAPL"
                break
            
        finally:
            # Cleanup
            if db_manager.async_engine:
                async with db_manager.async_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                await db_manager.close_connections()
            
            settings.DATABASE_URL = original_db_url

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])