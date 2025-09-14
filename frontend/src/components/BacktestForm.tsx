import React, { useState } from 'react';

interface BacktestFormData {
  symbol: string;
  start_date: string;
  end_date: string;
  strategy_type: 'recommendation_based' | 'technical_signals' | 'fundamental_signals' | 'combined_signals';
  min_confidence?: number;
  position_size?: number;
  strategy_params?: Record<string, any>;
}

interface BacktestFormProps {
  onSubmit: (data: BacktestFormData) => void;
  loading?: boolean;
}

const BacktestForm: React.FC<BacktestFormProps> = ({ onSubmit, loading = false }) => {
  const [formData, setFormData] = useState<BacktestFormData>({
    symbol: '',
    start_date: '',
    end_date: '',
    strategy_type: 'recommendation_based',
    min_confidence: 60,
    position_size: 10000,
  });

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [technicalParams, setTechnicalParams] = useState({
    name: 'sma_crossover',
    sma_short_period: 20,
    sma_long_period: 50,
    rsi_period: 14,
    rsi_oversold: 30,
    rsi_overbought: 70,
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'min_confidence' || name === 'position_size' ? Number(value) : value,
    }));
  };

  const handleTechnicalParamChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setTechnicalParams(prev => ({
      ...prev,
      [name]: name === 'name' ? value : Number(value),
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const submitData = { ...formData };
    
    // Add technical parameters if technical strategy is selected
    if (formData.strategy_type === 'technical_signals') {
      submitData.strategy_params = technicalParams;
    }
    
    onSubmit(submitData);
  };

  const getDefaultDates = () => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(endDate.getFullYear() - 1); // 1 year ago
    
    return {
      start: startDate.toISOString().split('T')[0],
      end: endDate.toISOString().split('T')[0],
    };
  };

  const defaultDates = getDefaultDates();

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Run Backtest</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Parameters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 mb-2">
              Stock Symbol *
            </label>
            <input
              type="text"
              id="symbol"
              name="symbol"
              value={formData.symbol}
              onChange={handleInputChange}
              placeholder="e.g., AAPL"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
              maxLength={10}
            />
          </div>

          <div>
            <label htmlFor="strategy_type" className="block text-sm font-medium text-gray-700 mb-2">
              Strategy Type *
            </label>
            <select
              id="strategy_type"
              name="strategy_type"
              value={formData.strategy_type}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="recommendation_based">Recommendation Based</option>
              <option value="technical_signals">Technical Signals</option>
              <option value="fundamental_signals">Fundamental Signals</option>
              <option value="combined_signals">Combined Signals</option>
            </select>
          </div>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 mb-2">
              Start Date *
            </label>
            <input
              type="date"
              id="start_date"
              name="start_date"
              value={formData.start_date || defaultDates.start}
              onChange={handleInputChange}
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
              name="end_date"
              value={formData.end_date || defaultDates.end}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
        </div>

        {/* Strategy-specific Parameters */}
        {formData.strategy_type === 'recommendation_based' && (
          <div>
            <label htmlFor="min_confidence" className="block text-sm font-medium text-gray-700 mb-2">
              Minimum Confidence Level (%)
            </label>
            <input
              type="number"
              id="min_confidence"
              name="min_confidence"
              value={formData.min_confidence}
              onChange={handleInputChange}
              min="0"
              max="100"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="text-sm text-gray-500 mt-1">
              Only consider recommendations with confidence above this threshold
            </p>
          </div>
        )}

        {formData.strategy_type === 'technical_signals' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Technical Strategy Parameters</h3>
            
            <div>
              <label htmlFor="technical_strategy" className="block text-sm font-medium text-gray-700 mb-2">
                Technical Strategy
              </label>
              <select
                id="technical_strategy"
                name="name"
                value={technicalParams.name}
                onChange={handleTechnicalParamChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="sma_crossover">SMA Crossover</option>
                <option value="rsi_strategy">RSI Strategy</option>
                <option value="macd_strategy">MACD Strategy</option>
              </select>
            </div>

            {technicalParams.name === 'sma_crossover' && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="sma_short_period" className="block text-sm font-medium text-gray-700 mb-2">
                    Short SMA Period
                  </label>
                  <input
                    type="number"
                    id="sma_short_period"
                    name="sma_short_period"
                    value={technicalParams.sma_short_period}
                    onChange={handleTechnicalParamChange}
                    min="5"
                    max="100"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="sma_long_period" className="block text-sm font-medium text-gray-700 mb-2">
                    Long SMA Period
                  </label>
                  <input
                    type="number"
                    id="sma_long_period"
                    name="sma_long_period"
                    value={technicalParams.sma_long_period}
                    onChange={handleTechnicalParamChange}
                    min="10"
                    max="200"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            )}

            {technicalParams.name === 'rsi_strategy' && (
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label htmlFor="rsi_period" className="block text-sm font-medium text-gray-700 mb-2">
                    RSI Period
                  </label>
                  <input
                    type="number"
                    id="rsi_period"
                    name="rsi_period"
                    value={technicalParams.rsi_period}
                    onChange={handleTechnicalParamChange}
                    min="5"
                    max="50"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="rsi_oversold" className="block text-sm font-medium text-gray-700 mb-2">
                    Oversold Level
                  </label>
                  <input
                    type="number"
                    id="rsi_oversold"
                    name="rsi_oversold"
                    value={technicalParams.rsi_oversold}
                    onChange={handleTechnicalParamChange}
                    min="10"
                    max="40"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="rsi_overbought" className="block text-sm font-medium text-gray-700 mb-2">
                    Overbought Level
                  </label>
                  <input
                    type="number"
                    id="rsi_overbought"
                    name="rsi_overbought"
                    value={technicalParams.rsi_overbought}
                    onChange={handleTechnicalParamChange}
                    min="60"
                    max="90"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Advanced Options */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm font-medium text-blue-600 hover:text-blue-500"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced Options
          </button>
        </div>

        {showAdvanced && (
          <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label htmlFor="position_size" className="block text-sm font-medium text-gray-700 mb-2">
                Position Size ($)
              </label>
              <input
                type="number"
                id="position_size"
                name="position_size"
                value={formData.position_size}
                onChange={handleInputChange}
                min="1000"
                max="1000000"
                step="1000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-sm text-gray-500 mt-1">
                Amount to invest in each trade
              </p>
            </div>
          </div>
        )}

        {/* Submit Button */}
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
                Running Backtest...
              </div>
            ) : (
              'Run Backtest'
            )}
          </button>
        </div>
      </form>

      {/* Information Box */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h3 className="text-sm font-medium text-blue-900 mb-2">About Backtesting</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Backtesting simulates how a strategy would have performed historically</li>
          <li>• Results are based on historical data and may not predict future performance</li>
          <li>• Transaction costs and slippage are included in calculations</li>
          <li>• Minimum date range is 30 days for meaningful results</li>
        </ul>
      </div>
    </div>
  );
};

export default BacktestForm;