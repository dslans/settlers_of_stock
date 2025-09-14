/**
 * Investment Opportunity Search API service.
 * Provides functions for searching, filtering, and analyzing investment opportunities.
 */

import { apiClient } from './api';
import {
  OpportunitySearchRequest,
  OpportunitySearchResult,
  InvestmentOpportunity,
  QuickSearchResponse,
  OpportunityFilterOptions,
  OpportunityFilterValidation,
  OpportunitySearchFilters,
  OpportunityType,
  RiskLevel,
  MarketCapCategory,
  OpportunityErrorResponse
} from '@/types/opportunity';

/**
 * Search for investment opportunities based on specified filters and ranking criteria
 */
export const searchOpportunities = async (
  request: OpportunitySearchRequest
): Promise<OpportunitySearchResult> => {
  try {
    const response = await apiClient.post('/api/v1/opportunities/search', request);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      const errorDetail = error.response.data.detail as OpportunityErrorResponse;
      throw new Error(errorDetail.message || 'Failed to search opportunities');
    }
    throw new Error('Network error while searching opportunities');
  }
};

/**
 * Quick opportunity search with simplified parameters
 */
export const quickSearchOpportunities = async (params: {
  opportunityTypes?: OpportunityType[];
  maxRisk?: RiskLevel;
  marketCap?: MarketCapCategory[];
  sectors?: string[];
  limit?: number;
}): Promise<QuickSearchResponse> => {
  try {
    const searchParams = new URLSearchParams();
    
    if (params.opportunityTypes) {
      params.opportunityTypes.forEach(type => 
        searchParams.append('opportunity_types', type)
      );
    }
    
    if (params.maxRisk) {
      searchParams.append('max_risk', params.maxRisk);
    }
    
    if (params.marketCap) {
      params.marketCap.forEach(cap => 
        searchParams.append('market_cap', cap)
      );
    }
    
    if (params.sectors) {
      params.sectors.forEach(sector => 
        searchParams.append('sectors', sector)
      );
    }
    
    if (params.limit) {
      searchParams.append('limit', params.limit.toString());
    }
    
    const response = await apiClient.get(`/api/v1/opportunities/quick-search?${searchParams}`);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      const errorDetail = error.response.data.detail as OpportunityErrorResponse;
      throw new Error(errorDetail.message || 'Failed to perform quick search');
    }
    throw new Error('Network error during quick search');
  }
};

/**
 * Get detailed opportunity analysis for a specific stock symbol
 */
export const getOpportunityDetails = async (symbol: string): Promise<InvestmentOpportunity> => {
  try {
    const response = await apiClient.get(`/api/v1/opportunities/details/${symbol.toUpperCase()}`);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      const errorDetail = error.response.data.detail as OpportunityErrorResponse;
      throw new Error(errorDetail.message || 'Failed to get opportunity details');
    }
    throw new Error('Network error while fetching opportunity details');
  }
};

/**
 * Find top investment opportunities within a specific sector
 */
export const getSectorOpportunities = async (
  sector: string,
  limit: number = 10,
  minMarketCap?: number
): Promise<InvestmentOpportunity[]> => {
  try {
    const params: any = { limit };
    if (minMarketCap) {
      params.min_market_cap = minMarketCap;
    }
    
    const response = await apiClient.get(`/api/v1/opportunities/sector/${encodeURIComponent(sector)}`, {
      params
    });
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      const errorDetail = error.response.data.detail as OpportunityErrorResponse;
      throw new Error(errorDetail.message || 'Failed to get sector opportunities');
    }
    throw new Error('Network error while fetching sector opportunities');
  }
};

/**
 * Find trending investment opportunities based on recent price momentum
 */
export const getTrendingOpportunities = async (
  timeframe: '1d' | '1w' | '1m' = '1d',
  limit: number = 20
): Promise<InvestmentOpportunity[]> => {
  try {
    const response = await apiClient.get('/api/v1/opportunities/trending', {
      params: { timeframe, limit }
    });
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      const errorDetail = error.response.data.detail as OpportunityErrorResponse;
      throw new Error(errorDetail.message || 'Failed to get trending opportunities');
    }
    throw new Error('Network error while fetching trending opportunities');
  }
};

/**
 * Get available filter options for opportunity search
 */
export const getFilterOptions = async (): Promise<OpportunityFilterOptions> => {
  try {
    const response = await apiClient.get('/api/v1/opportunities/filters/options');
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      const errorDetail = error.response.data.detail as OpportunityErrorResponse;
      throw new Error(errorDetail.message || 'Failed to get filter options');
    }
    throw new Error('Network error while fetching filter options');
  }
};

