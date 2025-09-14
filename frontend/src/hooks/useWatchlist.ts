import { useState, useEffect, useCallback } from 'react';
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
  LoadingState,
} from '../types';
import {
  getUserWatchlists,
  createWatchlist,
  getWatchlist,
  updateWatchlist,
  deleteWatchlist,
  addStockToWatchlist,
  bulkAddStocksToWatchlist,
  updateWatchlistItem,
  removeStockFromWatchlist,
  getWatchlistStats,
  ensureDefaultWatchlist,
  refreshWatchlistData,
} from '../services/watchlist';

// ============================================================================
// WATCHLIST MANAGEMENT HOOK
// ============================================================================

export interface UseWatchlistReturn {
  // State
  watchlists: WatchlistSummary[];
  currentWatchlist: Watchlist | null;
  stats: WatchlistStats | null;
  loading: LoadingState;
  error: string | null;
  
  // Actions
  loadWatchlists: (includeItems?: boolean) => Promise<void>;
  loadWatchlist: (id: number, includeMarketData?: boolean) => Promise<void>;
  createNewWatchlist: (data: WatchlistCreateRequest) => Promise<Watchlist>;
  updateExistingWatchlist: (id: number, data: WatchlistUpdateRequest) => Promise<Watchlist>;
  deleteExistingWatchlist: (id: number) => Promise<void>;
  addStock: (watchlistId: number, data: WatchlistItemCreateRequest) => Promise<WatchlistItem>;
  bulkAddStocks: (watchlistId: number, data: WatchlistBulkAddRequest) => Promise<WatchlistBulkAddResponse>;
  updateStock: (watchlistId: number, itemId: number, data: WatchlistItemUpdateRequest) => Promise<WatchlistItem>;
  removeStock: (watchlistId: number, itemId: number) => Promise<void>;
  loadStats: () => Promise<void>;
  ensureDefault: () => Promise<Watchlist>;
  refreshData: (watchlistId: number) => Promise<void>;
  clearError: () => void;
}

