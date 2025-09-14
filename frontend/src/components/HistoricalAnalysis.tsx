import React, { useState } from 'react';
import BacktestForm from './BacktestForm';
import BacktestResults from './BacktestResults';
import StrategyComparison from './StrategyComparison';
import { historicalAnalysisService, BacktestResult, StrategyComparisonResult } from '../services/historical';

type ViewMode = 'backtest' | 'comparison' | 'history';

const HistoricalAnalysis: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('backtest');
  const [loading, setLoading] = useState(false);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [comparisonResult, setComparisonResult] = useState<StrategyComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleBacktestSubmit = async (formData: any) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await historicalAnalysisService.runBacktest(formData);
      setBacktestResult(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to run backtest');
      console.error('Backtest error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleComparisonSubmit = async (formData: any) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await historicalAnalysisService.compareStrategies(formData);
      setComparisonResult(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to compare strategies');
      console.error('Strategy comparison error:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderContent = () => {
    switch (viewMode) {
      case 'backtest':
        return (
          <div className="space-y-6">
            <BacktestForm onSubmit={handleBacktestSubmit} loading={loading} />
            {backtestResult && <BacktestResults result={backtestResult} showTrades={true} />}
          </div>
        );
      
      case 'comparison':
        return (
          <div className="space-y-6">
            <StrategyComparisonForm onSubmit={handleComparisonSubmit} loading={loading} />
            {comparisonResult && <StrategyComparison data={comparisonResult} />}
          </div>
        );
      
      case 'history':
        return <BacktestHistoryView />;
      
      default:
        return null;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Historical Analysis & Backtesting</h1>
        <p className="mt-2 text-gray-600">
          Test trading strategies against historical data and analyze performance metrics
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="-mb-px flex space-x-8">
          {[
            { key: 'backtest', label: 'Single Strategy Backtest', icon: '📊' },
            { key: 'comparison', label: 'Strategy Comparison', icon: '⚖️' },
            { key: 'history', label: 'Backtest History', icon: '📈' },
          ].map(({ key, label, icon }) => (
            <button
              key={key}
              onClick={() => {
                setViewMode(key as ViewMode);
                setError(null);
                setBacktestResult(null);
                setComparisonResult(null);
              }}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                viewMode === key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span>{icon}</span>
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {renderContent()}
    </div>
  );
};

// Strategy Comparison Form Component
interface StrategyComparisonFormProps {
  onSubmit: (data: any) => void;
  loading?: boolean;
}

const StrategyComparisonForm: React.FC<StrategyComparisonFormProps> = ({ onSubmit, loading = false }) => {
  const [formData, setFormData] = useState({
    symbol: '',
    start_date: '',
    end_date: '',
    strategies: [
      { type: 'recommendation_based', min_confidence: 60 },
      { type: 'recommendation_based', min_confidence: 80 },
    ]
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const getDefaultDates = () => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(endDate.getFullYear() - 1);
    
    return {
      start: startDate.toISOString().split('T')[0],
      end: endDate.toISOString().split('T')[0],
    };
  };

  const defaultDates = getDefaultDates();

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Compare Trading Strategies</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 mb-2">
              Stock Symbol *
            </label>
            <input
              type="text"
              id="symbol"
              value={formData.symbol}
              onChange={(e) => setFormData(prev => ({ ...prev, symbol: e.target.value }))}
              placeholder="e.g., AAPL"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
              maxLength={10}
            />
          </div>

          <div>
            <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 mb-2">
              Start Date *
            </label>
            <input
              type="date"
              id="start_date"
              value={formData.start_date || defaultDates.start}
              onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label htmlFor="end_date" className="block text-sm font-medium text-gray-700 mb-2">
              End Date *
            </label>
            <input
              type="date"
              id="end_date"
              value={formData.end_date || defaultDates.end}
              onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Strategies to Compare</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-white rounded border">
              <span>Recommendation Based (60% confidence)</span>
              <span className="text-sm text-gray-500">Conservative</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-white rounded border">
              <span>Recommendation Based (80% confidence)</span>
              <span className="text-sm text-gray-500">Aggressive</span>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className={`px-6 py-3 rounded-md font-medium text-white ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
            } transition-colors`}
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Comparing Strategies...
              </div>
            ) : (
              'Compare Strategies'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

// Backtest History View Component
const BacktestHistoryView: React.FC = () => {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    symbol: '',
    strategy_name: '',
  });

  React.useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await historicalAnalysisService.getBacktestHistory(filters);
      setHistory(data);
    } catch (error) {
      console.error('Error loading backtest history:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => new Date(dateString).toLocaleDateString();
  const formatPercentage = (value: number) => `${value.toFixed(2)}%`;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Backtest History</h2>
        <button
          onClick={loadHistory}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <input
          type="text"
          placeholder="Filter by symbol..."
          value={filters.symbol}
          onChange={(e) => setFilters(prev => ({ ...prev, symbol: e.target.value }))}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="text"
          placeholder="Filter by strategy..."
          value={filters.strategy_name}
          onChange={(e) => setFilters(prev => ({ ...prev, strategy_name: e.target.value }))}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* History Table */}
      {history.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Strategy
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Period
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trades
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Return
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {history.map((item) => (
                <tr key={item.backtest_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {item.symbol}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.strategy_name.replace(/_/g, ' ')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(item.start_date)} - {formatDate(item.end_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.trade_count}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                    item.total_return > 0 ? 'text-green-600' : item.total_return < 0 ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {formatPercentage(item.total_return)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(item.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No backtest history</h3>
            <p className="mt-1 text-sm text-gray-500">
              Run your first backtest to see results here.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default HistoricalAnalysis;