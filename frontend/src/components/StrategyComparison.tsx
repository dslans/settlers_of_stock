import React, { useState } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import DisclaimerBanner from './DisclaimerBanner';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

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
}

interface StrategyComparisonData {
  symbol: string;
  start_date: string;
  end_date: string;
  strategies: Record<string, BacktestResult>;
  best_strategy: string;
  comparison_metrics: {
    avg_return: number;
    best_return: number;
    worst_return: number;
    avg_win_rate: number;
    avg_sharpe_ratio?: number;
    strategy_count: number;
  };
}

interface StrategyComparisonProps {
  data: StrategyComparisonData;
}

const StrategyComparison: React.FC<StrategyComparisonProps> = ({ data }) => {
  const [selectedMetric, setSelectedMetric] = useState<'total_return' | 'win_rate' | 'sharpe_ratio' | 'max_drawdown'>('total_return');

  const formatPercentage = (value: number) => `${value.toFixed(2)}%`;
  const formatDate = (dateString: string) => new Date(dateString).toLocaleDateString();

  const strategies = Object.values(data.strategies);
  const strategyNames = Object.keys(data.strategies);

  // Create chart data based on selected metric
  const createChartData = () => {
    const labels = strategyNames.map(name => name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()));
    
    let chartData: number[] = [];
    let label = '';
    let color = '';

    switch (selectedMetric) {
      case 'total_return':
        chartData = strategies.map(s => s.total_return);
        label = 'Total Return (%)';
        color = 'rgba(34, 197, 94, 0.8)';
        break;
      case 'win_rate':
        chartData = strategies.map(s => s.win_rate);
        label = 'Win Rate (%)';
        color = 'rgba(59, 130, 246, 0.8)';
        break;
      case 'sharpe_ratio':
        chartData = strategies.map(s => s.sharpe_ratio || 0);
        label = 'Sharpe Ratio';
        color = 'rgba(168, 85, 247, 0.8)';
        break;
      case 'max_drawdown':
        chartData = strategies.map(s => -s.max_drawdown); // Negative for better visualization
        label = 'Max Drawdown (%)';
        color = 'rgba(239, 68, 68, 0.8)';
        break;
    }

    return {
      labels,
      datasets: [
        {
          label,
          data: chartData,
          backgroundColor: color,
          borderColor: color.replace('0.8', '1'),
          borderWidth: 1,
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
        text: `Strategy Comparison - ${selectedMetric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}`,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value: any) {
            if (selectedMetric === 'sharpe_ratio') {
              return value.toFixed(2);
            }
            return value + '%';
          },
        },
      },
    },
  };

  const getRankColor = (rank: number) => {
    switch (rank) {
      case 1: return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 2: return 'bg-gray-100 text-gray-800 border-gray-200';
      case 3: return 'bg-orange-100 text-orange-800 border-orange-200';
      default: return 'bg-blue-50 text-blue-800 border-blue-200';
    }
  };

  // Rank strategies by total return
  const rankedStrategies = strategies
    .map((strategy, index) => ({ ...strategy, originalName: strategyNames[index] }))
    .sort((a, b) => b.total_return - a.total_return)
    .map((strategy, index) => ({ ...strategy, rank: index + 1 }));

  const chartData = createChartData();

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold text-gray-900">Strategy Comparison</h2>
        <p className="text-gray-600 mt-1">
          {data.symbol} • {formatDate(data.start_date)} - {formatDate(data.end_date)}
        </p>
        <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
          <span>Best Strategy: <strong className="text-green-600">{data.best_strategy.replace(/_/g, ' ')}</strong></span>
          <span>Strategies Compared: {data.comparison_metrics.strategy_count}</span>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <h3 className="text-sm font-medium text-green-700">Best Return</h3>
          <p className="text-2xl font-bold text-green-900">
            {formatPercentage(data.comparison_metrics.best_return)}
          </p>
        </div>
        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
          <h3 className="text-sm font-medium text-red-700">Worst Return</h3>
          <p className="text-2xl font-bold text-red-900">
            {formatPercentage(data.comparison_metrics.worst_return)}
          </p>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <h3 className="text-sm font-medium text-blue-700">Avg Win Rate</h3>
          <p className="text-2xl font-bold text-blue-900">
            {formatPercentage(data.comparison_metrics.avg_win_rate)}
          </p>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
          <h3 className="text-sm font-medium text-purple-700">Avg Sharpe</h3>
          <p className="text-2xl font-bold text-purple-900">
            {data.comparison_metrics.avg_sharpe_ratio?.toFixed(2) || 'N/A'}
          </p>
        </div>
      </div>

      {/* Chart Controls */}
      <div className="flex flex-wrap gap-2">
        <span className="text-sm font-medium text-gray-700 mr-2">Compare by:</span>
        {[
          { key: 'total_return', label: 'Total Return' },
          { key: 'win_rate', label: 'Win Rate' },
          { key: 'sharpe_ratio', label: 'Sharpe Ratio' },
          { key: 'max_drawdown', label: 'Max Drawdown' },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setSelectedMetric(key as any)}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              selectedMetric === key
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Comparison Chart */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <Bar data={chartData} options={chartOptions} />
      </div>

      {/* Detailed Strategy Rankings */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Strategy Rankings</h3>
        <div className="space-y-3">
          {rankedStrategies.map((strategy) => (
            <div
              key={strategy.backtest_id}
              className={`p-4 rounded-lg border-2 ${getRankColor(strategy.rank)}`}
            >
              <div className="flex justify-between items-start">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white border-2 border-current">
                    <span className="text-sm font-bold">#{strategy.rank}</span>
                  </div>
                  <div>
                    <h4 className="font-semibold">
                      {strategy.originalName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </h4>
                    <p className="text-sm opacity-75">
                      {strategy.total_trades} trades • {formatPercentage(strategy.win_rate)} win rate
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold">
                    {formatPercentage(strategy.total_return)}
                  </p>
                  <p className="text-sm opacity-75">
                    Total Return
                  </p>
                </div>
              </div>
              
              <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <span className="opacity-75">Annualized:</span>
                  <span className="ml-1 font-medium">{formatPercentage(strategy.annualized_return)}</span>
                </div>
                <div>
                  <span className="opacity-75">Max Drawdown:</span>
                  <span className="ml-1 font-medium">-{formatPercentage(strategy.max_drawdown)}</span>
                </div>
                <div>
                  <span className="opacity-75">Avg Hold:</span>
                  <span className="ml-1 font-medium">{strategy.avg_hold_days.toFixed(1)} days</span>
                </div>
                <div>
                  <span className="opacity-75">Sharpe:</span>
                  <span className="ml-1 font-medium">{strategy.sharpe_ratio?.toFixed(2) || 'N/A'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Insights */}
      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
        <h3 className="text-sm font-medium text-blue-900 mb-2">Key Insights</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>
            • The <strong>{data.best_strategy.replace(/_/g, ' ')}</strong> strategy performed best with{' '}
            {formatPercentage(data.comparison_metrics.best_return)} total return
          </li>
          <li>
            • Return spread: {formatPercentage(data.comparison_metrics.best_return - data.comparison_metrics.worst_return)}{' '}
            between best and worst performing strategies
          </li>
          <li>
            • Average win rate across all strategies: {formatPercentage(data.comparison_metrics.avg_win_rate)}
          </li>
          {data.comparison_metrics.avg_sharpe_ratio && (
            <li>
              • Average risk-adjusted return (Sharpe): {data.comparison_metrics.avg_sharpe_ratio.toFixed(2)}
            </li>
          )}
        </ul>
      </div>

      {/* Disclaimer */}
      <DisclaimerBanner
        context="backtest"
        compact={false}
      />
    </div>
  );
};

export default StrategyComparison;