/**
 * Validate opportunity search filters without performing the search
 */
export const validateFilters = async (
  filters: OpportunitySearchFilters
): Promise<OpportunityFilterValidation> => {
  try {
    const response = await apiClient.post('/api/v1/opportunities/filters/validate', filters);
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.detail) {
      const errorDetail = error.response.data.detail as OpportunityErrorResponse;
      throw new Error(errorDetail.message || 'Failed to validate filters');
    }
    throw new Error('Network error while validating filters');
  }
};

/**
 * Helper function to convert frontend filter format to backend format
 */
export const convertFiltersToBackendFormat = (filters: OpportunitySearchFilters): any => {
  return {
    market_cap_min: filters.marketCapMin,
    market_cap_max: filters.marketCapMax,
    market_cap_categories: filters.marketCapCategories,
    sectors: filters.sectors,
    industries: filters.industries,
    exclude_sectors: filters.excludeSectors,
    price_change_1d_min: filters.priceChange1dMin,
    price_change_1d_max: filters.priceChange1dMax,
    price_change_1w_min: filters.priceChange1wMin,
    price_change_1w_max: filters.priceChange1wMax,
    price_change_1m_min: filters.priceChange1mMin,
    price_change_1m_max: filters.priceChange1mMax,
    volume_min: filters.volumeMin,
    avg_volume_min: filters.avgVolumeMin,
    pe_ratio_min: filters.peRatioMin,
    pe_ratio_max: filters.peRatioMax,
    pb_ratio_min: filters.pbRatioMin,
    pb_ratio_max: filters.pbRatioMax,
    roe_min: filters.roeMin,
    debt_to_equity_max: filters.debtToEquityMax,
    profit_margin_min: filters.profitMarginMin,
    revenue_growth_min: filters.revenueGrowthMin,
    rsi_min: filters.rsiMin,
    rsi_max: filters.rsiMax,
    price_above_sma_20: filters.priceAboveSma20,
    price_above_sma_50: filters.priceAboveSma50,
    opportunity_types: filters.opportunityTypes,
    max_risk_level: filters.maxRiskLevel,
    limit: filters.limit,
    min_score: filters.minScore
  };
};

/**
 * Helper function to format market cap for display
 */
export const formatMarketCap = (marketCap: number): string => {
  if (marketCap >= 1e12) {
    return `$${(marketCap / 1e12).toFixed(2)}T`;
  } else if (marketCap >= 1e9) {
    return `$${(marketCap / 1e9).toFixed(2)}B`;
  } else if (marketCap >= 1e6) {
    return `$${(marketCap / 1e6).toFixed(2)}M`;
  } else {
    return `$${marketCap.toLocaleString()}`;
  }
};

/**
 * Helper function to format percentage values
 */
export const formatPercentage = (value: number, decimals: number = 2): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

/**
 * Helper function to get risk level color class
 */
export const getRiskLevelColorClass = (riskLevel: RiskLevel): string => {
  const colorMap: Record<RiskLevel, string> = {
    low: 'text-green-600 bg-green-100',
    moderate: 'text-yellow-600 bg-yellow-100',
    high: 'text-red-600 bg-red-100',
    very_high: 'text-red-800 bg-red-200'
  };
  return colorMap[riskLevel] || 'text-gray-600 bg-gray-100';
};

/**
 * Helper function to get opportunity type color class
 */
export const getOpportunityTypeColorClass = (opportunityType: OpportunityType): string => {
  const colorMap: Record<OpportunityType, string> = {
    undervalued: 'text-blue-600 bg-blue-100',
    growth: 'text-green-600 bg-green-100',
    momentum: 'text-purple-600 bg-purple-100',
    dividend: 'text-orange-600 bg-orange-100',
    breakout: 'text-red-600 bg-red-100',
    oversold: 'text-cyan-600 bg-cyan-100',
    earnings_surprise: 'text-pink-600 bg-pink-100'
  };
  return colorMap[opportunityType] || 'text-gray-600 bg-gray-100';
};

/**
 * Helper function to calculate score color class
 */
export const getScoreColorClass = (score: number): string => {
  if (score >= 80) return 'text-green-600 bg-green-100';
  if (score >= 60) return 'text-yellow-600 bg-yellow-100';
  if (score >= 40) return 'text-orange-600 bg-orange-100';
  return 'text-red-600 bg-red-100';
};