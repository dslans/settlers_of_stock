import { renderHook, act } from '@testing-library/react';
import { useStockLookup } from '../useStockLookup';
import * as api from '../../services/api';

// Mock the API module
jest.mock('../../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

const mockStockData: api.StockLookupResponse = {
  stock: {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    exchange: 'NASDAQ',
    sector: 'Technology',
    industry: 'Consumer Electronics',
    marketCap: 3000000000000,
    lastUpdated: '2024-01-15T10:30:00Z'
  },
  market_data: {
    symbol: 'AAPL',
    price: 150.25,
    change: 2.50,
    changePercent: 1.69,
    volume: 75000000,
    high52Week: 180.00,
    low52Week: 120.00,
    avgVolume: 80000000,
    marketCap: 2500000000000,
    peRatio: 25.5,
    timestamp: '2024-01-15T15:30:00Z',
    isStale: false
  }
};

const mockValidationResponse: api.SymbolValidationResponse = {
  symbol: 'AAPL',
  isValid: true,
  suggestions: []
};

describe('useStockLookup', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('initializes with correct default state', () => {
    const { result } = renderHook(() => useStockLookup());

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.stockData).toBe(null);
    expect(result.current.validationResult).toBe(null);
  });

  it('handles successful stock lookup', async () => {
    mockedApi.lookupStock.mockResolvedValue(mockStockData);

    const { result } = renderHook(() => useStockLookup());

    let lookupResult: api.StockLookupResponse | null = null;

    await act(async () => {
      lookupResult = await result.current.lookupStock('AAPL');
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.stockData).toEqual(mockStockData);
    expect(lookupResult).toEqual(mockStockData);
    expect(mockedApi.lookupStock).toHaveBeenCalledWith('AAPL', true);
  });

  it('handles stock lookup error', async () => {
    const errorMessage = 'Stock symbol INVALID not found';
    mockedApi.lookupStock.mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useStockLookup());

    let lookupResult: api.StockLookupResponse | null = null;

    await act(async () => {
      lookupResult = await result.current.lookupStock('INVALID');
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toContain('INVALID');
    expect(result.current.stockData).toBe(null);
    expect(lookupResult).toBe(null);
  });

  it('handles empty symbol input', async () => {
    const { result } = renderHook(() => useStockLookup());

    let lookupResult: api.StockLookupResponse | null = null;

    await act(async () => {
      lookupResult = await result.current.lookupStock('   ');
    });

    expect(result.current.error).toBe('Please enter a stock symbol');
    expect(lookupResult).toBe(null);
    expect(mockedApi.lookupStock).not.toHaveBeenCalled();
  });

  it('handles successful symbol validation', async () => {
    mockedApi.validateSymbol.mockResolvedValue(mockValidationResponse);

    const { result } = renderHook(() => useStockLookup());

    let validationResult: api.SymbolValidationResponse | null = null;

    await act(async () => {
      validationResult = await result.current.validateSymbol('AAPL');
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.validationResult).toEqual(mockValidationResponse);
    expect(validationResult).toEqual(mockValidationResponse);
    expect(mockedApi.validateSymbol).toHaveBeenCalledWith('AAPL');
  });

  it('handles symbol validation error', async () => {
    const errorMessage = 'Failed to validate symbol';
    mockedApi.validateSymbol.mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useStockLookup());

    let validationResult: api.SymbolValidationResponse | null = null;

    await act(async () => {
      validationResult = await result.current.validateSymbol('INVALID');
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(errorMessage);
    expect(result.current.validationResult).toBe(null);
    expect(validationResult).toBe(null);
  });

  it('handles market data refresh', async () => {
    const refreshedMarketData = {
      ...mockStockData.market_data,
      price: 155.00,
      change: 7.25,
      changePercent: 4.92
    };

    mockedApi.getMarketData.mockResolvedValue(refreshedMarketData);

    const { result } = renderHook(() => useStockLookup());

    // Set initial stock data
    act(() => {
      result.current.clearData();
    });

    // Manually set stock data to simulate previous lookup
    await act(async () => {
      await result.current.lookupStock('AAPL');
    });

    // Mock the lookup first
    mockedApi.lookupStock.mockResolvedValue(mockStockData);
    
    await act(async () => {
      await result.current.lookupStock('AAPL');
    });

    // Now refresh market data
    await act(async () => {
      await result.current.refreshMarketData('AAPL');
    });

    expect(result.current.stockData?.market_data.price).toBe(155.00);
    expect(mockedApi.getMarketData).toHaveBeenCalledWith('AAPL', false);
  });

  it('handles refresh without existing stock data', async () => {
    const { result } = renderHook(() => useStockLookup());

    await act(async () => {
      await result.current.refreshMarketData('AAPL');
    });

    // Should not make API call if no existing stock data
    expect(mockedApi.getMarketData).not.toHaveBeenCalled();
  });

  it('clears data correctly', () => {
    const { result } = renderHook(() => useStockLookup());

    // Set some data first
    act(() => {
      // Simulate having some data
      result.current.clearData();
    });

    act(() => {
      result.current.clearData();
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.stockData).toBe(null);
    expect(result.current.validationResult).toBe(null);
  });

  it('trims whitespace from symbol input', async () => {
    mockedApi.lookupStock.mockResolvedValue(mockStockData);

    const { result } = renderHook(() => useStockLookup());

    await act(async () => {
      await result.current.lookupStock('  AAPL  ');
    });

    expect(mockedApi.lookupStock).toHaveBeenCalledWith('AAPL', true);
  });

  it('sets loading state correctly during operations', async () => {
    // Create a promise that we can control
    let resolvePromise: (value: api.StockLookupResponse) => void;
    const controlledPromise = new Promise<api.StockLookupResponse>((resolve) => {
      resolvePromise = resolve;
    });

    mockedApi.lookupStock.mockReturnValue(controlledPromise);

    const { result } = renderHook(() => useStockLookup());

    // Start the lookup
    act(() => {
      result.current.lookupStock('AAPL');
    });

    // Should be loading
    expect(result.current.isLoading).toBe(true);

    // Resolve the promise
    await act(async () => {
      resolvePromise!(mockStockData);
      await controlledPromise;
    });

    // Should no longer be loading
    expect(result.current.isLoading).toBe(false);
  });
});