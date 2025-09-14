"""
Tests for watchlist API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.watchlist import WatchlistCreate, WatchlistItemCreate


class TestWatchlistAPI:
    """Test watchlist API endpoints."""
    
    def test_get_user_watchlists_empty(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test getting watchlists when user has none."""
        response = client.get("/api/v1/watchlists/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_create_watchlist(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test creating a new watchlist."""
        watchlist_data = {
            "name": "My Tech Stocks",
            "description": "Technology companies I'm watching",
            "isDefault": True
        }
        
        response = client.post("/api/v1/watchlists/", json=watchlist_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == watchlist_data["name"]
        assert data["description"] == watchlist_data["description"]
        assert data["isDefault"] == watchlist_data["isDefault"]
        assert data["userId"] == test_user.id
        assert "id" in data
        assert "createdAt" in data
    
    def test_get_watchlist_by_id(self, client: TestClient, test_user: User, test_watchlist: Watchlist, auth_headers: dict):
        """Test getting a specific watchlist by ID."""
        response = client.get(f"/api/v1/watchlists/{test_watchlist.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_watchlist.id
        assert data["name"] == test_watchlist.name
        assert data["userId"] == test_user.id
        assert "items" in data
    
    def test_get_nonexistent_watchlist(self, client: TestClient, auth_headers: dict):
        """Test getting a watchlist that doesn't exist."""
        response = client.get("/api/v1/watchlists/99999", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_update_watchlist(self, client: TestClient, test_watchlist: Watchlist, auth_headers: dict):
        """Test updating a watchlist."""
        update_data = {
            "name": "Updated Watchlist Name",
            "description": "Updated description"
        }
        
        response = client.put(f"/api/v1/watchlists/{test_watchlist.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
    
    def test_delete_watchlist(self, client: TestClient, db: Session, test_user: User, auth_headers: dict):
        """Test deleting a watchlist."""
        # Create two watchlists so we can delete one
        watchlist1 = Watchlist(user_id=test_user.id, name="Watchlist 1", is_default=True)
        watchlist2 = Watchlist(user_id=test_user.id, name="Watchlist 2", is_default=False)
        db.add_all([watchlist1, watchlist2])
        db.commit()
        
        response = client.delete(f"/api/v1/watchlists/{watchlist2.id}", headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify watchlist is deleted
        response = client.get(f"/api/v1/watchlists/{watchlist2.id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_delete_last_watchlist_fails(self, client: TestClient, test_watchlist: Watchlist, auth_headers: dict):
        """Test that deleting the last watchlist fails."""
        response = client.delete(f"/api/v1/watchlists/{test_watchlist.id}", headers=auth_headers)
        
        assert response.status_code == 400
        assert "Cannot delete the last watchlist" in response.json()["detail"]
    
    @patch('app.services.watchlist_service.DataAggregationService')
    def test_add_stock_to_watchlist(self, mock_data_service, client: TestClient, test_watchlist: Watchlist, auth_headers: dict):
        """Test adding a stock to a watchlist."""
        # Mock the data service
        mock_stock_info = Mock()
        mock_stock_info.name = "Apple Inc."
        mock_data_service.return_value.get_stock_info.return_value = mock_stock_info
        
        stock_data = {
            "symbol": "AAPL",
            "notes": "Great company",
            "targetPrice": 200.00
        }
        
        response = client.post(f"/api/v1/watchlists/{test_watchlist.id}/items", json=stock_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["notes"] == stock_data["notes"]
        assert data["targetPrice"] == stock_data["targetPrice"]
        assert data["watchlistId"] == test_watchlist.id
    
    @patch('app.services.watchlist_service.DataAggregationService')
    def test_bulk_add_stocks(self, mock_data_service, client: TestClient, test_watchlist: Watchlist, auth_headers: dict):
        """Test bulk adding stocks to a watchlist."""
        # Mock the data service
        mock_stock_info = Mock()
        mock_stock_info.name = "Test Company"
        mock_data_service.return_value.get_stock_info.return_value = mock_stock_info
        
        bulk_data = {
            "symbols": ["AAPL", "GOOGL", "MSFT"]
        }
        
        response = client.post(f"/api/v1/watchlists/{test_watchlist.id}/items/bulk", json=bulk_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["totalAdded"] == 3
        assert data["totalFailed"] == 0
        assert len(data["addedSymbols"]) == 3
    
    def test_update_watchlist_item(self, client: TestClient, test_watchlist_item: WatchlistItem, auth_headers: dict):
        """Test updating a watchlist item."""
        update_data = {
            "notes": "Updated notes",
            "targetPrice": 250.00
        }
        
        response = client.put(
            f"/api/v1/watchlists/{test_watchlist_item.watchlist_id}/items/{test_watchlist_item.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == update_data["notes"]
        assert data["targetPrice"] == update_data["targetPrice"]
    
    def test_remove_stock_from_watchlist(self, client: TestClient, test_watchlist_item: WatchlistItem, auth_headers: dict):
        """Test removing a stock from a watchlist."""
        response = client.delete(
            f"/api/v1/watchlists/{test_watchlist_item.watchlist_id}/items/{test_watchlist_item.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify item is removed by checking the watchlist
        response = client.get(f"/api/v1/watchlists/{test_watchlist_item.watchlist_id}", headers=auth_headers)
        data = response.json()
        assert len(data["items"]) == 0
    
    def test_get_watchlist_stats(self, client: TestClient, test_watchlist_item: WatchlistItem, auth_headers: dict):
        """Test getting watchlist statistics."""
        response = client.get("/api/v1/watchlists/stats/summary", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "totalWatchlists" in data
        assert "totalItems" in data
        assert "mostWatchedSymbols" in data
        assert data["totalWatchlists"] >= 1
        assert data["totalItems"] >= 1
    
    def test_ensure_default_watchlist(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test ensuring a default watchlist exists."""
        response = client.post("/api/v1/watchlists/default", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["isDefault"] == True
        assert data["userId"] == test_user.id
    
    @patch('app.services.watchlist_service.DataAggregationService')
    def test_refresh_watchlist_data(self, mock_data_service, client: TestClient, test_watchlist_item: WatchlistItem, auth_headers: dict):
        """Test refreshing watchlist market data."""
        # Mock market data
        mock_market_data = {
            test_watchlist_item.symbol: Mock(
                price=150.00,
                change=5.00,
                change_percent=3.45,
                volume=1000000,
                timestamp="2023-01-01T12:00:00Z"
            )
        }
        mock_data_service.return_value.get_multiple_market_data.return_value = mock_market_data
        
        response = client.get(f"/api/v1/watchlists/{test_watchlist_item.watchlist_id}/refresh", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        # Market data should be attached to items
        item = data["items"][0]
        assert "currentPrice" in item
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that watchlist endpoints require authentication."""
        response = client.get("/api/v1/watchlists/")
        assert response.status_code == 401
        
        response = client.post("/api/v1/watchlists/", json={"name": "Test"})
        assert response.status_code == 401
    
    def test_access_other_user_watchlist(self, client: TestClient, db: Session, auth_headers: dict):
        """Test that users cannot access other users' watchlists."""
        # Create another user and watchlist
        other_user = User(email="other@example.com", hashed_password="hashed", full_name="Other User")
        db.add(other_user)
        db.commit()
        
        other_watchlist = Watchlist(user_id=other_user.id, name="Other's Watchlist")
        db.add(other_watchlist)
        db.commit()
        
        # Try to access other user's watchlist
        response = client.get(f"/api/v1/watchlists/{other_watchlist.id}", headers=auth_headers)
        assert response.status_code == 404


class TestWatchlistValidation:
    """Test watchlist input validation."""
    
    def test_create_watchlist_invalid_data(self, client: TestClient, auth_headers: dict):
        """Test creating watchlist with invalid data."""
        # Empty name
        response = client.post("/api/v1/watchlists/", json={"name": ""}, headers=auth_headers)
        assert response.status_code == 422
        
        # Missing name
        response = client.post("/api/v1/watchlists/", json={"description": "Test"}, headers=auth_headers)
        assert response.status_code == 422
    
    def test_add_stock_invalid_symbol(self, client: TestClient, test_watchlist: Watchlist, auth_headers: dict):
        """Test adding stock with invalid symbol."""
        # Empty symbol
        response = client.post(
            f"/api/v1/watchlists/{test_watchlist.id}/items",
            json={"symbol": ""},
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Invalid characters
        response = client.post(
            f"/api/v1/watchlists/{test_watchlist.id}/items",
            json={"symbol": "INVALID@SYMBOL"},
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_add_stock_negative_prices(self, client: TestClient, test_watchlist: Watchlist, auth_headers: dict):
        """Test adding stock with negative prices."""
        response = client.post(
            f"/api/v1/watchlists/{test_watchlist.id}/items",
            json={
                "symbol": "AAPL",
                "targetPrice": -100.00
            },
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_bulk_add_empty_symbols(self, client: TestClient, test_watchlist: Watchlist, auth_headers: dict):
        """Test bulk add with empty symbols list."""
        response = client.post(
            f"/api/v1/watchlists/{test_watchlist.id}/items/bulk",
            json={"symbols": []},
            headers=auth_headers
        )
        assert response.status_code == 422


class TestWatchlistBusinessLogic:
    """Test watchlist business logic."""
    
    def test_default_watchlist_logic(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test default watchlist behavior."""
        # Create first watchlist as default
        response = client.post("/api/v1/watchlists/", json={
            "name": "First Watchlist",
            "isDefault": True
        }, headers=auth_headers)
        assert response.status_code == 201
        first_id = response.json()["id"]
        
        # Create second watchlist as default - should unset first
        response = client.post("/api/v1/watchlists/", json={
            "name": "Second Watchlist", 
            "isDefault": True
        }, headers=auth_headers)
        assert response.status_code == 201
        
        # Check that first is no longer default
        response = client.get(f"/api/v1/watchlists/{first_id}", headers=auth_headers)
        assert response.json()["isDefault"] == False
    
    @patch('app.services.watchlist_service.DataAggregationService')
    def test_duplicate_stock_prevention(self, mock_data_service, client: TestClient, test_watchlist: Watchlist, auth_headers: dict):
        """Test that duplicate stocks cannot be added to the same watchlist."""
        # Mock the data service
        mock_stock_info = Mock()
        mock_stock_info.name = "Apple Inc."
        mock_data_service.return_value.get_stock_info.return_value = mock_stock_info
        
        # Add stock first time
        response = client.post(
            f"/api/v1/watchlists/{test_watchlist.id}/items",
            json={"symbol": "AAPL"},
            headers=auth_headers
        )
        assert response.status_code == 201
        
        # Try to add same stock again
        response = client.post(
            f"/api/v1/watchlists/{test_watchlist.id}/items",
            json={"symbol": "AAPL"},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "already in this watchlist" in response.json()["detail"]