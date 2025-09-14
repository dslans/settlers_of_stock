/**
 * Investment Opportunity Search Component
 * 
 * Provides a comprehensive interface for searching and filtering investment opportunities
 * with advanced filters, sorting options, and detailed results display.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  OpportunitySearchFilters,
  OpportunitySearchResult,
  InvestmentOpportunity,
  OpportunityType,
  RiskLevel,
  MarketCapCategory,
  OPPORTUNITY_TYPE_LABELS,
  RISK_LEVEL_LABELS,
  MARKET_CAP_LABELS
} from '@/types/opportunity';
import {
  searchOpportunities,
  quickSearchOpportunities,
  getFilterOptions,
  validateFilters,
  convertFiltersToBackendFormat,
  formatMarketCap,
  formatPercentage,
  getRiskLevelColorClass,
  getOpportunityTypeColorClass,
  getScoreColorClass
} from '@/services/opportunity';
import { OpportunityFilters } from './OpportunityFilters';
import { OpportunityCard } from './OpportunityCard';
import { LoadingSpinner } from './LoadingSpinner';

interface OpportunitySearchProps {
  onOpportunitySelect?: (opportunity: InvestmentOpportunity) => void;
  initialFilters?: Partial<OpportunitySearchFilters>;
  showFilters?: boolean;
  maxResults?: number;
}

export const OpportunitySearch: React.FC<OpportunitySearchProps> = ({
  onOpportunitySelect,
  initialFilters = {},
  showFilters = true,
  maxResults = 50
}) => {
  // State management
  const [filters, setFilters] = useState<OpportunitySearchFilters>({
    limit: maxResults,
    ...initialFilters
  });
  const [searchResult, setSearchResult] = useState<OpportunitySearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [sortBy, setSortBy] = useState<string>('overallScore');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Quick search state
  const [quickSearchLoading, setQuickSearchLoading] = useState(false);
  const [selectedQuickFilters, setSelectedQuickFilters] = useState<{
    opportunityTypes: OpportunityType[];
    maxRisk?: RiskLevel;
    marketCap: MarketCapCategory[];
    sectors: string[];
  }>({
    opportunityTypes: [],
    marketCap: [],
    sectors: []
  });

  /**
   * Perform opportunity search with current filters
   */
  const performSearch = useCallback(async () => {
    if (loading) return;

    setLoading(true);
    setError(null);

    try {
      const backendFilters = convertFiltersToBackendFormat(filters);
      const searchRequest = {
        filters: backendFilters,
        ranking: {
          sortBy: sortBy,
          sortOrder: sortOrder,
          fundamentalWeight: 0.4,
          technicalWeight: 0.3,
          momentumWeight: 0.2,
          valueWeight: 0.1
        },
        universe: 'popular'
      };

      const result = await searchOpportunities(searchRequest);
      setSearchResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search opportunities');
      setSearchResult(null);
    } finally {
      setLoading(false);
    }
  }, [filters, sortBy, sortOrder, loading]);

  /**
   * Perform quick search with simplified filters
   */
  const performQuickSearch = useCallback(async () => {
    if (quickSearchLoading) return;

    setQuickSearchLoading(true);
    setError(null);

    try {
      const result = await quickSearchOpportunities({
        opportunityTypes: selectedQuickFilters.opportunityTypes.length > 0 
          ? selectedQuickFilters.opportunityTypes 
          : undefined,
        maxRisk: selectedQuickFilters.maxRisk,
        marketCap: selectedQuickFilters.marketCap.length > 0 
          ? selectedQuickFilters.marketCap 
          : undefined,
        sectors: selectedQuickFilters.sectors.length > 0 
          ? selectedQuickFilters.sectors 
          : undefined,
        limit: 20
      });

      // Convert quick search result to full search result format
      const fullResult: OpportunitySearchResult = {
        opportunities: result.opportunities.map(opp => ({
          symbol: opp.symbol,
          name: opp.name,
          sector: opp.sector,
          industry: undefined,
          currentPrice: opp.currentPrice,
          marketCap: opp.marketCap,
          volume: 0,
          opportunityTypes: opp.opportunityTypes as OpportunityType[],
          riskLevel: opp.riskLevel as RiskLevel,
          scores: {
            overallScore: opp.score,
            fundamentalScore: undefined,
            technicalScore: undefined,
            momentumScore: undefined,
            valueScore: undefined,
            qualityScore: undefined
          },
          keyMetrics: {},
          reasons: [],
          risks: [],
          catalysts: [],
          lastUpdated: new Date().toISOString(),
          dataFreshness: {}
        })),
        totalFound: result.totalFound,
        filtersApplied: filters,
        searchTimestamp: new Date().toISOString(),
        executionTimeMs: result.searchTimeMs,
        stats: {}
      };

      setSearchResult(fullResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to perform quick search');
      setSearchResult(null);
    } finally {
      setQuickSearchLoading(false);
    }
  }, [selectedQuickFilters, quickSearchLoading, filters]);

  /**
   * Handle filter changes
   */
  const handleFilterChange = useCallback((newFilters: Partial<OpportunitySearchFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  /**
   * Handle quick filter changes
   */
  const handleQuickFilterChange = useCallback((
    type: keyof typeof selectedQuickFilters,
    value: any
  ) => {
    setSelectedQuickFilters(prev => ({
      ...prev,
      [type]: value
    }));
  }, []);

  /**
   * Clear all filters
   */
  const clearFilters = useCallback(() => {
    setFilters({ limit: maxResults });
    setSelectedQuickFilters({
      opportunityTypes: [],
      marketCap: [],
      sectors: []
    });
    setSearchResult(null);
  }, [maxResults]);

  /**
   * Handle opportunity selection
   */
  const handleOpportunityClick = useCallback((opportunity: InvestmentOpportunity) => {
    if (onOpportunitySelect) {
      onOpportunitySelect(opportunity);
    }
  }, [onOpportunitySelect]);

  // Auto-search when filters change (debounced)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (Object.keys(filters).length > 1) { // More than just limit
        performSearch();
      }
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [filters, performSearch]);

  return (
    <div className="opportunity-search">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Investment Opportunities
        </h2>
        <p className="text-gray-600">
          Discover stocks that match your investment criteria and strategy
        </p>
      </div>

      {/* Quick Search Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Search</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          {/* Opportunity Types */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Opportunity Types
            </label>
            <select
              multiple
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={selectedQuickFilters.opportunityTypes}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions, option => option.value as OpportunityType);
                handleQuickFilterChange('opportunityTypes', values);
              }}
            >
              {Object.entries(OPPORTUNITY_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* Risk Level */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Risk Level
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={selectedQuickFilters.maxRisk || ''}
              onChange={(e) => handleQuickFilterChange('maxRisk', e.target.value || undefined)}
            >
              <option value="">Any Risk Level</option>
              {Object.entries(RISK_LEVEL_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* Market Cap */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Market Cap
            </label>
            <select
              multiple
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={selectedQuickFilters.marketCap}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions, option => option.value as MarketCapCategory);
                handleQuickFilterChange('marketCap', values);
              }}
            >
              {Object.entries(MARKET_CAP_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* Sectors */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sectors
            </label>
            <select
              multiple
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={selectedQuickFilters.sectors}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions, option => option.value);
                handleQuickFilterChange('sectors', values);
              }}
            >
              <option value="Technology">Technology</option>
              <option value="Healthcare">Healthcare</option>
              <option value="Financial Services">Financial Services</option>
              <option value="Consumer Cyclical">Consumer Cyclical</option>
              <option value="Communication Services">Communication Services</option>
              <option value="Industrials">Industrials</option>
              <option value="Consumer Defensive">Consumer Defensive</option>
              <option value="Energy">Energy</option>
              <option value="Utilities">Utilities</option>
              <option value="Real Estate">Real Estate</option>
              <option value="Basic Materials">Basic Materials</option>
            </select>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={performQuickSearch}
            disabled={quickSearchLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {quickSearchLoading ? 'Searching...' : 'Quick Search'}
          </button>
          <button
            onClick={clearFilters}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="mb-6">
          <button
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
          >
            <span>{showAdvancedFilters ? 'Hide' : 'Show'} Advanced Filters</span>
            <svg
              className={`w-4 h-4 transform transition-transform ${showAdvancedFilters ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showAdvancedFilters && (
            <div className="mt-4">
              <OpportunityFilters
                filters={filters}
                onChange={handleFilterChange}
                onSearch={performSearch}
                loading={loading}
              />
            </div>
          )}
        </div>
      )}

      {/* Results Section */}
      {(loading || quickSearchLoading) && (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Search Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {searchResult && !loading && !quickSearchLoading && (
        <div>
          {/* Results Header */}
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Search Results
              </h3>
              <p className="text-sm text-gray-600">
                Found {searchResult.totalFound} opportunities
                {searchResult.executionTimeMs && (
                  <span> in {searchResult.executionTimeMs}ms</span>
                )}
              </p>
            </div>

            {/* Sort Controls */}
            <div className="flex gap-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="overallScore">Overall Score</option>
                <option value="marketCap">Market Cap</option>
                <option value="currentPrice">Price</option>
                <option value="volume">Volume</option>
              </select>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="desc">High to Low</option>
                <option value="asc">Low to High</option>
              </select>
            </div>
          </div>

          {/* Results Grid */}
          {searchResult.opportunities.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {searchResult.opportunities.map((opportunity) => (
                <OpportunityCard
                  key={opportunity.symbol}
                  opportunity={opportunity}
                  onClick={() => handleOpportunityClick(opportunity)}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.34 0-4.47-.881-6.08-2.33" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No opportunities found</h3>
              <p className="text-gray-600 mb-4">
                Try adjusting your search criteria or clearing some filters.
              </p>
              <button
                onClick={clearFilters}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Clear Filters
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default OpportunitySearch;