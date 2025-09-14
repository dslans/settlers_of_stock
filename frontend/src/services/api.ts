import axios from 'axios';
import { ApiResponse } from '@/types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      // Redirect to login or refresh token
    }
    return Promise.reject(error);
  }
);

export const healthCheck = async (): Promise<ApiResponse<{ status: string; service: string }>> => {
  const response = await apiClient.get('/health');
  return response.data;
};

// ============================================================================
// STOCK API FUNCTIONS
// ============================================================================

export interface StockLookupResponse {
  stock: {
    symbol: string;
    name: string;
    exchange: string;
    sector?: string;
    industry?: string;
    marketCap?: number;
    lastUpdated: string;
  };
  market_data: {
    symbol: string;
    price: number;
    change: number;
    changePercent: number;
    volume: number;
    high52Week?: number;
    low52Week?: number;
    avgVolume?: number;
    marketCap?: number;
    peRatio?: number;
    timestamp: string;
    isStale?: boolean;
  };
}

export interface SymbolValidationResponse {
  symbol: string;
  isValid: boolean;
  suggestions: string[];
}

export interface StockErrorResponse {
  error: boolean;
  message: string;
  errorType: string;
  suggestions: string[];
  timestamp: string;
}

/**
 * Look up comprehensive stock information including market data
 */
export const lookupStock = async (
  symbol: string, 
  useCache: boolean = true
): Promise<StockLookupResponse> => {
  try {
    const response = await apiClient.get(`/api/v1/stocks/lookup/${symbol.toUpperCase()}`, {
      params: { use_cache: useCache }
    });
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail.message || 'Failed to lookup stock');
    }
    throw new Error('Network error while looking up stock');
  }
};

/**
 * Get real-time market data for a stock symbol
 */
export const getMarketData = async (
  symbol: string, 
  useCache: boolean = true
): Promise<StockLookupResponse['market_data']> => {
  try {
    const response = await apiClient.get(`/api/v1/stocks/market-data/${symbol.toUpperCase()}`, {
      params: { use_cache: useCache }
    });
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail.message || 'Failed to get market data');
    }
    throw new Error('Network error while fetching market data');
  }
};

/**
 * Validate if a stock symbol exists and is tradeable
 */
export const validateSymbol = async (symbol: string): Promise<SymbolValidationResponse> => {
  try {
    const response = await apiClient.get(`/api/v1/stocks/validate/${symbol.toUpperCase()}`);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail.message || 'Failed to validate symbol');
    }
    throw new Error('Network error while validating symbol');
  }
};

/**
 * Get basic stock information (company name, sector, etc.)
 */
export const getStockInfo = async (
  symbol: string, 
  useCache: boolean = true
): Promise<StockLookupResponse['stock']> => {
  try {
    const response = await apiClient.get(`/api/v1/stocks/info/${symbol.toUpperCase()}`, {
      params: { use_cache: useCache }
    });
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail.message || 'Failed to get stock info');
    }
    throw new Error('Network error while fetching stock info');
  }
};

/**
 * Get market data for multiple symbols at once
 */
export const getBatchMarketData = async (
  symbols: string[], 
  useCache: boolean = true
): Promise<Record<string, StockLookupResponse['market_data']>> => {
  try {
    const response = await apiClient.post('/api/v1/stocks/batch/market-data', symbols, {
      params: { use_cache: useCache }
    });
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail.message || 'Failed to get batch market data');
    }
    throw new Error('Network error while fetching batch market data');
  }
};