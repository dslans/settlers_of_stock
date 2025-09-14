"""
Pytest configuration and fixtures for testing.
"""

import pytest
from typing import Generator, Dict
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.auth import create_access_token
from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate
from main import app

# Test database URL (SQLite in memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_settlers_of_stock.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create database engine for testing."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session override."""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """Create a test user for authentication testing."""
    auth_service = AuthService(db_session)
    
    user_data = UserCreate(
        email="testuser@example.com",
        password="TestPassword123!",
        confirm_password="TestPassword123!",
        full_name="Test User",
        preferences={
            "risk_tolerance": "moderate",
            "investment_horizon": "medium",
            "preferred_analysis": ["fundamental", "technical"],
            "notification_settings": {
                "email_alerts": True,
                "push_notifications": True,
                "price_alerts": True,
                "news_alerts": False
            },
            "display_settings": {
                "theme": "light",
                "currency": "USD",
                "chart_type": "candlestick"
            }
        }
    )
    
    user = auth_service.create_user(user_data)
    # Mark user as verified for testing
    user.is_verified = True
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def test_user_token(test_user: User) -> str:
    """Create an access token for the test user."""
    return create_access_token(subject=test_user.email)


@pytest.fixture(scope="function")
def auth_headers(test_user_token: str) -> Dict[str, str]:
    """Create authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture(scope="function")
def inactive_user(db_session: Session) -> User:
    """Create an inactive test user."""
    auth_service = AuthService(db_session)
    
    user_data = UserCreate(
        email="inactive@example.com",
        password="TestPassword123!",
        confirm_password="TestPassword123!",
        full_name="Inactive User"
    )
    
    user = auth_service.create_user(user_data)
    user.is_active = False
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def unverified_user(db_session: Session) -> User:
    """Create an unverified test user."""
    auth_service = AuthService(db_session)
    
    user_data = UserCreate(
        email="unverified@example.com",
        password="TestPassword123!",
        confirm_password="TestPassword123!",
        full_name="Unverified User"
    )
    
    user = auth_service.create_user(user_data)
    # User is created as unverified by default
    
    return user


@pytest.fixture(scope="function")
def multiple_users(db_session: Session) -> list[User]:
    """Create multiple test users for testing."""
    auth_service = AuthService(db_session)
    users = []
    
    for i in range(3):
        user_data = UserCreate(
            email=f"user{i}@example.com",
            password="TestPassword123!",
            confirm_password="TestPassword123!",
            full_name=f"Test User {i}"
        )
        
        user = auth_service.create_user(user_data)
        user.is_verified = True
        users.append(user)
    
    db_session.commit()
    for user in users:
        db_session.refresh(user)
    
    return users


# Mock data fixtures
@pytest.fixture
def sample_user_preferences():
    """Sample user preferences for testing."""
    return {
        "risk_tolerance": "aggressive",
        "investment_horizon": "long",
        "preferred_analysis": ["fundamental", "technical", "sentiment"],
        "notification_settings": {
            "email_alerts": True,
            "push_notifications": False,
            "price_alerts": True,
            "news_alerts": True
        },
        "display_settings": {
            "theme": "dark",
            "currency": "EUR",
            "chart_type": "line"
        }
    }


@pytest.fixture
def sample_user_create_data():
    """Sample user creation data for testing."""
    return {
        "email": "newuser@example.com",
        "password": "NewPassword123!",
        "confirm_password": "NewPassword123!",
        "full_name": "New User",
        "preferences": {
            "risk_tolerance": "conservative",
            "investment_horizon": "short"
        }
    }


@pytest.fixture
def sample_login_data():
    """Sample login data for testing."""
    return {
        "email": "testuser@example.com",
        "password": "TestPassword123!"
    }


@pytest.fixture
def sample_password_update_data():
    """Sample password update data for testing."""
    return {
        "current_password": "TestPassword123!",
        "new_password": "NewPassword456!",
        "confirm_new_password": "NewPassword456!"
    }


# Watchlist fixtures
@pytest.fixture(scope="function")
def test_watchlist(db_session: Session, test_user: User) -> Watchlist:
    """Create a test watchlist."""
    watchlist = Watchlist(
        user_id=test_user.id,
        name="Test Watchlist",
        description="A test watchlist",
        is_default=True
    )
    db_session.add(watchlist)
    db_session.commit()
    db_session.refresh(watchlist)
    return watchlist


@pytest.fixture(scope="function")
def test_watchlist_item(db_session: Session, test_watchlist: Watchlist) -> WatchlistItem:
    """Create a test watchlist item."""
    item = WatchlistItem(
        watchlist_id=test_watchlist.id,
        symbol="AAPL",
        company_name="Apple Inc.",
        notes="Test stock",
        target_price=200.00,
        entry_price=150.00,
        shares_owned=10.0
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


# Alias for compatibility
@pytest.fixture(scope="function")
def db(db_session: Session) -> Session:
    """Alias for db_session fixture."""
    return db_session