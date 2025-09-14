import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export interface BacktestRequest {
  symbol: string;
  start_date: string;
  end_date: string;
  strategy_type: 'recommendation_based' | 'technical_signals' | 'fundamental_signals' | 'combined_signals';
  min_confidence?: number;
  position_size?: number;
  strategy_params?: Record<string, any>;
}

export interface Trade {
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

export interface BacktestResult {
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

export interface StrategyComparisonRequest {
  symbol: string;
  start_date: string;
  end_date: string;
  strategies: Array<{
    type: string;
    min_confidence?: number;
    position_size?: number;
    params?: Record<string, any>;
  }>;
}

export interface StrategyComparisonResult {
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

export interface AnalysisHistory {
  symbol: string;
  analysis_date: string;
  recommendation: string;
  confidence: number;
  overall_score: number;
  fundamental_score?: number;
  technical_score?: number;
  price_at_analysis: number;
  target_price_3m?: number;
  target_price_1y?: number;
  risk_level: string;
  strengths: string[];
  weaknesses: string[];
  risks: string[];
}

export interface BacktestSummary {
  backtest_id: string;
  strategy_name: string;
  symbol: string;
  start_date: string;
  end_date: string;
  created_at: string;
  trade_count: number;
  total_return: number;
}

class HistoricalAnalysisService {
  private getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async runBacktest(request: BacktestRequest): Promise<BacktestResult> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/historical/backtest`,
        request,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error running backtest:', error);
      throw error;
    }
  }

  async getBacktestDetails(backtestId: string): Promise<BacktestResult> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/historical/backtest/${backtestId}`,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting backtest details:', error);
      throw error;
    }
  }

  async compareStrategies(request: StrategyComparisonRequest): Promise<StrategyComparisonResult> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/historical/compare-strategies`,
        request,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error comparing strategies:', error);
      throw error;
    }
  }

  async getAnalysisHistory(
    symbol: string,
    startDate?: string,
    limit: number = 50
  ): Promise<AnalysisHistory[]> {
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      params.append('limit', limit.toString());

      const response = await axios.get(
        `${API_BASE_URL}/historical/analysis-history/${symbol}?${params}`,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting analysis history:', error);
      throw error;
    }
  }

  async getBacktestHistory(filters?: {
    strategy_name?: string;
    symbol?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<BacktestSummary[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.strategy_name) params.append('strategy_name', filters.strategy_name);
      if (filters?.symbol) params.append('symbol', filters.symbol);
      if (filters?.start_date) params.append('start_date', filters.start_date);
      if (filters?.end_date) params.append('end_date', filters.end_date);

      const response = await axios.get(
        `${API_BASE_URL}/historical/backtest-history?${params}`,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error getting backtest history:', error);
      throw error;
    }
  }

  async cleanupOldData(daysToKeep: number = 365): Promise<{ message: string; days_kept: number }> {
    try {
      const response = await axios.delete(
        `${API_BASE_URL}/historical/cleanup-old-data?days_to_keep=${daysToKeep}`,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error cleaning up old data:', error);
      throw error;
    }
  }
}

export const historicalAnalysisService = new HistoricalAnalysisService();