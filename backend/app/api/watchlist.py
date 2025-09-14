"""
Watchlist API endpoints for managing user watchlists and stock tracking.
"""

from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import get_current_active_user
from ..services.watchlist_service import WatchlistService
from ..schemas.watchlist import (
    WatchlistCreate, WatchlistUpdate, WatchlistResponse, WatchlistSummary,
    WatchlistItemCreate, WatchlistItemUpdate, WatchlistItemResponse,
    WatchlistBulkAddRequest, WatchlistBulkAddResponse,
    WatchlistStatsResponse, MessageResponse
)
from ..models.user import User

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("/", response_model=List[WatchlistSummary])
async def get_user_watchlists(
    include_items: bool = Query(False, description="Include watchlist items in response"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all watchlists for the current user.
    
    Returns a list of the user's watchlists, optionally including items.
    """
    watchlist_service = WatchlistService(db)
    watchlists = watchlist_service.get_user_watchlists(current_user, include_items=include_items)
    
    if include_items:
        # Return full watchlist responses with items
        return [WatchlistResponse.model_validate(w) for w in watchlists]
    else:
        # Return summary responses without items
        return [WatchlistSummary.model_validate(w) for w in watchlists]


@router.post("/", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    watchlist_data: WatchlistCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new watchlist for the current user.
    
    Creates a new watchlist with the provided name and description.
    """
    watchlist_service = WatchlistService(db)
    watchlist = watchlist_service.create_watchlist(current_user, watchlist_data)
    return WatchlistResponse.model_validate(watchlist)


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: int,
    include_market_data: bool = Query(True, description="Include real-time market data for items"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a specific watchlist by ID.
    
    Returns the watchlist with all items, optionally including real-time market data.
    """
    watchlist_service = WatchlistService(db)
    
    if include_market_data:
        watchlist = await watchlist_service.get_watchlist_with_market_data(current_user, watchlist_id)
    else:
        watchlist = watchlist_service.get_watchlist_by_id(current_user, watchlist_id, include_items=True)
    
    return WatchlistResponse.model_validate(watchlist)


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_id: int,
    update_data: WatchlistUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update a watchlist.
    
    Updates the watchlist name, description, or default status.
    """
    watchlist_service = WatchlistService(db)
    watchlist = watchlist_service.update_watchlist(current_user, watchlist_id, update_data)
    return WatchlistResponse.model_validate(watchlist)


@router.delete("/{watchlist_id}", response_model=MessageResponse)
async def delete_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete a watchlist.
    
    Deletes the specified watchlist and all its items.
    Cannot delete the last remaining watchlist.
    """
    watchlist_service = WatchlistService(db)
    watchlist_service.delete_watchlist(current_user, watchlist_id)
    return MessageResponse(message="Watchlist deleted successfully")


# Watchlist Items endpoints

@router.post("/{watchlist_id}/items", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_stock_to_watchlist(
    watchlist_id: int,
    item_data: WatchlistItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Add a stock to a watchlist.
    
    Adds a new stock to the specified watchlist with optional notes and target prices.
    """
    watchlist_service = WatchlistService(db)
    item = await watchlist_service.add_stock_to_watchlist(current_user, watchlist_id, item_data)
    return WatchlistItemResponse.model_validate(item)


@router.post("/{watchlist_id}/items/bulk", response_model=WatchlistBulkAddResponse)
async def bulk_add_stocks_to_watchlist(
    watchlist_id: int,
    bulk_data: WatchlistBulkAddRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Add multiple stocks to a watchlist.
    
    Adds multiple stocks to the watchlist in a single operation.
    Returns details about successful and failed additions.
    """
    watchlist_service = WatchlistService(db)
    result = await watchlist_service.bulk_add_stocks_to_watchlist(current_user, watchlist_id, bulk_data)
    return result


@router.put("/{watchlist_id}/items/{item_id}", response_model=WatchlistItemResponse)
async def update_watchlist_item(
    watchlist_id: int,
    item_id: int,
    update_data: WatchlistItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update a watchlist item.
    
    Updates notes, target prices, or other item-specific data.
    """
    watchlist_service = WatchlistService(db)
    item = watchlist_service.update_watchlist_item(current_user, watchlist_id, item_id, update_data)
    return WatchlistItemResponse.model_validate(item)


@router.delete("/{watchlist_id}/items/{item_id}", response_model=MessageResponse)
async def remove_stock_from_watchlist(
    watchlist_id: int,
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Remove a stock from a watchlist.
    
    Removes the specified stock from the watchlist.
    """
    watchlist_service = WatchlistService(db)
    watchlist_service.remove_stock_from_watchlist(current_user, watchlist_id, item_id)
    return MessageResponse(message="Stock removed from watchlist successfully")


# Statistics and utility endpoints

@router.get("/stats/summary", response_model=WatchlistStatsResponse)
async def get_watchlist_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get watchlist statistics for the current user.
    
    Returns summary statistics about the user's watchlists and most watched stocks.
    """
    watchlist_service = WatchlistService(db)
    stats = watchlist_service.get_user_watchlist_stats(current_user)
    return WatchlistStatsResponse(**stats)


@router.post("/default", response_model=WatchlistResponse)
async def ensure_default_watchlist(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Ensure user has a default watchlist.
    
    Creates a default watchlist if the user doesn't have any watchlists,
    or marks an existing watchlist as default if none is marked.
    """
    watchlist_service = WatchlistService(db)
    watchlist = watchlist_service.ensure_default_watchlist(current_user)
    return WatchlistResponse.model_validate(watchlist)


@router.get("/{watchlist_id}/refresh", response_model=WatchlistResponse)
async def refresh_watchlist_data(
    watchlist_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh market data for all stocks in a watchlist.
    
    Forces a refresh of real-time market data for all items in the watchlist.
    """
    watchlist_service = WatchlistService(db)
    # Clear cache and fetch fresh data
    watchlist_service.data_service.clear_cache()
    watchlist = await watchlist_service.get_watchlist_with_market_data(current_user, watchlist_id)
    return WatchlistResponse.model_validate(watchlist)