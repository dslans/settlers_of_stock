/**
 * Sector Analysis Service
 * 
 * Provides functions for sector performance analysis, industry comparisons,
 * and sector rotation identification.
 */

import { api } from './api';

// Types for sector analysis
export interface SectorCategory {
  name: string;
  code: string;
}

export interface SectorPerformance {
  sector: string;
  performance_1d: number;
  performance_1w: number;
  performance_1m: number;
  performance_3m: number;
  performance_6m: number;
  performance_1y: number;
  performance_ytd: number;
  relative_performance_1m: number;
  relative_performance_3m: number;
  relative_performance_1y: number;
  trend_direction: 'strong_up' | 'up' | 'sideways' | 'down' | 'strong_down';
  trend_strength: number;
  momentum_score: number;
  market_cap: number;
  avg_volume: number;
  pe_ratio?: number;
  pb_ratio?: number;
  performance_rank_1m: number;
  performance_rank_3m: number;
  performance_rank_1y: number;
  volatility: number;
  beta?: number;
  dividend_yield?: number;
  last_updated: string;
}

export interface IndustryPerformance {
  industry: string;
  sector: string;
  performance_1d: number;
  performance_1w: number;
  performance_1m: number;
  performance_3m: number;
  performance_1y: number;
  relative_to_sector_1m: number;
  relative_to_sector_3m: number;
  relative_to_sector_1y: number;
  avg_pe_ratio?: number;
  avg_pb_ratio?: number;
  avg_roe?: number;
  avg_profit_margin?: number;
  revenue_growth?: number;
  earnings_growth?: number;
  market_cap: number;
  stock_count: number;
  performance_rank: number;
  valuation_rank: number;
  growth_rank: number;
  last_updated: string;
}

export interface SectorRotationSignal {
  from_sector: string;
  to_sector: string;
  signal_strength: number;
  confidence: number;
  momentum_shift: number;
  relative_strength_change: number;
  volume_confirmation: boolean;
  market_phase: 'early_cycle' | 'mid_cycle' | 'late_cycle' | 'recession';
  economic_driver: string;
  signal_date: string;
  expected_duration: string;
  reasons: string[];
  risks: string[];
  last_updated: string;
}

export interface SectorAnalysisResult {
  sector_performances: SectorPerformance[];
  top_performers_1m: string[];
  top_performers_3m: string[];
  top_performers_1y: string[];
  bottom_performers_1m: string[];
  bottom_performers_3m: string[];
  bottom_performers_1y: string[];
  rotation_signals: SectorRotationSignal[];
  market_trend: 'strong_up' | 'up' | 'sideways' | 'down' | 'strong_down';
  market_phase: 'early_cycle' | 'mid_cycle' | 'late_cycle' | 'recession';
  volatility_regime: string;
  analysis_timestamp: string;
  data_freshness: Record<string, string>;
}

export interface IndustryAnalysisResult {
  sector: string;
  industries: IndustryPerformance[];
  top_performing_industries: string[];
  best_value_industries: string[];
  highest_growth_industries: string[];
  sector_summary: SectorPerformance;
  analysis_timestamp: string;
}

export interface SectorComparisonRequest {
  sectors: string[];
  timeframe: string;
  metrics: string[];
}

export interface SectorComparisonResult {
  sectors: string[];
  timeframe: string;
  performance_ranking: Array<{
    sector: string;
    performance: number;
    rank: number;
  }>;
  valuation_ranking: Array<{
    sector: string;
    pe_ratio?: number;
    pb_ratio?: number;
    rank: number;
  }>;
  momentum_ranking: Array<{
    sector: string;
    momentum_score: number;
    trend_strength: number;
    rank: number;
  }>;
  winner: string;
  best_value: string;
  strongest_momentum: string;
  key_insights: string[];
  recommendations: string[];
  analysis_timestamp: string;
}

export interface SectorRankingResult {
  rankings: Array<{
    rank: number;
    sector: string;
    sector_code: string;
    [key: string]: any;
  }>;
  sort_by: string;
  order: string;
  total_sectors: number;
}

