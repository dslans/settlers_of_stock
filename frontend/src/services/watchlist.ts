import { apiClient } from './api';
import {
  Watchlist,
  WatchlistSummary,
  WatchlistItem,
  WatchlistCreateRequest,
  WatchlistUpdateRequest,
  WatchlistItemCreateRequest,
  WatchlistItemUpdateRequest,
  WatchlistBulkAddRequest,
  WatchlistBulkAddResponse,
  WatchlistStats,
} from '../types';

// ============================================================================
// WATCHLIST API FUNCTIONS
// ============================================================================

/**
 * Get all watchlists for the current user
 */
export const getUserWatchlists = async (includeItems: boolean = false): Promise<WatchlistSummary[] | Watchlist[]> => {
  try {
    const response = await apiClient.get('/api/v1/watchlists/', {
      params: { include_items: includeItems }
    });
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail || 'Failed to get watchlists');
    }
    throw new Error('Network error while fetching watchlists');
  }
};

/**
 * Create a new watchlist
 */
export const createWatchlist = async (watchlistData: WatchlistCreateRequest): Promise<Watchlist> => {
  try {
    const response = await apiClient.post('/api/v1/watchlists/', watchlistData);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail || 'Failed to create watchlist');
    }
    throw new Error('Network error while creating watchlist');
  }
};

/**
 * Get a specific watchlist by ID
 */
export const getWatchlist = async (
  watchlistId: number, 
  includeMarketData: boolean = true
): Promise<Watchlist> => {
  try {
    const response = await apiClient.get(`/api/v1/watchlists/${watchlistId}`, {
      params: { include_market_data: includeMarketData }
    });
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail || 'Failed to get watchlist');
    }
    throw new Error('Network error while fetching watchlist');
  }
};

/**
 * Update a watchlist
 */
export const updateWatchlist = async (
  watchlistId: number, 
  updateData: WatchlistUpdateRequest
): Promise<Watchlist> => {
  try {
    const response = await apiClient.put(`/api/v1/watchlists/${watchlistId}`, updateData);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail || 'Failed to update watchlist');
    }
    throw new Error('Network error while updating watchlist');
  }
};

/**
 * Delete a watchlist
 */
export const deleteWatchlist = async (watchlistId: number): Promise<void> => {
  try {
    await apiClient.delete(`/api/v1/watchlists/${watchlistId}`);
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail || 'Failed to delete watchlist');
    }
    throw new Error('Network error while deleting watchlist');
  }
};

// ============================================================================
// WATCHLIST ITEM API FUNCTIONS
// ============================================================================

/**
 * Add a stock to a watchlist
 */
export const addStockToWatchlist = async (
  watchlistId: number, 
  itemData: WatchlistItemCreateRequest
): Promise<WatchlistItem> => {
  try {
    const response = await apiClient.post(`/api/v1/watchlists/${watchlistId}/items`, itemData);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail || 'Failed to add stock to watchlist');
    }
    throw new Error('Network error while adding stock to watchlist');
  }
};

/**
 * Add multiple stocks to a watchlist
 */
export const bulkAddStocksToWatchlist = async (
  watchlistId: number, 
  bulkData: WatchlistBulkAddRequest
): Promise<WatchlistBulkAddResponse> => {
  try {
    const response = await apiClient.post(`/api/v1/watchlists/${watchlistId}/items/bulk`, bulkData);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail || 'Failed to add stocks to watchlist');
    }
    throw new Error('Network error while adding stocks to watchlist');
  }
};

/**
 * Update a watchlist item
 */
export const updateWatchlistItem = async (
  watchlistId: number, 
  itemId: number, 
  updateData: WatchlistItemUpdateRequest
): Promise<WatchlistItem> => {
  try {
    const response = await apiClient.put(`/api/v1/watchlists/${watchlistId}/items/${itemId}`, updateData);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail || 'Failed to update watchlist item');
    }
    throw new Error('Network error while updating watchlist item');
  }
};

/**
 * Remove a stock from a watchlist
 */
export const removeStockFromWatchlist = async (watchlistId: number, itemId: number): Promise<void> => {
  try {
    await apiClient.delete(`/api/v1/watchlists/${watchlistId}/items/${itemId}`);
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail || 'Failed to remove stock from watchlist');
    }
    throw new Error('Network error while removing stock from watchlist');
  }
};

// ============================================================================
// UTILITY API FUNCTIONS
// ============================================================================

/**
 * Get watchlist statistics for the current user
 */
export const getWatchlistStats = async (): Promise<WatchlistStats> => {
  try {
    const response = await apiClient.get('/api/v1/watchlists/stats/summary');
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail || 'Failed to get watchlist stats');
    }
    throw new Error('Network error while fetching watchlist stats');
  }
};

/**
 * Ensure user has a default watchlist
 */
export const ensureDefaultWatchlist = async (): Promise<Watchlist> => {
  try {
    const response = await apiClient.post('/api/v1/watchlists/default');
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail || 'Failed to create default watchlist');
    }
    throw new Error('Network error while creating default watchlist');
  }
};

/**
 * Refresh market data for all stocks in a watchlist
 */
export const refreshWatchlistData = async (watchlistId: number): Promise<Watchlist> => {
  try {
    const response = await apiClient.get(`/api/v1/watchlists/${watchlistId}/refresh`);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail || 'Failed to refresh watchlist data');
    }
    throw new Error('Network error while refreshing watchlist data');
  }
};