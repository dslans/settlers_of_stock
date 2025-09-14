import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import DisclaimerBanner from './DisclaimerBanner';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface Trade {
  entry_date: string;
  exit_date?: string;
  entry_price: number;
  exit_price?: number;
  return_pct?: number;
  hold_days?: number;
  trade_type: string;
  strategy_signal: string;
  confidence?: number;
}

interface BacktestResult {
  backtest_id: string;
  strategy_name: string;
  symbol: string;
  start_date: string;
  end_date: string;
  total_return: number;
  annualized_return: number;
  win_rate: number;
  avg_return_per_trade: number;
  max_drawdown: number;
  sharpe_ratio?: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  avg_hold_days: number;
  volatility: number;
  beta?: number;
  created_at: string;
  trades?: Trade[];
}

interface BacktestResultsProps {
  result: BacktestResult;
  showTrades?: boolean;
}

const BacktestResults: React.FC<BacktestResultsProps> = ({ result, showTrades = false }) => {
  const [showTradeDetails, setShowTradeDetails] = useState(showTrades);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getReturnColor = (returnPct: number) => {
    if (returnPct > 0) return 'text-green-600';
    if (returnPct < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getPerformanceRating = (totalReturn: number, winRate: number) => {
    if (totalReturn > 20 && winRate > 70) return { rating: 'Excellent', color: 'text-green-700 bg-green-100' };
    if (totalReturn > 10 && winRate > 60) return { rating: 'Good', color: 'text-green-600 bg-green-50' };
    if (totalReturn > 0 && winRate > 50) return { rating: 'Fair', color: 'text-yellow-600 bg-yellow-50' };
    if (totalReturn > -10) return { rating: 'Poor', color: 'text-orange-600 bg-orange-50' };
    return { rating: 'Very Poor', color: 'text-red-600 bg-red-50' };
  };

  // Create cumulative return chart data
  const createCumulativeReturnChart = () => {
    if (!result.trades || result.trades.length === 0) return null;

    const sortedTrades = [...result.trades]
      .filter(trade => trade.exit_date && trade.return_pct !== undefined)
      .sort((a, b) => new Date(a.exit_date!).getTime() - new Date(b.exit_date!).getTime());

    let cumulativeReturn = 0;
    const labels = ['Start'];
    const data = [0];

    sortedTrades.forEach(trade => {
      cumulativeReturn += trade.return_pct!;
      labels.push(formatDate(trade.exit_date!));
      data.push(cumulativeReturn);
    });

    return {
      labels,
      datasets: [
        {
          label: 'Cumulative Return (%)',
          data,
          borderColor: cumulativeReturn >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
          backgroundColor: cumulativeReturn >= 0 ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          tension: 0.1,
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Cumulative Return Over Time',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value: any) {
            return value + '%';
          },
        },
      },
    },
  };

  const performance = getPerformanceRating(result.total_return, result.win_rate);
  const chartData = createCumulativeReturnChart();

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Backtest Results: {result.symbol}
            </h2>
            <p className="text-gray-600 mt-1">
              Strategy: {result.strategy_name}
            </p>
            <p className="text-sm text-gray-500">
              {formatDate(result.start_date)} - {formatDate(result.end_date)}
            </p>
          </div>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${performance.color}`}>
            {performance.rating}
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500">Total Return</h3>
          <p className={`text-2xl font-bold ${getReturnColor(result.total_return)}`}>
            {formatPercentage(result.total_return)}
          </p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500">Annualized Return</h3>
          <p className={`text-2xl font-bold ${getReturnColor(result.annualized_return)}`}>
            {formatPercentage(result.annualized_return)}
          </p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500">Win Rate</h3>
          <p className="text-2xl font-bold text-blue-600">
            {formatPercentage(result.win_rate)}
          </p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500">Total Trades</h3>
          <p className="text-2xl font-bold text-gray-900">
            {result.total_trades}
          </p>
        </div>
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500">Avg Return/Trade</h3>
          <p className={`text-lg font-semibold ${getReturnColor(result.avg_return_per_trade)}`}>
            {formatPercentage(result.avg_return_per_trade)}
          </p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500">Max Drawdown</h3>
          <p className="text-lg font-semibold text-red-600">
            -{formatPercentage(result.max_drawdown)}
          </p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500">Avg Hold Days</h3>
          <p className="text-lg font-semibold text-gray-900">
            {result.avg_hold_days.toFixed(1)} days
          </p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500">Volatility</h3>
          <p className="text-lg font-semibold text-gray-900">
            {formatPercentage(result.volatility)}
          </p>
        </div>
        {result.sharpe_ratio && (
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500">Sharpe Ratio</h3>
            <p className="text-lg font-semibold text-gray-900">
              {result.sharpe_ratio.toFixed(2)}
            </p>
          </div>
        )}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500">Win/Loss</h3>
          <p className="text-lg font-semibold text-gray-900">
            {result.winning_trades}/{result.losing_trades}
          </p>
        </div>
      </div>

      {/* Cumulative Return Chart */}
      {chartData && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <Line data={chartData} options={chartOptions} />
        </div>
      )}

      {/* Trade Details */}
      {result.trades && result.trades.length > 0 && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Trade Details</h3>
            <button
              onClick={() => setShowTradeDetails(!showTradeDetails)}
              className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors"
            >
              {showTradeDetails ? 'Hide Trades' : 'Show Trades'}
            </button>
          </div>

          {showTradeDetails && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Entry Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Exit Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Entry Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Exit Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Return
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Hold Days
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Signal
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {result.trades.map((trade, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(trade.entry_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.exit_date ? formatDate(trade.exit_date) : 'Open'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatCurrency(trade.entry_price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.exit_price ? formatCurrency(trade.exit_price) : '-'}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                        trade.return_pct ? getReturnColor(trade.return_pct) : 'text-gray-500'
                      }`}>
                        {trade.return_pct ? formatPercentage(trade.return_pct) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {trade.hold_days || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          trade.trade_type === 'BUY' 
                            ? 'bg-green-100 text-green-800' 
                            : trade.trade_type === 'SELL'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {trade.strategy_signal}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="text-xs text-gray-500 border-t pt-4">
        <p>Backtest ID: {result.backtest_id}</p>
        <p>Created: {formatDate(result.created_at)}</p>
        <DisclaimerBanner
          context="backtest"
          compact={false}
        />
      </div>
    </div>
  );
};

export default BacktestResults;