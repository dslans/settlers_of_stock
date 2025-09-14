/**
 * TypeScript types for investment opportunity search functionality.
 */

export type OpportunityType = 
  | 'undervalued'
  | 'growth'
  | 'momentum'
  | 'dividend'
  | 'breakout'
  | 'oversold'
  | 'earnings_surprise';

export type RiskLevel = 'low' | 'moderate' | 'high' | 'very_high';

export type MarketCapCategory = 
  | 'mega_cap'
  | 'large_cap'
  | 'mid_cap'
  | 'small_cap'
  | 'micro_cap';

export interface OpportunitySearchFilters {
  // Market cap filters
  marketCapMin?: number;
  marketCapMax?: number;
  marketCapCategories?: MarketCapCategory[];
  
  // Sector and industry filters
  sectors?: string[];
  industries?: string[];
  excludeSectors?: string[];
  
  // Performance filters
  priceChange1dMin?: number;
  priceChange1dMax?: number;
  priceChange1wMin?: number;
  priceChange1wMax?: number;
  priceChange1mMin?: number;
  priceChange1mMax?: number;
  
  // Volume filters
  volumeMin?: number;
  avgVolumeMin?: number;
  
  // Fundamental filters
  peRatioMin?: number;
  peRatioMax?: number;
  pbRatioMin?: number;
  pbRatioMax?: number;
  roeMin?: number;
  debtToEquityMax?: number;
  profitMarginMin?: number;
  revenueGrowthMin?: number;
  
  // Technical filters
  rsiMin?: number;
  rsiMax?: number;
  priceAboveSma20?: boolean;
  priceAboveSma50?: boolean;
  
  // Opportunity type filters
  opportunityTypes?: OpportunityType[];
  
  // Risk filters
  maxRiskLevel?: RiskLevel;
  
  // Result filters
  limit?: number;
  minScore?: number;
}

export interface OpportunityScore {
  overallScore: number;
  fundamentalScore?: number;
  technicalScore?: number;
  momentumScore?: number;
  valueScore?: number;
  qualityScore?: number;
  scoreComponents?: Record<string, number>;
}

export interface InvestmentOpportunity {
  // Basic stock information
  symbol: string;
  name: string;
  sector?: string;
  industry?: string;
  
  // Current market data
  currentPrice: number;
  marketCap?: number;
  volume: number;
  
  // Opportunity details
  opportunityTypes: OpportunityType[];
  riskLevel: RiskLevel;
  
  // Scoring
  scores: OpportunityScore;
  
  // Key metrics
  keyMetrics: Record<string, string | number>;
  
  // Analysis
  reasons: string[];
  risks: string[];
  catalysts: string[];
  
  // Price targets
  priceTargetShort?: number;
  priceTargetMedium?: number;
  priceTargetLong?: number;
  
  // Metadata
  lastUpdated: string;
  dataFreshness: Record<string, string | null>;
}

export interface OpportunityRanking {
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  fundamentalWeight: number;
  technicalWeight: number;
  momentumWeight: number;
  valueWeight: number;
}

export interface OpportunitySearchResult {
  opportunities: InvestmentOpportunity[];
  totalFound: number;
  filtersApplied: OpportunitySearchFilters;
  searchTimestamp: string;
  executionTimeMs?: number;
  stats: Record<string, any>;
}

export interface OpportunitySearchRequest {
  filters: OpportunitySearchFilters;
  ranking?: OpportunityRanking;
  universe?: string;
}

export interface QuickSearchResponse {
  opportunities: SimplifiedOpportunity[];
  totalFound: number;
  searchTimeMs: number;
}

export interface SimplifiedOpportunity {
  symbol: string;
  name: string;
  currentPrice: number;
  score: number;
  opportunityTypes: string[];
  riskLevel: string;
  sector?: string;
  marketCap?: number;
}

export interface OpportunityFilterOptions {
  opportunityTypes: string[];
  riskLevels: string[];
  marketCapCategories: string[];
  popularSectors: string[];
  timeframes: string[];
  sortOptions: string[];
  sortOrders: string[];
}

export interface OpportunityFilterValidation {
  valid: boolean;
  issues: string[];
  warnings: string[];
  filterCount: number;
}

// Error response type
export interface OpportunityErrorResponse {
  error: boolean;
  message: string;
  errorType: string;
  suggestions: string[];
  timestamp: string;
}

// Display helpers
export const OPPORTUNITY_TYPE_LABELS: Record<OpportunityType, string> = {
  undervalued: 'Undervalued',
  growth: 'Growth',
  momentum: 'Momentum',
  dividend: 'Dividend',
  breakout: 'Breakout',
  oversold: 'Oversold',
  earnings_surprise: 'Earnings Surprise'
};

export const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  low: 'Low Risk',
  moderate: 'Moderate Risk',
  high: 'High Risk',
  very_high: 'Very High Risk'
};

export const MARKET_CAP_LABELS: Record<MarketCapCategory, string> = {
  mega_cap: 'Mega Cap (>$200B)',
  large_cap: 'Large Cap ($10B-$200B)',
  mid_cap: 'Mid Cap ($2B-$10B)',
  small_cap: 'Small Cap ($300M-$2B)',
  micro_cap: 'Micro Cap (<$300M)'
};

// Color schemes for UI
export const RISK_LEVEL_COLORS: Record<RiskLevel, string> = {
  low: '#10B981',      // Green
  moderate: '#F59E0B',  // Yellow
  high: '#EF4444',     // Red
  very_high: '#DC2626' // Dark Red
};

export const OPPORTUNITY_TYPE_COLORS: Record<OpportunityType, string> = {
  undervalued: '#3B82F6',    // Blue
  growth: '#10B981',         // Green
  momentum: '#8B5CF6',       // Purple
  dividend: '#F59E0B',       // Orange
  breakout: '#EF4444',       // Red
  oversold: '#06B6D4',       // Cyan
  earnings_surprise: '#EC4899' // Pink
};