/**
 * Get list of available sectors
 */
export const getSectors = async (): Promise<{ sectors: SectorCategory[]; total_count: number }> => {
  const response = await api.get('/sectors/');
  return response.data;
};

/**
 * Perform comprehensive analysis of all sectors
 */
export const analyzeSectors = async (): Promise<SectorAnalysisResult> => {
  const response = await api.get('/sectors/analysis');
  return response.data;
};

/**
 * Get detailed performance analysis for a specific sector
 */
export const getSectorPerformance = async (sector: string): Promise<SectorPerformance> => {
  const response = await api.get(`/sectors/performance/${sector}`);
  return response.data;
};

/**
 * Analyze industries within a specific sector
 */
export const analyzeSectorIndustries = async (sector: string): Promise<IndustryAnalysisResult> => {
  const response = await api.get(`/sectors/industries/${sector}`);
  return response.data;
};

/**
 * Compare performance of multiple sectors
 */
export const compareSectors = async (request: SectorComparisonRequest): Promise<SectorComparisonResult> => {
  const response = await api.post('/sectors/compare', request);
  return response.data;
};

/**
 * Get current sector rotation signals
 */
export const getRotationSignals = async (minStrength: number = 50): Promise<SectorRotationSignal[]> => {
  const response = await api.get('/sectors/rotation-signals', {
    params: { min_strength: minStrength }
  });
  return response.data;
};

/**
 * Get top performing sectors for different timeframes
 */
export const getTopPerformers = async (
  timeframe: string = '3m',
  limit: number = 5
): Promise<Record<string, any>> => {
  const response = await api.get('/sectors/top-performers', {
    params: { timeframe, limit }
  });
  return response.data;
};

/**
 * Get comprehensive sector rankings by various metrics
 */
export const getSectorRankings = async (
  sortBy: string = 'performance_3m',
  order: string = 'desc'
): Promise<SectorRankingResult> => {
  const response = await api.get('/sectors/rankings', {
    params: { sort_by: sortBy, order }
  });
  return response.data;
};

/**
 * Format performance percentage for display
 */
export const formatPerformance = (value: number): string => {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
};

/**
 * Get performance color based on value
 */
export const getPerformanceColor = (value: number): string => {
  if (value > 5) return '#22c55e'; // green-500
  if (value > 0) return '#84cc16'; // lime-500
  if (value > -5) return '#f59e0b'; // amber-500
  return '#ef4444'; // red-500
};

/**
 * Get trend direction display text
 */
export const getTrendDirectionText = (direction: string): string => {
  const directions: Record<string, string> = {
    'strong_up': 'Strong Uptrend',
    'up': 'Uptrend',
    'sideways': 'Sideways',
    'down': 'Downtrend',
    'strong_down': 'Strong Downtrend'
  };
  return directions[direction] || direction;
};

/**
 * Get market phase display text
 */
export const getMarketPhaseText = (phase: string): string => {
  const phases: Record<string, string> = {
    'early_cycle': 'Early Cycle',
    'mid_cycle': 'Mid Cycle',
    'late_cycle': 'Late Cycle',
    'recession': 'Recession'
  };
  return phases[phase] || phase;
};

/**
 * Format market cap for display
 */
export const formatMarketCap = (value: number): string => {
  if (value >= 1e12) {
    return `$${(value / 1e12).toFixed(2)}T`;
  } else if (value >= 1e9) {
    return `$${(value / 1e9).toFixed(2)}B`;
  } else if (value >= 1e6) {
    return `$${(value / 1e6).toFixed(2)}M`;
  } else {
    return `$${value.toLocaleString()}`;
  }
};

/**
 * Format volume for display
 */
export const formatVolume = (value: number): string => {
  if (value >= 1e9) {
    return `${(value / 1e9).toFixed(2)}B`;
  } else if (value >= 1e6) {
    return `${(value / 1e6).toFixed(2)}M`;
  } else if (value >= 1e3) {
    return `${(value / 1e3).toFixed(2)}K`;
  } else {
    return value.toLocaleString();
  }
};