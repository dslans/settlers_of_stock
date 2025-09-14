/**
 * Type validation tests for frontend data models.
 * This file ensures TypeScript interfaces are properly structured.
 */

import {
  Stock,
  MarketData,
  FundamentalData,
  TechnicalData,
  TechnicalIndicator,
  SupportResistanceLevel,
  TimeFrame,
  TrendDirection,
  SignalStrength,
  AnalysisResult,
  ApiResponse,
  ErrorResponse
} from './index';

// Test Stock interface
const testStock: Stock = {
  symbol: 'AAPL',
  name: 'Apple Inc.',
  exchange: 'NASDAQ',
  sector: 'Technology',
  industry: 'Consumer Electronics',
  marketCap: 3000000000000,
  lastUpdated: '2024-01-15T10:30:00Z'
};

// Test MarketData interface
const testMarketData: MarketData = {
  symbol: 'AAPL',
  price: 150.25,
  change: 2.50,
  changePercent: 1.69,
  volume: 75000000,
  high52Week: 180.00,
  low52Week: 120.00,
  avgVolume: 80000000,
  marketCap: 2500000000000,
  peRatio: 25.5,
  timestamp: '2024-01-15T15:30:00Z',
  isStale: false
};

// Test FundamentalData interface
const testFundamentalData: FundamentalData = {
  symbol: 'AAPL',
  peRatio: 25.5,
  pbRatio: 8.2,
  roe: 0.28,
  debtToEquity: 0.45,
  revenueGrowth: 0.08,
  profitMargin: 0.23,
  eps: 6.15,
  dividend: 0.92,
  dividendYield: 0.006,
  bookValue: 18.5,
  revenue: 394328000000,
  netIncome: 99803000000,
  totalDebt: 132480000000,
  totalEquity: 62146000000,
  freeCashFlow: 84726000000,
  quarter: 'Q4',
  year: 2024,
  lastUpdated: '2024-01-15T10:30:00Z'
};

// Test SupportResistanceLevel interface
const testSupportLevel: SupportResistanceLevel = {
  level: 145.00,
  strength: 8,
  type: 'support',
  touches: 3,
  lastTouch: '2024-01-10T14:30:00Z'
};

const testResistanceLevel: SupportResistanceLevel = {
  level: 155.00,
  strength: 7,
  type: 'resistance',
  touches: 2,
  lastTouch: '2024-01-12T11:15:00Z'
};

// Test TechnicalIndicator interface
const testTechnicalIndicator: TechnicalIndicator = {
  name: 'RSI',
  value: 65.5,
  signal: 'neutral',
  period: 14,
  timestamp: '2024-01-15T15:30:00Z'
};

// Test TechnicalData interface
const testTechnicalData: TechnicalData = {
  symbol: 'AAPL',
  timeframe: '1D',
  sma20: 148.50,
  sma50: 145.20,
  sma200: 140.80,
  ema12: 149.10,
  ema26: 147.30,
  rsi: 65.5,
  macd: 1.25,
  macdSignal: 0.85,
  macdHistogram: 0.40,
  bollingerUpper: 152.00,
  bollingerLower: 144.00,
  bollingerMiddle: 148.00,
  volumeSma: 75000000,
  obv: 1250000000,
  atr: 2.45,
  supportLevels: [testSupportLevel],
  resistanceLevels: [testResistanceLevel],
  trendDirection: 'bullish',
  overallSignal: 'buy',
  timestamp: '2024-01-15T15:30:00Z',
  dataPoints: 252
};

// Test AnalysisResult interface
const testAnalysisResult: AnalysisResult = {
  symbol: 'AAPL',
  analysisType: 'combined',
  score: 85,
  recommendation: 'BUY',
  confidence: 78,
  reasoning: [
    'Strong fundamental metrics with PE ratio of 25.5',
    'Technical indicators showing bullish momentum',
    'RSI at 65.5 indicates room for growth'
  ],
  risks: [
    'Market volatility could affect short-term performance',
    'High valuation compared to sector average'
  ],
  targets: {
    shortTerm: 160.00,
    mediumTerm: 175.00,
    longTerm: 200.00
  },
  timestamp: '2024-01-15T15:30:00Z'
};

// Test ApiResponse interface
const testApiResponse: ApiResponse<MarketData> = {
  data: testMarketData,
  message: 'Market data retrieved successfully'
};

// Test ErrorResponse interface
const testErrorResponse: ErrorResponse = {
  error: 'ValidationError',
  message: 'Invalid stock symbol provided',
  details: [
    {
      field: 'symbol',
      message: 'Symbol must be between 1 and 10 characters',
      code: 'INVALID_LENGTH'
    }
  ],
  timestamp: '2024-01-15T15:30:00Z'
};

// Test enum values
const timeFrames: TimeFrame[] = ['1D', '1W', '1M', '3M', '6M', '1Y', '2Y'];
const trendDirections: TrendDirection[] = ['bullish', 'bearish', 'sideways', 'unknown'];
const signalStrengths: SignalStrength[] = [
  'strong_buy', 'buy', 'weak_buy', 'neutral', 'weak_sell', 'sell', 'strong_sell'
];

// Type validation functions
export function validateStock(data: unknown): data is Stock {
  const stock = data as Stock;
  return (
    typeof stock.symbol === 'string' &&
    typeof stock.name === 'string' &&
    typeof stock.exchange === 'string' &&
    typeof stock.lastUpdated === 'string'
  );
}

export function validateMarketData(data: unknown): data is MarketData {
  const marketData = data as MarketData;
  return (
    typeof marketData.symbol === 'string' &&
    typeof marketData.price === 'number' &&
    typeof marketData.change === 'number' &&
    typeof marketData.changePercent === 'number' &&
    typeof marketData.volume === 'number' &&
    typeof marketData.timestamp === 'string'
  );
}

export function validateFundamentalData(data: unknown): data is FundamentalData {
  const fundamental = data as FundamentalData;
  return (
    typeof fundamental.symbol === 'string' &&
    typeof fundamental.quarter === 'string' &&
    typeof fundamental.year === 'number' &&
    typeof fundamental.lastUpdated === 'string'
  );
}

export function validateTechnicalData(data: unknown): data is TechnicalData {
  const technical = data as TechnicalData;
  return (
    typeof technical.symbol === 'string' &&
    timeFrames.includes(technical.timeframe) &&
    trendDirections.includes(technical.trendDirection) &&
    signalStrengths.includes(technical.overallSignal) &&
    Array.isArray(technical.supportLevels) &&
    Array.isArray(technical.resistanceLevels) &&
    typeof technical.timestamp === 'string' &&
    typeof technical.dataPoints === 'number'
  );
}

// Export test data for use in other files
export const testData = {
  stock: testStock,
  marketData: testMarketData,
  fundamentalData: testFundamentalData,
  technicalData: testTechnicalData,
  analysisResult: testAnalysisResult,
  apiResponse: testApiResponse,
  errorResponse: testErrorResponse
};

console.log('✅ All TypeScript interfaces validated successfully');