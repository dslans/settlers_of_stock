"""
Watchlist Service for managing user watchlists and stock tracking.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from fastapi import HTTPException, status

from ..models.watchlist import Watchlist, WatchlistItem
from ..models.user import User
from ..schemas.watchlist import (
    WatchlistCreate, WatchlistUpdate, WatchlistItemCreate, WatchlistItemUpdate,
    WatchlistBulkAddRequest, WatchlistBulkAddResponse
)
from .data_aggregation import DataAggregationService, DataAggregationException

logger = logging.getLogger(__name__)


class WatchlistService:
    """Service for managing watchlists and watchlist items."""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_service = DataAggregationService()
    
    # Watchlist CRUD operations
    
    def create_watchlist(self, user: User, watchlist_data: WatchlistCreate) -> Watchlist:
        """Create a new watchlist for the user."""
        try:
            # If this is set as default, unset other default watchlists
            if watchlist_data.is_default:
                self.db.query(Watchlist).filter(
                    and_(Watchlist.user_id == user.id, Watchlist.is_default == True)
                ).update({"is_default": False})
            
            # Create new watchlist
            watchlist = Watchlist(
                user_id=user.id,
                name=watchlist_data.name,
                description=watchlist_data.description,
                is_default=watchlist_data.is_default
            )
            
            self.db.add(watchlist)
            self.db.commit()
            self.db.refresh(watchlist)
            
            logger.info(f"Created watchlist '{watchlist.name}' for user {user.id}")
            return watchlist
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create watchlist for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create watchlist"
            )
    
    def get_user_watchlists(self, user: User, include_items: bool = False) -> List[Watchlist]:
        """Get all watchlists for a user."""
        try:
            query = self.db.query(Watchlist).filter(Watchlist.user_id == user.id)
            
            if include_items:
                from sqlalchemy.orm import joinedload
                query = query.options(joinedload(Watchlist.items))
            
            watchlists = query.order_by(desc(Watchlist.is_default), Watchlist.name).all()
            
            return watchlists
            
        except Exception as e:
            logger.error(f"Failed to get watchlists for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve watchlists"
            )
    
    def get_watchlist_by_id(self, user: User, watchlist_id: int, include_items: bool = True) -> Watchlist:
        """Get a specific watchlist by ID."""
        try:
            query = self.db.query(Watchlist).filter(
                and_(Watchlist.id == watchlist_id, Watchlist.user_id == user.id)
            )
            
            if include_items:
                from sqlalchemy.orm import joinedload
                query = query.options(joinedload(Watchlist.items))
            
            watchlist = query.first()
            
            if not watchlist:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Watchlist not found"
                )
            
            return watchlist
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get watchlist {watchlist_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve watchlist"
            )
    
    def update_watchlist(self, user: User, watchlist_id: int, update_data: WatchlistUpdate) -> Watchlist:
        """Update a watchlist."""
        try:
            watchlist = self.get_watchlist_by_id(user, watchlist_id, include_items=False)
            
            # If setting as default, unset other default watchlists
            if update_data.is_default:
                self.db.query(Watchlist).filter(
                    and_(Watchlist.user_id == user.id, Watchlist.id != watchlist_id, Watchlist.is_default == True)
                ).update({"is_default": False})
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(watchlist, field, value)
            
            self.db.commit()
            self.db.refresh(watchlist)
            
            logger.info(f"Updated watchlist {watchlist_id} for user {user.id}")
            return watchlist
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update watchlist {watchlist_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update watchlist"
            )
    
    def delete_watchlist(self, user: User, watchlist_id: int) -> None:
        """Delete a watchlist."""
        try:
            watchlist = self.get_watchlist_by_id(user, watchlist_id, include_items=False)
            
            # Don't allow deletion of the last watchlist
            total_watchlists = self.db.query(Watchlist).filter(Watchlist.user_id == user.id).count()
            if total_watchlists <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last watchlist. Create another watchlist first."
                )
            
            # If deleting default watchlist, make another one default
            if watchlist.is_default:
                other_watchlist = self.db.query(Watchlist).filter(
                    and_(Watchlist.user_id == user.id, Watchlist.id != watchlist_id)
                ).first()
                if other_watchlist:
                    other_watchlist.is_default = True
            
            self.db.delete(watchlist)
            self.db.commit()
            
            logger.info(f"Deleted watchlist {watchlist_id} for user {user.id}")
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete watchlist {watchlist_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete watchlist"
            )
    
    # Watchlist Item operations
    
    async def add_stock_to_watchlist(self, user: User, watchlist_id: int, item_data: WatchlistItemCreate) -> WatchlistItem:
        """Add a stock to a watchlist."""
        try:
            # Verify watchlist ownership
            watchlist = self.get_watchlist_by_id(user, watchlist_id, include_items=False)
            
            # Validate stock symbol
            symbol = item_data.symbol.upper().strip()
            try:
                stock_info = await self.data_service.get_stock_info(symbol)
                company_name = item_data.company_name or stock_info.name
            except DataAggregationException as e:
                if e.error_type == "INVALID_SYMBOL":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid stock symbol: {symbol}. {', '.join(e.suggestions)}"
                    )
                else:
                    # Use provided company name if API fails
                    company_name = item_data.company_name or symbol
                    logger.warning(f"Could not fetch company info for {symbol}, using provided name")
            
            # Check if stock already exists in this watchlist
            existing_item = self.db.query(WatchlistItem).filter(
                and_(WatchlistItem.watchlist_id == watchlist_id, WatchlistItem.symbol == symbol)
            ).first()
            
            if existing_item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stock {symbol} is already in this watchlist"
                )
            
            # Create watchlist item
            watchlist_item = WatchlistItem(
                watchlist_id=watchlist_id,
                symbol=symbol,
                company_name=company_name,
                notes=item_data.notes,
                target_price=item_data.target_price,
                entry_price=item_data.entry_price,
                shares_owned=item_data.shares_owned
            )
            
            self.db.add(watchlist_item)
            self.db.commit()
            self.db.refresh(watchlist_item)
            
            logger.info(f"Added {symbol} to watchlist {watchlist_id} for user {user.id}")
            return watchlist_item
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add stock to watchlist {watchlist_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add stock to watchlist"
            )
    
    async def bulk_add_stocks_to_watchlist(self, user: User, watchlist_id: int, bulk_data: WatchlistBulkAddRequest) -> WatchlistBulkAddResponse:
        """Add multiple stocks to a watchlist."""
        try:
            # Verify watchlist ownership
            watchlist = self.get_watchlist_by_id(user, watchlist_id, include_items=False)
            
            added_symbols = []
            failed_symbols = []
            
            for symbol in bulk_data.symbols:
                try:
                    # Check if already exists
                    existing_item = self.db.query(WatchlistItem).filter(
                        and_(WatchlistItem.watchlist_id == watchlist_id, WatchlistItem.symbol == symbol)
                    ).first()
                    
                    if existing_item:
                        failed_symbols.append({
                            "symbol": symbol,
                            "error": "Already in watchlist"
                        })
                        continue
                    
                    # Validate symbol and get company name
                    try:
                        stock_info = await self.data_service.get_stock_info(symbol)
                        company_name = stock_info.name
                    except DataAggregationException:
                        company_name = symbol  # Use symbol as fallback
                    
                    # Create item
                    item_data = WatchlistItemCreate(symbol=symbol, company_name=company_name)
                    await self.add_stock_to_watchlist(user, watchlist_id, item_data)
                    added_symbols.append(symbol)
                    
                except HTTPException as e:
                    if e.status_code == 400:  # Bad request (already exists, invalid symbol)
                        failed_symbols.append({
                            "symbol": symbol,
                            "error": e.detail
                        })
                    else:
                        raise e
                except Exception as e:
                    failed_symbols.append({
                        "symbol": symbol,
                        "error": str(e)
                    })
            
            return WatchlistBulkAddResponse(
                added_symbols=added_symbols,
                failed_symbols=failed_symbols,
                total_added=len(added_symbols),
                total_failed=len(failed_symbols)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed bulk add to watchlist {watchlist_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add stocks to watchlist"
            )
    
    def update_watchlist_item(self, user: User, watchlist_id: int, item_id: int, update_data: WatchlistItemUpdate) -> WatchlistItem:
        """Update a watchlist item."""
        try:
            # Verify watchlist ownership
            watchlist = self.get_watchlist_by_id(user, watchlist_id, include_items=False)
            
            # Get the item
            item = self.db.query(WatchlistItem).filter(
                and_(WatchlistItem.id == item_id, WatchlistItem.watchlist_id == watchlist_id)
            ).first()
            
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Watchlist item not found"
                )
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(item, field, value)
            
            self.db.commit()
            self.db.refresh(item)
            
            logger.info(f"Updated watchlist item {item_id} for user {user.id}")
            return item
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update watchlist item {item_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update watchlist item"
            )
    
    def remove_stock_from_watchlist(self, user: User, watchlist_id: int, item_id: int) -> None:
        """Remove a stock from a watchlist."""
        try:
            # Verify watchlist ownership
            watchlist = self.get_watchlist_by_id(user, watchlist_id, include_items=False)
            
            # Get the item
            item = self.db.query(WatchlistItem).filter(
                and_(WatchlistItem.id == item_id, WatchlistItem.watchlist_id == watchlist_id)
            ).first()
            
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Watchlist item not found"
                )
            
            symbol = item.symbol
            self.db.delete(item)
            self.db.commit()
            
            logger.info(f"Removed {symbol} from watchlist {watchlist_id} for user {user.id}")
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to remove watchlist item {item_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove stock from watchlist"
            )
    
    # Real-time data operations
    
    async def get_watchlist_with_market_data(self, user: User, watchlist_id: int) -> Watchlist:
        """Get watchlist with real-time market data for all items."""
        try:
            watchlist = self.get_watchlist_by_id(user, watchlist_id, include_items=True)
            
            if not watchlist.items:
                return watchlist
            
            # Get symbols
            symbols = [item.symbol for item in watchlist.items]
            
            # Fetch market data for all symbols
            market_data_dict = await self.data_service.get_multiple_market_data(symbols)
            
            # Attach market data to items
            for item in watchlist.items:
                market_data = market_data_dict.get(item.symbol)
                if market_data:
                    item.current_price = market_data.price
                    item.daily_change = market_data.change
                    item.daily_change_percent = market_data.change_percent
                    item.volume = market_data.volume
                    item.last_updated = market_data.timestamp
                    item.is_market_open = True  # Simplified - could be enhanced
            
            return watchlist
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get watchlist with market data for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve watchlist with market data"
            )
    
    def get_user_watchlist_stats(self, user: User) -> Dict[str, Any]:
        """Get statistics about user's watchlists."""
        try:
            # Basic counts
            total_watchlists = self.db.query(Watchlist).filter(Watchlist.user_id == user.id).count()
            total_items = self.db.query(WatchlistItem).join(Watchlist).filter(Watchlist.user_id == user.id).count()
            
            # Most watched symbols across all user's watchlists
            most_watched = self.db.query(
                WatchlistItem.symbol,
                func.count(WatchlistItem.symbol).label('count')
            ).join(Watchlist).filter(
                Watchlist.user_id == user.id
            ).group_by(WatchlistItem.symbol).order_by(desc('count')).limit(10).all()
            
            most_watched_symbols = [{"symbol": symbol, "count": count} for symbol, count in most_watched]
            
            # Recent additions (last 10)
            recent_items = self.db.query(WatchlistItem).join(Watchlist).filter(
                Watchlist.user_id == user.id
            ).order_by(desc(WatchlistItem.added_at)).limit(10).all()
            
            recent_additions = [item.symbol for item in recent_items]
            
            return {
                "total_watchlists": total_watchlists,
                "total_items": total_items,
                "most_watched_symbols": most_watched_symbols,
                "recent_additions": recent_additions,
                "performance_summary": {}  # Could be enhanced with actual performance calculations
            }
            
        except Exception as e:
            logger.error(f"Failed to get watchlist stats for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve watchlist statistics"
            )
    
    def ensure_default_watchlist(self, user: User) -> Watchlist:
        """Ensure user has a default watchlist, create one if needed."""
        try:
            # Check if user has any watchlists
            existing_watchlists = self.get_user_watchlists(user)
            
            if not existing_watchlists:
                # Create default watchlist
                default_watchlist_data = WatchlistCreate(
                    name="My Watchlist",
                    description="Default watchlist",
                    is_default=True
                )
                return self.create_watchlist(user, default_watchlist_data)
            
            # Check if any is marked as default
            default_watchlist = next((w for w in existing_watchlists if w.is_default), None)
            
            if not default_watchlist:
                # Mark first watchlist as default
                first_watchlist = existing_watchlists[0]
                first_watchlist.is_default = True
                self.db.commit()
                return first_watchlist
            
            return default_watchlist
            
        except Exception as e:
            logger.error(f"Failed to ensure default watchlist for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create default watchlist"
            )