// Core type definitions for the application

// ============================================================================
// STOCK DATA TYPES
// ============================================================================

export interface Stock {
  symbol: string;
  name: string;
  exchange: string;
  sector?: string;
  industry?: string;
  marketCap?: number;
  lastUpdated: string;
}

export interface MarketData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high52Week?: number;
  low52Week?: number;
  avgVolume?: number;
  marketCap?: number;
  peRatio?: number;
  timestamp: string;
  isStale?: boolean;
}

// ============================================================================
// FUNDAMENTAL ANALYSIS TYPES
// ============================================================================

export interface FundamentalData {
  symbol: string;
  peRatio?: number;
  pbRatio?: number;
  roe?: number;
  debtToEquity?: number;
  revenueGrowth?: number;
  profitMargin?: number;
  eps?: number;
  dividend?: number;
  dividendYield?: number;
  bookValue?: number;
  revenue?: number;
  netIncome?: number;
  totalDebt?: number;
  totalEquity?: number;
  freeCashFlow?: number;
  quarter: string;
  year: number;
  lastUpdated: string;
}

// ============================================================================
// TECHNICAL ANALYSIS TYPES
// ============================================================================

export type TimeFrame = '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | '2Y';

export type TrendDirection = 'bullish' | 'bearish' | 'sideways' | 'unknown';

export type SignalStrength = 
  | 'strong_buy' 
  | 'buy' 
  | 'weak_buy' 
  | 'neutral' 
  | 'weak_sell' 
  | 'sell' 
  | 'strong_sell';

export interface TechnicalIndicator {
  name: string;
  value?: number;
  signal: SignalStrength;
  period?: number;
  timestamp: string;
}

export interface SupportResistanceLevel {
  level: number;
  strength: number; // 1-10
  type: 'support' | 'resistance';
  touches: number;
  lastTouch?: string;
}

export interface TechnicalData {
  symbol: string;
  timeframe: TimeFrame;
  
  // Moving Averages
  sma20?: number;
  sma50?: number;
  sma200?: number;
  ema12?: number;
  ema26?: number;
  
  // Momentum Indicators
  rsi?: number;
  macd?: number;
  macdSignal?: number;
  macdHistogram?: number;
  
  // Bollinger Bands
  bollingerUpper?: number;
  bollingerLower?: number;
  bollingerMiddle?: number;
  
  // Volume Indicators
  volumeSma?: number;
  obv?: number;
  
  // Volatility
  atr?: number;
  
  // Support and Resistance
  supportLevels: SupportResistanceLevel[];
  resistanceLevels: SupportResistanceLevel[];
  
  // Overall Analysis
  trendDirection: TrendDirection;
  overallSignal: SignalStrength;
  
  // Metadata
  timestamp: string;
  dataPoints: number;
}

// ============================================================================
// WATCHLIST TYPES
// ============================================================================

export interface WatchlistItem {
  id: number;
  watchlistId: number;
  symbol: string;
  companyName?: string;
  notes?: string;
  targetPrice?: number;
  entryPrice?: number;
  sharesOwned?: number;
  addedAt: string;
  updatedAt: string;
  
  // Real-time market data (populated dynamically)
  currentPrice?: number;
  dailyChange?: number;
  dailyChangePercent?: number;
  volume?: number;
  isMarketOpen?: boolean;
  lastUpdated?: string;
}

export interface Watchlist {
  id: number;
  userId: number;
  name: string;
  description?: string;
  isDefault: boolean;
  createdAt: string;
  updatedAt: string;
  items: WatchlistItem[];
  
  // Summary statistics (populated dynamically)
  totalItems: number;
  totalValue?: number;
  totalGainLoss?: number;
  totalGainLossPercent?: number;
}

export interface WatchlistSummary {
  id: number;
  name: string;
  description?: string;
  isDefault: boolean;
  userId: number;
  createdAt: string;
  updatedAt: string;
  totalItems: number;
}

export interface WatchlistCreateRequest {
  name: string;
  description?: string;
  isDefault?: boolean;
}

export interface WatchlistUpdateRequest {
  name?: string;
  description?: string;
  isDefault?: boolean;
}

