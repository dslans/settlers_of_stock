import { useState, useCallback } from 'react';
import { 
  lookupStock, 
  validateSymbol, 
  getMarketData,
  StockLookupResponse,
  SymbolValidationResponse 
} from '../services/api';

interface UseStockLookupState {
  isLoading: boolean;
  error: string | null;
  stockData: StockLookupResponse | null;
  validationResult: SymbolValidationResponse | null;
}

interface UseStockLookupReturn extends UseStockLookupState {
  lookupStock: (symbol: string, useCache?: boolean) => Promise<StockLookupResponse | null>;
  validateSymbol: (symbol: string) => Promise<SymbolValidationResponse | null>;
  refreshMarketData: (symbol: string) => Promise<void>;
  clearData: () => void;
}

export const useStockLookup = (): UseStockLookupReturn => {
  const [state, setState] = useState<UseStockLookupState>({
    isLoading: false,
    error: null,
    stockData: null,
    validationResult: null,
  });

  const setLoading = useCallback((isLoading: boolean) => {
    setState(prev => ({ ...prev, isLoading }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error }));
  }, []);

  const setStockData = useCallback((stockData: StockLookupResponse | null) => {
    setState(prev => ({ ...prev, stockData }));
  }, []);

  const setValidationResult = useCallback((validationResult: SymbolValidationResponse | null) => {
    setState(prev => ({ ...prev, validationResult }));
  }, []);

  const handleLookupStock = useCallback(async (
    symbol: string, 
    useCache: boolean = true
  ): Promise<StockLookupResponse | null> => {
    if (!symbol.trim()) {
      setError('Please enter a stock symbol');
      return null;
    }

    setLoading(true);
    setError(null);
    setStockData(null);

    try {
      const data = await lookupStock(symbol.trim(), useCache);
      setStockData(data);
      return data;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to lookup stock';
      setError(errorMessage);
      
      // If it's an invalid symbol error, provide helpful suggestions
      if (errorMessage.toLowerCase().includes('not found') || 
          errorMessage.toLowerCase().includes('invalid')) {
        setError(`Stock symbol "${symbol.toUpperCase()}" not found. Please check the spelling or try a different symbol.`);
      }
      
      return null;
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError, setStockData]);

  const handleValidateSymbol = useCallback(async (
    symbol: string
  ): Promise<SymbolValidationResponse | null> => {
    if (!symbol.trim()) {
      setError('Please enter a stock symbol');
      return null;
    }

    setLoading(true);
    setError(null);
    setValidationResult(null);

    try {
      const result = await validateSymbol(symbol.trim());
      setValidationResult(result);
      return result;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to validate symbol';
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError, setValidationResult]);

  const handleRefreshMarketData = useCallback(async (symbol: string): Promise<void> => {
    if (!symbol.trim() || !state.stockData) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const marketData = await getMarketData(symbol.trim(), false); // Force fresh data
      
      // Update the existing stock data with fresh market data
      setStockData({
        ...state.stockData,
        market_data: marketData
      });
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to refresh market data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [state.stockData, setLoading, setError, setStockData]);

  const clearData = useCallback(() => {
    setState({
      isLoading: false,
      error: null,
      stockData: null,
      validationResult: null,
    });
  }, []);

  return {
    ...state,
    lookupStock: handleLookupStock,
    validateSymbol: handleValidateSymbol,
    refreshMarketData: handleRefreshMarketData,
    clearData,
  };
};