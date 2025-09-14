"""
Tests for watchlist service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.watchlist_service import WatchlistService
from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.watchlist import WatchlistCreate, WatchlistItemCreate, WatchlistBulkAddRequest
from app.services.data_aggregation import DataAggregationException


class TestWatchlistService:
    """Test watchlist service functionality."""
    
    def test_create_watchlist(self, db: Session, test_user: User):
        """Test creating a new watchlist."""
        service = WatchlistService(db)
        
        watchlist_data = WatchlistCreate(
            name="My Tech Stocks",
            description="Technology companies",
            is_default=True
        )
        
        watchlist = service.create_watchlist(test_user, watchlist_data)
        
        assert watchlist.name == "My Tech Stocks"
        assert watchlist.description == "Technology companies"
        assert watchlist.is_default == True
        assert watchlist.user_id == test_user.id
        assert watchlist.id is not None
    
    def test_create_default_watchlist_unsets_others(self, db: Session, test_user: User):
        """Test that creating a default watchlist unsets other defaults."""
        service = WatchlistService(db)
        
        # Create first default watchlist
        first_watchlist = service.create_watchlist(test_user, WatchlistCreate(
            name="First", is_default=True
        ))
        
        # Create second default watchlist
        second_watchlist = service.create_watchlist(test_user, WatchlistCreate(
            name="Second", is_default=True
        ))
        
        # Refresh first watchlist from database
        db.refresh(first_watchlist)
        
        assert first_watchlist.is_default == False
        assert second_watchlist.is_default == True
    
    def test_get_user_watchlists(self, db: Session, test_user: User):
        """Test getting all watchlists for a user."""
        service = WatchlistService(db)
        
        # Create test watchlists
        watchlist1 = service.create_watchlist(test_user, WatchlistCreate(name="Watchlist 1"))
        watchlist2 = service.create_watchlist(test_user, WatchlistCreate(name="Watchlist 2", is_default=True))
        
        watchlists = service.get_user_watchlists(test_user)
        
        assert len(watchlists) == 2
        # Default watchlist should be first
        assert watchlists[0].is_default == True
        assert watchlists[0].name == "Watchlist 2"
    
    def test_get_watchlist_by_id(self, db: Session, test_user: User, test_watchlist: Watchlist):
        """Test getting a specific watchlist by ID."""
        service = WatchlistService(db)
        
        watchlist = service.get_watchlist_by_id(test_user, test_watchlist.id)
        
        assert watchlist.id == test_watchlist.id
        assert watchlist.name == test_watchlist.name
    
    def test_get_watchlist_by_id_not_found(self, db: Session, test_user: User):
        """Test getting a non-existent watchlist."""
        service = WatchlistService(db)
        
        with pytest.raises(Exception) as exc_info:
            service.get_watchlist_by_id(test_user, 99999)
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_get_watchlist_by_id_wrong_user(self, db: Session, test_user: User):
        """Test getting a watchlist that belongs to another user."""
        service = WatchlistService(db)
        
        # Create another user and watchlist
        other_user = User(email="other@example.com", hashed_password="hashed")
        db.add(other_user)
        db.commit()
        
        other_watchlist = Watchlist(user_id=other_user.id, name="Other's Watchlist")
        db.add(other_watchlist)
        db.commit()
        
        with pytest.raises(Exception) as exc_info:
            service.get_watchlist_by_id(test_user, other_watchlist.id)
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_update_watchlist(self, db: Session, test_user: User, test_watchlist: Watchlist):
        """Test updating a watchlist."""
        service = WatchlistService(db)
        
        from app.schemas.watchlist import WatchlistUpdate
        update_data = WatchlistUpdate(
            name="Updated Name",
            description="Updated description"
        )
        
        updated_watchlist = service.update_watchlist(test_user, test_watchlist.id, update_data)
        
        assert updated_watchlist.name == "Updated Name"
        assert updated_watchlist.description == "Updated description"
    
    def test_delete_watchlist(self, db: Session, test_user: User):
        """Test deleting a watchlist."""
        service = WatchlistService(db)
        
        # Create two watchlists
        watchlist1 = service.create_watchlist(test_user, WatchlistCreate(name="Watchlist 1"))
        watchlist2 = service.create_watchlist(test_user, WatchlistCreate(name="Watchlist 2"))
        
        # Delete one
        service.delete_watchlist(test_user, watchlist2.id)
        
        # Verify it's deleted
        with pytest.raises(Exception):
            service.get_watchlist_by_id(test_user, watchlist2.id)
    
    def test_delete_last_watchlist_fails(self, db: Session, test_user: User, test_watchlist: Watchlist):
        """Test that deleting the last watchlist fails."""
        service = WatchlistService(db)
        
        with pytest.raises(Exception) as exc_info:
            service.delete_watchlist(test_user, test_watchlist.id)
        
        assert "cannot delete the last watchlist" in str(exc_info.value).lower()
    
    def test_delete_default_watchlist_promotes_another(self, db: Session, test_user: User):
        """Test that deleting default watchlist makes another one default."""
        service = WatchlistService(db)
        
        # Create two watchlists, first is default
        watchlist1 = service.create_watchlist(test_user, WatchlistCreate(name="Default", is_default=True))
        watchlist2 = service.create_watchlist(test_user, WatchlistCreate(name="Other"))
        
        # Delete default watchlist
        service.delete_watchlist(test_user, watchlist1.id)
        
        # Check that other watchlist became default
        db.refresh(watchlist2)
        assert watchlist2.is_default == True
    
    @patch('app.services.watchlist_service.DataAggregationService')
    async def test_add_stock_to_watchlist(self, mock_data_service_class, db: Session, test_user: User, test_watchlist: Watchlist):
        """Test adding a stock to a watchlist."""
        # Mock the data service
        mock_data_service = Mock()
        mock_stock_info = Mock()
        mock_stock_info.name = "Apple Inc."
        mock_data_service.get_stock_info = AsyncMock(return_value=mock_stock_info)
        mock_data_service_class.return_value = mock_data_service
        
        service = WatchlistService(db)
        
        item_data = WatchlistItemCreate(
            symbol="AAPL",
            notes="Great company",
            target_price=200.00
        )
        
        item = await service.add_stock_to_watchlist(test_user, test_watchlist.id, item_data)
        
        assert item.symbol == "AAPL"
        assert item.company_name == "Apple Inc."
        assert item.notes == "Great company"
        assert item.target_price == 200.00
        assert item.watchlist_id == test_watchlist.id
    
    @patch('app.services.watchlist_service.DataAggregationService')
    async def test_add_stock_invalid_symbol(self, mock_data_service_class, db: Session, test_user: User, test_watchlist: Watchlist):
        """Test adding an invalid stock symbol."""
        # Mock the data service to raise invalid symbol error
        mock_data_service = Mock()
        mock_data_service.get_stock_info = AsyncMock(
            side_effect=DataAggregationException("Invalid symbol", error_type="INVALID_SYMBOL", suggestions=["Check spelling"])
        )
        mock_data_service_class.return_value = mock_data_service
        
        service = WatchlistService(db)
        
        item_data = WatchlistItemCreate(symbol="INVALID")
        
        with pytest.raises(Exception) as exc_info:
            await service.add_stock_to_watchlist(test_user, test_watchlist.id, item_data)
        
        assert "invalid stock symbol" in str(exc_info.value).lower()
    
    @patch('app.services.watchlist_service.DataAggregationService')
    async def test_add_duplicate_stock(self, mock_data_service_class, db: Session, test_user: User, test_watchlist: Watchlist):
        """Test adding a duplicate stock to the same watchlist."""
        # Mock the data service
        mock_data_service = Mock()
        mock_stock_info = Mock()
        mock_stock_info.name = "Apple Inc."
        mock_data_service.get_stock_info = AsyncMock(return_value=mock_stock_info)
        mock_data_service_class.return_value = mock_data_service
        
        service = WatchlistService(db)
        
        item_data = WatchlistItemCreate(symbol="AAPL")
        
        # Add stock first time
        await service.add_stock_to_watchlist(test_user, test_watchlist.id, item_data)
        
        # Try to add same stock again
        with pytest.raises(Exception) as exc_info:
            await service.add_stock_to_watchlist(test_user, test_watchlist.id, item_data)
        
        assert "already in this watchlist" in str(exc_info.value).lower()
    
    @patch('app.services.watchlist_service.DataAggregationService')
    async def test_bulk_add_stocks(self, mock_data_service_class, db: Session, test_user: User, test_watchlist: Watchlist):
        """Test bulk adding stocks to a watchlist."""
        # Mock the data service
        mock_data_service = Mock()
        mock_stock_info = Mock()
        mock_stock_info.name = "Test Company"
        mock_data_service.get_stock_info = AsyncMock(return_value=mock_stock_info)
        mock_data_service_class.return_value = mock_data_service
        
        service = WatchlistService(db)
        
        bulk_data = WatchlistBulkAddRequest(symbols=["AAPL", "GOOGL", "MSFT"])
        
        result = await service.bulk_add_stocks_to_watchlist(test_user, test_watchlist.id, bulk_data)
        
        assert result.total_added == 3
        assert result.total_failed == 0
        assert len(result.added_symbols) == 3
        assert "AAPL" in result.added_symbols
        assert "GOOGL" in result.added_symbols
        assert "MSFT" in result.added_symbols
    
    @patch('app.services.watchlist_service.DataAggregationService')
    async def test_bulk_add_mixed_results(self, mock_data_service_class, db: Session, test_user: User, test_watchlist: Watchlist):
        """Test bulk adding with some successes and failures."""
        # Mock the data service
        mock_data_service = Mock()
        
        def mock_get_stock_info(symbol):
            if symbol == "INVALID":
                raise DataAggregationException("Invalid symbol", error_type="INVALID_SYMBOL")
            mock_stock_info = Mock()
            mock_stock_info.name = f"{symbol} Company"
            return mock_stock_info
        
        mock_data_service.get_stock_info = AsyncMock(side_effect=mock_get_stock_info)
        mock_data_service_class.return_value = mock_data_service
        
        service = WatchlistService(db)
        
        bulk_data = WatchlistBulkAddRequest(symbols=["AAPL", "INVALID", "GOOGL"])
        
        result = await service.bulk_add_stocks_to_watchlist(test_user, test_watchlist.id, bulk_data)
        
        assert result.total_added == 2
        assert result.total_failed == 1
        assert "AAPL" in result.added_symbols
        assert "GOOGL" in result.added_symbols
        assert len(result.failed_symbols) == 1
        assert result.failed_symbols[0]["symbol"] == "INVALID"
    
    def test_update_watchlist_item(self, db: Session, test_user: User, test_watchlist_item: WatchlistItem):
        """Test updating a watchlist item."""
        service = WatchlistService(db)
        
        from app.schemas.watchlist import WatchlistItemUpdate
        update_data = WatchlistItemUpdate(
            notes="Updated notes",
            target_price=250.00
        )
        
        updated_item = service.update_watchlist_item(
            test_user, test_watchlist_item.watchlist_id, test_watchlist_item.id, update_data
        )
        
        assert updated_item.notes == "Updated notes"
        assert updated_item.target_price == 250.00
    
    def test_remove_stock_from_watchlist(self, db: Session, test_user: User, test_watchlist_item: WatchlistItem):
        """Test removing a stock from a watchlist."""
        service = WatchlistService(db)
        
        # Remove the item
        service.remove_stock_from_watchlist(
            test_user, test_watchlist_item.watchlist_id, test_watchlist_item.id
        )
        
        # Verify it's removed
        watchlist = service.get_watchlist_by_id(test_user, test_watchlist_item.watchlist_id)
        assert len(watchlist.items) == 0
    
    @patch('app.services.watchlist_service.DataAggregationService')
    async def test_get_watchlist_with_market_data(self, mock_data_service_class, db: Session, test_user: User, test_watchlist_item: WatchlistItem):
        """Test getting watchlist with real-time market data."""
        # Mock the data service
        mock_data_service = Mock()
        mock_market_data = Mock()
        mock_market_data.price = 150.00
        mock_market_data.change = 5.00
        mock_market_data.change_percent = 3.45
        mock_market_data.volume = 1000000
        mock_market_data.timestamp = "2023-01-01T12:00:00Z"
        
        mock_data_service.get_multiple_market_data = AsyncMock(
            return_value={test_watchlist_item.symbol: mock_market_data}
        )
        mock_data_service_class.return_value = mock_data_service
        
        service = WatchlistService(db)
        
        watchlist = await service.get_watchlist_with_market_data(test_user, test_watchlist_item.watchlist_id)
        
        assert len(watchlist.items) == 1
        item = watchlist.items[0]
        assert item.current_price == 150.00
        assert item.daily_change == 5.00
        assert item.daily_change_percent == 3.45
        assert item.volume == 1000000
    
    def test_get_user_watchlist_stats(self, db: Session, test_user: User, test_watchlist_item: WatchlistItem):
        """Test getting user watchlist statistics."""
        service = WatchlistService(db)
        
        stats = service.get_user_watchlist_stats(test_user)
        
        assert stats["total_watchlists"] >= 1
        assert stats["total_items"] >= 1
        assert isinstance(stats["most_watched_symbols"], list)
        assert isinstance(stats["recent_additions"], list)
    
    def test_ensure_default_watchlist_creates_new(self, db: Session, test_user: User):
        """Test ensuring default watchlist when user has none."""
        service = WatchlistService(db)
        
        # Remove any existing watchlists
        db.query(Watchlist).filter(Watchlist.user_id == test_user.id).delete()
        db.commit()
        
        default_watchlist = service.ensure_default_watchlist(test_user)
        
        assert default_watchlist.is_default == True
        assert default_watchlist.user_id == test_user.id
        assert default_watchlist.name == "My Watchlist"
    
    def test_ensure_default_watchlist_marks_existing(self, db: Session, test_user: User, test_watchlist: Watchlist):
        """Test ensuring default watchlist when user has watchlists but none is default."""
        service = WatchlistService(db)
        
        # Ensure test watchlist is not default
        test_watchlist.is_default = False
        db.commit()
        
        default_watchlist = service.ensure_default_watchlist(test_user)
        
        assert default_watchlist.id == test_watchlist.id
        assert default_watchlist.is_default == True