export interface WatchlistItemCreateRequest {
  symbol: string;
  companyName?: string;
  notes?: string;
  targetPrice?: number;
  entryPrice?: number;
  sharesOwned?: number;
}

export interface WatchlistItemUpdateRequest {
  companyName?: string;
  notes?: string;
  targetPrice?: number;
  entryPrice?: number;
  sharesOwned?: number;
}

export interface WatchlistBulkAddRequest {
  symbols: string[];
}

export interface WatchlistBulkAddResponse {
  addedSymbols: string[];
  failedSymbols: Array<{
    symbol: string;
    error: string;
  }>;
  totalAdded: number;
  totalFailed: number;
}

export interface WatchlistStats {
  totalWatchlists: number;
  totalItems: number;
  mostWatchedSymbols: Array<{
    symbol: string;
    count: number;
  }>;
  recentAdditions: string[];
  performanceSummary: Record<string, any>;
}

// ============================================================================
// CHAT AND UI TYPES
// ============================================================================

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    stockSymbol?: string;
    analysisType?: string;
    charts?: ChartData[];
    analysisData?: any;
    suggestions?: string[];
    requiresFollowUp?: boolean;
    errorCode?: string;
    level?: 'info' | 'warning' | 'error';
  };
}

export interface ChartData {
  symbol: string;
  timeframe: TimeFrame;
  data: PricePoint[];
  indicators: TechnicalIndicator[];
  annotations: ChartAnnotation[];
}

export interface PricePoint {
  timestamp: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartAnnotation {
  type: 'support' | 'resistance' | 'trend';
  value: number;
  label: string;
}

// ============================================================================
// API RESPONSE TYPES
// ============================================================================

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: ValidationError[];
  timestamp: string;
}

// ============================================================================
// ANALYSIS RESULT TYPES
// ============================================================================

export type AnalysisType = 'fundamental' | 'technical' | 'sentiment' | 'combined';

export type Recommendation = 'BUY' | 'SELL' | 'HOLD';

export interface AnalysisResult {
  symbol: string;
  analysisType: AnalysisType;
  score: number; // 0-100
  recommendation: Recommendation;
  confidence: number; // 0-100
  reasoning: string[];
  risks: string[];
  targets: {
    shortTerm?: number;
    mediumTerm?: number;
    longTerm?: number;
  };
  timestamp: string;
}

// ============================================================================
// ALERT TYPES
// ============================================================================

export * from './alert';

// ============================================================================
// OPPORTUNITY TYPES
// ============================================================================

export * from './opportunity';

// ============================================================================
// EDUCATIONAL TYPES
// ============================================================================

export interface EducationalProgress {
  totalConcepts: number;
  completedConcepts: number;
  progressPercentage: number;
  currentLevel: 'beginner' | 'intermediate' | 'advanced';
  recentCompletions: Array<{
    conceptName: string;
    completedAt: string;
    difficultyRating?: number;
  }>;
  suggestedConcepts: Array<{
    name: string;
    type: string;
    difficulty: string;
    estimatedMinutes: number;
  }>;
  streakDays: number;
  lastActivityDate?: string;
}

export interface UserProfile {
  id: number;
  email: string;
  fullName?: string;
  preferences: {
    riskTolerance: 'conservative' | 'moderate' | 'aggressive';
    investmentHorizon: 'short' | 'medium' | 'long';
    preferredAnalysis: ('fundamental' | 'technical' | 'sentiment')[];
    notificationSettings: {
      emailAlerts: boolean;
      pushNotifications: boolean;
      priceAlerts: boolean;
      newsAlerts: boolean;
      educationalReminders: boolean;
    };
    displaySettings: {
      theme: 'light' | 'dark';
      currency: string;
      chartType: string;
      showEducationalTooltips: boolean;
    };
  };
  educationalProgress: EducationalProgress;
  createdAt: string;
  lastActive: string;
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface SearchFilters {
  symbol?: string;
  sector?: string;
  marketCapMin?: number;
  marketCapMax?: number;
  peRatioMax?: number;
  dividendYieldMin?: number;
}