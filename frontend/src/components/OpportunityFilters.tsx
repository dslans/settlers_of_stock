/**
 * Investment Opportunity Filters Component
 * 
 * Provides advanced filtering options for investment opportunity search.
 */

import React, { useState, useEffect } from 'react';
import {
  OpportunitySearchFilters,
  OpportunityType,
  RiskLevel,
  MarketCapCategory,
  OPPORTUNITY_TYPE_LABELS,
  RISK_LEVEL_LABELS,
  MARKET_CAP_LABELS
} from '@/types/opportunity';

interface OpportunityFiltersProps {
  filters: OpportunitySearchFilters;
  onChange: (filters: Partial<OpportunitySearchFilters>) => void;
  onSearch: () => void;
  loading?: boolean;
}

export const OpportunityFilters: React.FC<OpportunityFiltersProps> = ({
  filters,
  onChange,
  onSearch,
  loading = false
}) => {
  const [localFilters, setLocalFilters] = useState<OpportunitySearchFilters>(filters);

  // Update local filters when props change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleInputChange = (field: keyof OpportunitySearchFilters, value: any) => {
    const newFilters = { ...localFilters, [field]: value };
    setLocalFilters(newFilters);
    onChange({ [field]: value });
  };

  const handleMultiSelectChange = (field: keyof OpportunitySearchFilters, value: string, checked: boolean) => {
    const currentValues = (localFilters[field] as string[]) || [];
    const newValues = checked
      ? [...currentValues, value]
      : currentValues.filter(v => v !== value);
    
    handleInputChange(field, newValues.length > 0 ? newValues : undefined);
  };

  const clearFilters = () => {
    const clearedFilters: OpportunitySearchFilters = { limit: filters.limit || 50 };
    setLocalFilters(clearedFilters);
    onChange(clearedFilters);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Advanced Filters</h3>
        <button
          onClick={clearFilters}
          className="text-sm text-gray-600 hover:text-gray-800"
        >
          Clear All Filters
        </button>
      </div>

      <div className="space-y-6">
        {/* Market Cap Section */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Market Capitalization</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-700 mb-1">Minimum ($)</label>
              <input
                type="number"
                placeholder="e.g., 1000000000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.marketCapMin || ''}
                onChange={(e) => handleInputChange('marketCapMin', e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">Maximum ($)</label>
              <input
                type="number"
                placeholder="e.g., 100000000000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.marketCapMax || ''}
                onChange={(e) => handleInputChange('marketCapMax', e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </div>
          </div>
          <div className="mt-3">
            <label className="block text-sm text-gray-700 mb-2">Categories</label>
            <div className="flex flex-wrap gap-2">
              {Object.entries(MARKET_CAP_LABELS).map(([value, label]) => (
                <label key={value} className="flex items-center">
                  <input
                    type="checkbox"
                    className="mr-2"
                    checked={(localFilters.marketCapCategories || []).includes(value as MarketCapCategory)}
                    onChange={(e) => handleMultiSelectChange('marketCapCategories', value, e.target.checked)}
                  />
                  <span className="text-sm text-gray-700">{label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Sectors Section */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Sectors</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {[
              'Technology', 'Healthcare', 'Financial Services', 'Consumer Cyclical',
              'Communication Services', 'Industrials', 'Consumer Defensive',
              'Energy', 'Utilities', 'Real Estate', 'Basic Materials'
            ].map((sector) => (
              <label key={sector} className="flex items-center">
                <input
                  type="checkbox"
                  className="mr-2"
                  checked={(localFilters.sectors || []).includes(sector)}
                  onChange={(e) => handleMultiSelectChange('sectors', sector, e.target.checked)}
                />
                <span className="text-sm text-gray-700">{sector}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Fundamental Metrics Section */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Fundamental Metrics</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-700 mb-1">P/E Ratio Max</label>
              <input
                type="number"
                step="0.1"
                placeholder="e.g., 25"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.peRatioMax || ''}
                onChange={(e) => handleInputChange('peRatioMax', e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">P/B Ratio Max</label>
              <input
                type="number"
                step="0.1"
                placeholder="e.g., 3"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.pbRatioMax || ''}
                onChange={(e) => handleInputChange('pbRatioMax', e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">ROE Min (%)</label>
              <input
                type="number"
                step="0.01"
                placeholder="e.g., 0.15"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.roeMin || ''}
                onChange={(e) => handleInputChange('roeMin', e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">Debt/Equity Max</label>
              <input
                type="number"
                step="0.1"
                placeholder="e.g., 0.5"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.debtToEquityMax || ''}
                onChange={(e) => handleInputChange('debtToEquityMax', e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">Profit Margin Min (%)</label>
              <input
                type="number"
                step="0.01"
                placeholder="e.g., 0.1"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.profitMarginMin || ''}
                onChange={(e) => handleInputChange('profitMarginMin', e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">Revenue Growth Min (%)</label>
              <input
                type="number"
                step="0.01"
                placeholder="e.g., 0.05"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.revenueGrowthMin || ''}
                onChange={(e) => handleInputChange('revenueGrowthMin', e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>
          </div>
        </div>

        {/* Technical Indicators Section */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Technical Indicators</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-gray-700 mb-1">RSI Min</label>
              <input
                type="number"
                min="0"
                max="100"
                placeholder="e.g., 30"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.rsiMin || ''}
                onChange={(e) => handleInputChange('rsiMin', e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">RSI Max</label>
              <input
                type="number"
                min="0"
                max="100"
                placeholder="e.g., 70"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.rsiMax || ''}
                onChange={(e) => handleInputChange('rsiMax', e.target.value ? parseFloat(e.target.value) : undefined)}
              />
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="mr-2"
                  checked={localFilters.priceAboveSma20 || false}
                  onChange={(e) => handleInputChange('priceAboveSma20', e.target.checked || undefined)}
                />
                <span className="text-sm text-gray-700">Price above 20-day SMA</span>
              </label>
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="mr-2"
                  checked={localFilters.priceAboveSma50 || false}
                  onChange={(e) => handleInputChange('priceAboveSma50', e.target.checked || undefined)}
                />
                <span className="text-sm text-gray-700">Price above 50-day SMA</span>
              </label>
            </div>
          </div>
        </div>

        {/* Volume Section */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Volume</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-700 mb-1">Minimum Daily Volume</label>
              <input
                type="number"
                placeholder="e.g., 1000000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.volumeMin || ''}
                onChange={(e) => handleInputChange('volumeMin', e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">Minimum Average Volume</label>
              <input
                type="number"
                placeholder="e.g., 5000000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.avgVolumeMin || ''}
                onChange={(e) => handleInputChange('avgVolumeMin', e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </div>
          </div>
        </div>

        {/* Opportunity Types Section */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Opportunity Types</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(OPPORTUNITY_TYPE_LABELS).map(([value, label]) => (
              <label key={value} className="flex items-center">
                <input
                  type="checkbox"
                  className="mr-2"
                  checked={(localFilters.opportunityTypes || []).includes(value as OpportunityType)}
                  onChange={(e) => handleMultiSelectChange('opportunityTypes', value, e.target.checked)}
                />
                <span className="text-sm text-gray-700">{label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Risk Level Section */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Maximum Risk Level</h4>
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={localFilters.maxRiskLevel || ''}
            onChange={(e) => handleInputChange('maxRiskLevel', e.target.value || undefined)}
          >
            <option value="">Any Risk Level</option>
            {Object.entries(RISK_LEVEL_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Results Section */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Results</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-700 mb-1">Maximum Results</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.limit || 50}
                onChange={(e) => handleInputChange('limit', parseInt(e.target.value))}
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={200}>200</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-1">Minimum Score</label>
              <input
                type="number"
                min="0"
                max="100"
                placeholder="e.g., 70"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localFilters.minScore || ''}
                onChange={(e) => handleInputChange('minScore', e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 mt-6 pt-6 border-t border-gray-200">
        <button
          onClick={onSearch}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Search Opportunities'}
        </button>
        <button
          onClick={clearFilters}
          className="px-6 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
        >
          Clear Filters
        </button>
      </div>
    </div>
  );
};

export default OpportunityFilters;