export const useWatchlist = (): UseWatchlistReturn => {
  const [watchlists, setWatchlists] = useState<WatchlistSummary[]>([]);
  const [currentWatchlist, setCurrentWatchlist] = useState<Watchlist | null>(null);
  const [stats, setStats] = useState<WatchlistStats | null>(null);
  const [loading, setLoading] = useState<LoadingState>({ isLoading: false });
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const handleError = useCallback((error: any, defaultMessage: string) => {
    const message = error instanceof Error ? error.message : defaultMessage;
    setError(message);
    console.error(defaultMessage, error);
  }, []);

  const loadWatchlists = useCallback(async (includeItems: boolean = false) => {
    try {
      setLoading({ isLoading: true, message: 'Loading watchlists...' });
      setError(null);
      
      const data = await getUserWatchlists(includeItems);
      setWatchlists(data as WatchlistSummary[]);
    } catch (error) {
      handleError(error, 'Failed to load watchlists');
    } finally {
      setLoading({ isLoading: false });
    }
  }, [handleError]);

  const loadWatchlist = useCallback(async (id: number, includeMarketData: boolean = true) => {
    try {
      setLoading({ isLoading: true, message: 'Loading watchlist...' });
      setError(null);
      
      const data = await getWatchlist(id, includeMarketData);
      setCurrentWatchlist(data);
    } catch (error) {
      handleError(error, 'Failed to load watchlist');
    } finally {
      setLoading({ isLoading: false });
    }
  }, [handleError]);

  const createNewWatchlist = useCallback(async (data: WatchlistCreateRequest): Promise<Watchlist> => {
    try {
      setLoading({ isLoading: true, message: 'Creating watchlist...' });
      setError(null);
      
      const newWatchlist = await createWatchlist(data);
      
      // Refresh watchlists list
      await loadWatchlists();
      
      return newWatchlist;
    } catch (error) {
      handleError(error, 'Failed to create watchlist');
      throw error;
    } finally {
      setLoading({ isLoading: false });
    }
  }, [handleError, loadWatchlists]);

  const updateExistingWatchlist = useCallback(async (id: number, data: WatchlistUpdateRequest): Promise<Watchlist> => {
    try {
      setLoading({ isLoading: true, message: 'Updating watchlist...' });
      setError(null);
      
      const updatedWatchlist = await updateWatchlist(id, data);
      
      // Update current watchlist if it's the one being updated
      if (currentWatchlist?.id === id) {
        setCurrentWatchlist(updatedWatchlist);
      }
      
      // Refresh watchlists list
      await loadWatchlists();
      
      return updatedWatchlist;
    } catch (error) {
      handleError(error, 'Failed to update watchlist');
      throw error;
    } finally {
      setLoading({ isLoading: false });
    }
  }, [handleError, loadWatchlists, currentWatchlist]);

  const deleteExistingWatchlist = useCallback(async (id: number): Promise<void> => {
    try {
      setLoading({ isLoading: true, message: 'Deleting watchlist...' });
      setError(null);
      
      await deleteWatchlist(id);
      
      // Clear current watchlist if it's the one being deleted
      if (currentWatchlist?.id === id) {
        setCurrentWatchlist(null);
      }
      
      // Refresh watchlists list
      await loadWatchlists();
    } catch (error) {
      handleError(error, 'Failed to delete watchlist');
      throw error;
    } finally {
      setLoading({ isLoading: false });
    }
  }, [handleError, loadWatchlists, currentWatchlist]);

  const addStock = useCallback(async (watchlistId: number, data: WatchlistItemCreateRequest): Promise<WatchlistItem> => {
    try {
      setLoading({ isLoading: true, message: 'Adding stock to watchlist...' });
      setError(null);
      
      const newItem = await addStockToWatchlist(watchlistId, data);
      
      // Refresh current watchlist if it's the one being updated
      if (currentWatchlist?.id === watchlistId) {
        await loadWatchlist(watchlistId);
      }
      
      return newItem;
    } catch (error) {
      handleError(error, 'Failed to add stock to watchlist');
      throw error;
    } finally {
      setLoading({ isLoading: false });
    }
  }, [handleError, loadWatchlist, currentWatchlist]);

  const bulkAddStocks = useCallback(async (watchlistId: number, data: WatchlistBulkAddRequest): Promise<WatchlistBulkAddResponse> => {
    try {
      setLoading({ isLoading: true, message: 'Adding stocks to watchlist...' });
      setError(null);
      
      const result = await bulkAddStocksToWatchlist(watchlistId, data);
      
      // Refresh current watchlist if it's the one being updated
      if (currentWatchlist?.id === watchlistId) {
        await loadWatchlist(watchlistId);
      }
      
      return result;
    } catch (error) {
      handleError(error, 'Failed to add stocks to watchlist');
      throw error;
    } finally {
      setLoading({ isLoading: false });
    }
  }, [handleError, loadWatchlist, currentWatchlist]);

  const updateStock = useCallback(async (watchlistId: number, itemId: number, data: WatchlistItemUpdateRequest): Promise<WatchlistItem> => {
    try {
      setLoading({ isLoading: true, message: 'Updating stock...' });
      setError(null);
      
      const updatedItem = await updateWatchlistItem(watchlistId, itemId, data);
      
      // Refresh current watchlist if it's the one being updated
      if (currentWatchlist?.id === watchlistId) {
        await loadWatchlist(watchlistId);
      }
      
      return updatedItem;
    } catch (error) {
      handleError(error, 'Failed to update stock');
      throw error;
    } finally {
      setLoading({ isLoading: false });
    }
  }, [handleError, loadWatchlist, currentWatchlist]);

  const removeStock = useCallback(async (watchlistId: number, itemId: number): Promise<void> => {
    try {
      setLoading({ isLoading: true, message: 'Removing stock from watchlist...' });
      setError(null);
      
      await removeStockFromWatchlist(watchlistId, itemId);
      
      // Refresh current watchlist if it's the one being updated
      if (currentWatchlist?.id === watchlistId) {
        await loadWatchlist(watchlistId);
      }
    } catch (error) {
      handleError(error, 'Failed to remove stock from watchlist');
      throw error;
    } finally {
      setLoading({ isLoading: false });
    }
  }, [handleError, loadWatchlist, currentWatchlist]);

  const loadStats = useCallback(async () => {
    try {
      setLoading({ isLoading: true, message: 'Loading statistics...' });
      setError(null);
      
      const data = await getWatchlistStats();
      setStats(data);
    } catch (error) {
      handleError(error, 'Failed to load watchlist statistics');
    } finally {
      setLoading({ isLoading: false });
    }
  }, [handleError]);

  const ensureDefault = useCallback(async (): Promise<Watchlist> => {
    try {
      setLoading({ isLoading: true, message: 'Creating default watchlist...' });
      setError(null);
      
      const defaultWatchlist = await ensureDefaultWatchlist();
      
      // Refresh watchlists list
      await loadWatchlists();
      
      return defaultWatchlist;
    } catch (error) {
      handleError(error, 'Failed to create default watchlist');
      throw error;
    } finally {
      setLoading({ isLoading: false });
    }
  }, [handleError, loadWatchlists]);

  const refreshData = useCallback(async (watchlistId: number): Promise<void> => {
    try {
      setLoading({ isLoading: true, message: 'Refreshing market data...' });
      setError(null);
      
      const refreshedWatchlist = await refreshWatchlistData(watchlistId);
      
      // Update current watchlist if it's the one being refreshed
      if (currentWatchlist?.id === watchlistId) {
        setCurrentWatchlist(refreshedWatchlist);
      }
    } catch (error) {
      handleError(error, 'Failed to refresh watchlist data');
    } finally {
      setLoading({ isLoading: false });
    }
  }, [handleError, currentWatchlist]);

  // Load watchlists on mount
  useEffect(() => {
    loadWatchlists();
  }, [loadWatchlists]);

  return {
    // State
    watchlists,
    currentWatchlist,
    stats,
    loading,
    error,
    
    // Actions
    loadWatchlists,
    loadWatchlist,
    createNewWatchlist,
    updateExistingWatchlist,
    deleteExistingWatchlist,
    addStock,
    bulkAddStocks,
    updateStock,
    removeStock,
    loadStats,
    ensureDefault,
    refreshData,
    clearError,
  };
};