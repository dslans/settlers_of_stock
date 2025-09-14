"""
Integration tests for authentication flow.
"""

import pytest
from fastapi.testclient import TestClient


class TestAuthenticationFlow:
    """Test complete authentication workflows."""
    
    def test_complete_registration_and_login_flow(self, client: TestClient):
        """Test complete user registration and login flow."""
        
        # 1. Register a new user
        registration_data = {
            "email": "integration@example.com",
            "password": "IntegrationTest123!",
            "confirm_password": "IntegrationTest123!",
            "full_name": "Integration Test User"
        }
        
        register_response = client.post("/api/v1/auth/register", json=registration_data)
        assert register_response.status_code == 201
        
        register_data = register_response.json()
        assert "user" in register_data
        assert "token" in register_data
        assert register_data["user"]["email"] == "integration@example.com"
        assert register_data["user"]["full_name"] == "Integration Test User"
        
        # Store the token for later use
        access_token = register_data["token"]["access_token"]
        
        # 2. Use the token to access protected endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()
        assert profile_data["email"] == "integration@example.com"
        assert profile_data["full_name"] == "Integration Test User"
        
        # 3. Login with the same credentials
        login_data = {
            "email": "integration@example.com",
            "password": "IntegrationTest123!"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        login_response_data = login_response.json()
        assert "user" in login_response_data
        assert "token" in login_response_data
        assert login_response_data["user"]["email"] == "integration@example.com"
        
        # 4. Use the new token to access protected endpoint
        new_access_token = login_response_data["token"]["access_token"]
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        
        profile_response_2 = client.get("/api/v1/auth/me", headers=new_headers)
        assert profile_response_2.status_code == 200
        
        profile_data_2 = profile_response_2.json()
        assert profile_data_2["email"] == "integration@example.com"
    
    def test_profile_update_flow(self, client: TestClient):
        """Test user profile update flow."""
        
        # 1. Register a user
        registration_data = {
            "email": "profileupdate@example.com",
            "password": "ProfileTest123!",
            "confirm_password": "ProfileTest123!",
            "full_name": "Profile Test User"
        }
        
        register_response = client.post("/api/v1/auth/register", json=registration_data)
        assert register_response.status_code == 201
        
        access_token = register_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Update profile
        update_data = {
            "full_name": "Updated Profile Name",
            "preferences": {
                "risk_tolerance": "aggressive",
                "investment_horizon": "long"
            }
        }
        
        update_response = client.put("/api/v1/auth/me", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        updated_profile = update_response.json()
        assert updated_profile["full_name"] == "Updated Profile Name"
        
        # 3. Verify the update persisted
        profile_response = client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()
        assert profile_data["full_name"] == "Updated Profile Name"
        assert profile_data["preferences"]["risk_tolerance"] == "aggressive"
        assert profile_data["preferences"]["investment_horizon"] == "long"
    
    def test_password_update_flow(self, client: TestClient):
        """Test password update flow."""
        
        # 1. Register a user
        registration_data = {
            "email": "passwordupdate@example.com",
            "password": "OldPassword123!",
            "confirm_password": "OldPassword123!",
            "full_name": "Password Test User"
        }
        
        register_response = client.post("/api/v1/auth/register", json=registration_data)
        assert register_response.status_code == 201
        
        access_token = register_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Update password
        password_update_data = {
            "current_password": "OldPassword123!",
            "new_password": "NewPassword123!",
            "confirm_new_password": "NewPassword123!"
        }
        
        password_response = client.put("/api/v1/auth/me/password", json=password_update_data, headers=headers)
        assert password_response.status_code == 200
        assert "Password updated successfully" in password_response.json()["message"]
        
        # 3. Try to login with old password (should fail)
        old_login_data = {
            "email": "passwordupdate@example.com",
            "password": "OldPassword123!"
        }
        
        old_login_response = client.post("/api/v1/auth/login", json=old_login_data)
        assert old_login_response.status_code == 401
        
        # 4. Login with new password (should succeed)
        new_login_data = {
            "email": "passwordupdate@example.com",
            "password": "NewPassword123!"
        }
        
        new_login_response = client.post("/api/v1/auth/login", json=new_login_data)
        assert new_login_response.status_code == 200
        
        login_data = new_login_response.json()
        assert login_data["user"]["email"] == "passwordupdate@example.com"
    
    def test_preferences_management_flow(self, client: TestClient):
        """Test user preferences management flow."""
        
        # 1. Register a user
        registration_data = {
            "email": "preferences@example.com",
            "password": "PreferencesTest123!",
            "confirm_password": "PreferencesTest123!",
            "full_name": "Preferences Test User"
        }
        
        register_response = client.post("/api/v1/auth/register", json=registration_data)
        assert register_response.status_code == 201
        
        access_token = register_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Get initial preferences
        prefs_response = client.get("/api/v1/auth/preferences", headers=headers)
        assert prefs_response.status_code == 200
        
        initial_prefs = prefs_response.json()
        assert initial_prefs["risk_tolerance"] == "moderate"
        assert initial_prefs["investment_horizon"] == "medium"
        
        # 3. Update preferences
        new_preferences = {
            "risk_tolerance": "conservative",
            "investment_horizon": "short",
            "display_settings": {
                "theme": "dark",
                "currency": "EUR"
            }
        }
        
        update_prefs_response = client.put("/api/v1/auth/preferences", json=new_preferences, headers=headers)
        assert update_prefs_response.status_code == 200
        
        updated_prefs = update_prefs_response.json()
        assert updated_prefs["risk_tolerance"] == "conservative"
        assert updated_prefs["investment_horizon"] == "short"
        assert updated_prefs["display_settings"]["theme"] == "dark"
        assert updated_prefs["display_settings"]["currency"] == "EUR"
        
        # 4. Verify preferences persisted
        final_prefs_response = client.get("/api/v1/auth/preferences", headers=headers)
        assert final_prefs_response.status_code == 200
        
        final_prefs = final_prefs_response.json()
        assert final_prefs["risk_tolerance"] == "conservative"
        assert final_prefs["display_settings"]["theme"] == "dark"
    
    def test_token_refresh_flow(self, client: TestClient):
        """Test token refresh flow."""
        
        # 1. Register a user
        registration_data = {
            "email": "tokenrefresh@example.com",
            "password": "TokenRefresh123!",
            "confirm_password": "TokenRefresh123!",
            "full_name": "Token Refresh User"
        }
        
        register_response = client.post("/api/v1/auth/register", json=registration_data)
        assert register_response.status_code == 201
        
        tokens = register_response.json()["token"]
        refresh_token = tokens["refresh_token"]
        
        # 2. Use refresh token to get new access token
        refresh_data = {
            "refresh_token": refresh_token
        }
        
        refresh_response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert refresh_response.status_code == 200
        
        new_token_data = refresh_response.json()
        assert "access_token" in new_token_data
        assert "token_type" in new_token_data
        assert new_token_data["token_type"] == "bearer"
        
        # 3. Use new access token to access protected endpoint
        new_access_token = new_token_data["access_token"]
        headers = {"Authorization": f"Bearer {new_access_token}"}
        
        profile_response = client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()
        assert profile_data["email"] == "tokenrefresh@example.com"
    
    def test_unauthorized_access_scenarios(self, client: TestClient):
        """Test various unauthorized access scenarios."""
        
        # 1. Access protected endpoint without token
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        
        # 2. Access protected endpoint with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/v1/auth/me", headers=invalid_headers)
        assert response.status_code == 401
        
        # 3. Access protected endpoint with malformed authorization header
        malformed_headers = {"Authorization": "InvalidFormat token_here"}
        response = client.get("/api/v1/auth/me", headers=malformed_headers)
        assert response.status_code == 401
        
        # 4. Try to refresh with invalid refresh token
        invalid_refresh_data = {
            "refresh_token": "invalid_refresh_token"
        }
        response = client.post("/api/v1/auth/refresh", json=invalid_refresh_data)
        assert response.status_code == 401