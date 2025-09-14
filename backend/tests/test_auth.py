"""
Tests for authentication functionality.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.auth import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password,
    validate_password_strength
)
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate, UserUpdate, UserUpdatePassword
from app.models.user import User


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Valid password
        assert validate_password_strength("TestPassword123!") is True
        
        # Test various invalid passwords
        with pytest.raises(Exception):
            validate_password_strength("short")  # Too short
        
        with pytest.raises(Exception):
            validate_password_strength("nouppercase123!")  # No uppercase
        
        with pytest.raises(Exception):
            validate_password_strength("NOLOWERCASE123!")  # No lowercase
        
        with pytest.raises(Exception):
            validate_password_strength("NoNumbers!")  # No numbers


class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_and_verify_token(self):
        """Test token creation and verification."""
        email = "test@example.com"
        token = create_access_token(subject=email)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token
        decoded_email = verify_token(token)
        assert decoded_email == email
    
    def test_expired_token(self):
        """Test expired token handling."""
        email = "test@example.com"
        # Create token that expires immediately
        token = create_access_token(
            subject=email, 
            expires_delta=timedelta(seconds=-1)
        )
        
        # Should return None for expired token
        decoded_email = verify_token(token)
        assert decoded_email is None
    
    def test_invalid_token(self):
        """Test invalid token handling."""
        invalid_token = "invalid.token.here"
        decoded_email = verify_token(invalid_token)
        assert decoded_email is None


class TestAuthService:
    """Test authentication service functionality."""
    
    def test_create_user(self, db_session: Session):
        """Test user creation."""
        auth_service = AuthService(db_session)
        
        user_data = UserCreate(
            email="test@example.com",
            password="TestPassword123!",
            confirm_password="TestPassword123!",
            full_name="Test User"
        )
        
        user = auth_service.create_user(user_data)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.hashed_password != "TestPassword123!"
        assert verify_password("TestPassword123!", user.hashed_password)
    
    def test_create_duplicate_user(self, db_session: Session):
        """Test creating user with duplicate email."""
        auth_service = AuthService(db_session)
        
        user_data = UserCreate(
            email="duplicate@example.com",
            password="TestPassword123!",
            confirm_password="TestPassword123!",
            full_name="Test User"
        )
        
        # Create first user
        auth_service.create_user(user_data)
        
        # Try to create duplicate
        with pytest.raises(Exception):
            auth_service.create_user(user_data)
    
    def test_authenticate_user(self, db_session: Session):
        """Test user authentication."""
        auth_service = AuthService(db_session)
        
        # Create user
        user_data = UserCreate(
            email="auth@example.com",
            password="TestPassword123!",
            confirm_password="TestPassword123!",
            full_name="Auth User"
        )
        created_user = auth_service.create_user(user_data)
        
        # Test successful authentication
        authenticated_user = auth_service.authenticate_user(
            "auth@example.com", 
            "TestPassword123!"
        )
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        
        # Test failed authentication
        failed_auth = auth_service.authenticate_user(
            "auth@example.com", 
            "WrongPassword"
        )
        assert failed_auth is None
        
        # Test non-existent user
        no_user = auth_service.authenticate_user(
            "nonexistent@example.com", 
            "TestPassword123!"
        )
        assert no_user is None
    
    def test_update_user(self, db_session: Session):
        """Test user profile updates."""
        auth_service = AuthService(db_session)
        
        # Create user
        user_data = UserCreate(
            email="update@example.com",
            password="TestPassword123!",
            confirm_password="TestPassword123!",
            full_name="Original Name"
        )
        user = auth_service.create_user(user_data)
        
        # Update user
        update_data = UserUpdate(
            full_name="Updated Name",
            preferences={
                "risk_tolerance": "aggressive",
                "theme": "dark"
            }
        )
        updated_user = auth_service.update_user(user, update_data)
        
        assert updated_user.full_name == "Updated Name"
        assert updated_user.preferences["risk_tolerance"] == "aggressive"
    
    def test_update_password(self, db_session: Session):
        """Test password updates."""
        auth_service = AuthService(db_session)
        
        # Create user
        user_data = UserCreate(
            email="password@example.com",
            password="OldPassword123!",
            confirm_password="OldPassword123!",
            full_name="Password User"
        )
        user = auth_service.create_user(user_data)
        
        # Update password
        password_data = UserUpdatePassword(
            current_password="OldPassword123!",
            new_password="NewPassword123!",
            confirm_new_password="NewPassword123!"
        )
        auth_service.update_user_password(user, password_data)
        
        # Test authentication with new password
        authenticated = auth_service.authenticate_user(
            "password@example.com", 
            "NewPassword123!"
        )
        assert authenticated is not None
        
        # Test old password no longer works
        old_auth = auth_service.authenticate_user(
            "password@example.com", 
            "OldPassword123!"
        )
        assert old_auth is None
    
    def test_create_tokens(self, db_session: Session):
        """Test token creation."""
        auth_service = AuthService(db_session)
        
        # Create user
        user_data = UserCreate(
            email="tokens@example.com",
            password="TestPassword123!",
            confirm_password="TestPassword123!",
            full_name="Token User"
        )
        user = auth_service.create_user(user_data)
        
        # Create tokens
        tokens = auth_service.create_tokens(user)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert "expires_in" in tokens
        assert tokens["token_type"] == "bearer"
        
        # Verify access token
        decoded_email = verify_token(tokens["access_token"])
        assert decoded_email == user.email


class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def test_register_endpoint(self, client: TestClient):
        """Test user registration endpoint."""
        user_data = {
            "email": "register@example.com",
            "password": "TestPassword123!",
            "confirm_password": "TestPassword123!",
            "full_name": "Register User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == "register@example.com"
        assert data["user"]["full_name"] == "Register User"
        assert "access_token" in data["token"]
    
    def test_login_endpoint(self, client: TestClient, test_user: User):
        """Test user login endpoint."""
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == test_user.email
        assert "access_token" in data["token"]
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_get_current_user(self, client: TestClient, auth_headers: dict):
        """Test getting current user profile."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "full_name" in data
        assert "preferences" in data
    
    def test_update_current_user(self, client: TestClient, auth_headers: dict):
        """Test updating current user profile."""
        update_data = {
            "full_name": "Updated Name",
            "preferences": {
                "risk_tolerance": "aggressive"
            }
        }
        
        response = client.put("/api/v1/auth/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
    
    def test_update_password(self, client: TestClient, auth_headers: dict):
        """Test password update endpoint."""
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword123!",
            "confirm_new_password": "NewPassword123!"
        }
        
        response = client.put("/api/v1/auth/me/password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 200
        assert "Password updated successfully" in response.json()["message"]
    
    def test_unauthorized_access(self, client: TestClient):
        """Test accessing protected endpoints without authentication."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_invalid_token(self, client: TestClient):
        """Test accessing protected endpoints with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401