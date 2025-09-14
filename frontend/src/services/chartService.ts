/**
 * Chart Service
 * 
 * Handles chart data generation and processing for stock price charts
 */

import { 
  PricePoint, 
  TechnicalIndicator, 
  ChartAnnotation, 
  TimeFrame, 
  ChartData,
  SupportResistanceLevel 
} from '../types';

export interface ChartDataRequest {
  symbol: string;
  timeframe: TimeFrame;
  startDate?: string;
  endDate?: string;
  includeIndicators?: boolean;
  includeVolume?: boolean;
}

export interface ChartDataResponse {
  symbol: string;
  timeframe: TimeFrame;
  data: PricePoint[];
  indicators: TechnicalIndicator[];
  annotations: ChartAnnotation[];
  supportLevels: SupportResistanceLevel[];
  resistanceLevels: SupportResistanceLevel[];
  metadata: {
    dataPoints: number;
    startDate: string;
    endDate: string;
    lastUpdated: string;
  };
}

/**
 * Generate mock price data for testing
 */
export const generateMockPriceData = (
  symbol: string, 
  timeframe: TimeFrame, 
  days: number = 100
): PricePoint[] => {
  const data: PricePoint[] = [];
  const basePrice = 100 + Math.random() * 400; // Random base price between $100-$500
  let currentPrice = basePrice;
  
  const now = new Date();
  const msPerDay = 24 * 60 * 60 * 1000;
  
  // Determine interval based on timeframe
  let intervalMs = msPerDay; // Default to daily
  let dataPoints = days;
  
  switch (timeframe) {
    case '1D':
      intervalMs = 5 * 60 * 1000; // 5 minutes
      dataPoints = 78; // Trading hours: 6.5 hours * 12 intervals per hour
      break;
    case '1W':
      intervalMs = 60 * 60 * 1000; // 1 hour
      dataPoints = 168; // 7 days * 24 hours
      break;
    case '1M':
      intervalMs = msPerDay;
      dataPoints = days; // Use the provided days parameter
      break;
    case '3M':
      intervalMs = msPerDay;
      dataPoints = days; // Use the provided days parameter
      break;
    case '6M':
      intervalMs = msPerDay;
      dataPoints = days; // Use the provided days parameter
      break;
    case '1Y':
      intervalMs = msPerDay;
      dataPoints = days; // Use the provided days parameter
      break;
    case '2Y':
      intervalMs = msPerDay;
      dataPoints = days; // Use the provided days parameter
      break;
  }
  
  for (let i = dataPoints - 1; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - (i * intervalMs));
    
    // Generate realistic price movement
    const volatility = 0.02; // 2% daily volatility
    const trend = 0.0002; // Slight upward trend
    const randomChange = (Math.random() - 0.5) * volatility * currentPrice;
    const trendChange = trend * currentPrice;
    
    currentPrice += randomChange + trendChange;
    
    // Generate OHLC data
    const dayVolatility = volatility * 0.5;
    const high = currentPrice * (1 + Math.random() * dayVolatility);
    const low = currentPrice * (1 - Math.random() * dayVolatility);
    const open = low + Math.random() * (high - low);
    const close = low + Math.random() * (high - low);
    
    // Generate volume (higher volume on larger price moves)
    const priceChangePercent = Math.abs((close - open) / open);
    const baseVolume = 1000000 + Math.random() * 5000000;
    const volume = Math.floor(baseVolume * (1 + priceChangePercent * 3));
    
    data.push({
      timestamp,
      open,
      high,
      low,
      close,
      volume,
    });
    
    currentPrice = close;
  }
  
  return data;
};

/**
 * Generate mock technical indicators
 */
export const generateMockIndicators = (
  priceData: PricePoint[],
  symbol: string
): TechnicalIndicator[] => {
  const indicators: TechnicalIndicator[] = [];
  
  if (priceData.length < 20) return indicators;
  
  // Simple Moving Averages
  for (let i = 19; i < priceData.length; i++) {
    const sma20 = priceData.slice(i - 19, i + 1)
      .reduce((sum, point) => sum + point.close, 0) / 20;
    
    indicators.push({
      name: 'SMA_20',
      value: sma20,
      signal: 'neutral',
      period: 20,
      timestamp: priceData[i].timestamp.toISOString(),
    });
  }
  
  if (priceData.length >= 50) {
    for (let i = 49; i < priceData.length; i++) {
      const sma50 = priceData.slice(i - 49, i + 1)
        .reduce((sum, point) => sum + point.close, 0) / 50;
      
      indicators.push({
        name: 'SMA_50',
        value: sma50,
        signal: 'neutral',
        period: 50,
        timestamp: priceData[i].timestamp.toISOString(),
      });
    }
  }
  
  // Exponential Moving Averages (simplified calculation)
  const ema12Multiplier = 2 / (12 + 1);
  const ema26Multiplier = 2 / (26 + 1);
  
  if (priceData.length >= 12) {
    let ema12 = priceData.slice(0, 12).reduce((sum, point) => sum + point.close, 0) / 12;
    
    for (let i = 12; i < priceData.length; i++) {
      ema12 = (priceData[i].close * ema12Multiplier) + (ema12 * (1 - ema12Multiplier));
      
      indicators.push({
        name: 'EMA_12',
        value: ema12,
        signal: 'neutral',
        period: 12,
        timestamp: priceData[i].timestamp.toISOString(),
      });
    }
  }
  
  if (priceData.length >= 26) {
    let ema26 = priceData.slice(0, 26).reduce((sum, point) => sum + point.close, 0) / 26;
    
    for (let i = 26; i < priceData.length; i++) {
      ema26 = (priceData[i].close * ema26Multiplier) + (ema26 * (1 - ema26Multiplier));
      
      indicators.push({
        name: 'EMA_26',
        value: ema26,
        signal: 'neutral',
        period: 26,
        timestamp: priceData[i].timestamp.toISOString(),
      });
    }
  }
  
  // RSI (simplified calculation)
  if (priceData.length >= 15) {
    for (let i = 14; i < priceData.length; i++) {
      const period = priceData.slice(i - 13, i + 1);
      let gains = 0;
      let losses = 0;
      
      for (let j = 1; j < period.length; j++) {
        const change = period[j].close - period[j - 1].close;
        if (change > 0) gains += change;
        else losses += Math.abs(change);
      }
      
      const avgGain = gains / 14;
      const avgLoss = losses / 14;
      const rs = avgGain / (avgLoss || 0.01);
      const rsi = 100 - (100 / (1 + rs));
      
      let signal: 'strong_buy' | 'buy' | 'weak_buy' | 'neutral' | 'weak_sell' | 'sell' | 'strong_sell' = 'neutral';
      if (rsi > 70) signal = 'sell';
      else if (rsi > 60) signal = 'weak_sell';
      else if (rsi < 30) signal = 'buy';
      else if (rsi < 40) signal = 'weak_buy';
      
      indicators.push({
        name: 'RSI',
        value: rsi,
        signal,
        period: 14,
        timestamp: priceData[i].timestamp.toISOString(),
      });
    }
  }
  
  return indicators;
};

/**
 * Generate support and resistance levels
 */
export const generateSupportResistanceLevels = (
  priceData: PricePoint[]
): { supportLevels: SupportResistanceLevel[]; resistanceLevels: SupportResistanceLevel[] } => {
  if (priceData.length < 20) {
    return { supportLevels: [], resistanceLevels: [] };
  }
  
  const prices = priceData.map(p => p.close);
  const highs = priceData.map(p => p.high);
  const lows = priceData.map(p => p.low);
  
  const supportLevels: SupportResistanceLevel[] = [];
  const resistanceLevels: SupportResistanceLevel[] = [];
  
  // Find local minima for support
  for (let i = 5; i < prices.length - 5; i++) {
    const isLocalMin = lows.slice(i - 5, i).every(price => price >= lows[i]) &&
                       lows.slice(i + 1, i + 6).every(price => price >= lows[i]);
    
    if (isLocalMin) {
      // Count how many times price touched this level
      const level = lows[i];
      const touches = lows.filter(price => Math.abs(price - level) / level < 0.01).length;
      
      if (touches >= 2) {
        supportLevels.push({
          level,
          strength: Math.min(touches, 10),
          type: 'support',
          touches,
          lastTouch: priceData[i].timestamp.toISOString(),
        });
      }
    }
  }
  
  // Find local maxima for resistance
  for (let i = 5; i < prices.length - 5; i++) {
    const isLocalMax = highs.slice(i - 5, i).every(price => price <= highs[i]) &&
                       highs.slice(i + 1, i + 6).every(price => price <= highs[i]);
    
    if (isLocalMax) {
      // Count how many times price touched this level
      const level = highs[i];
      const touches = highs.filter(price => Math.abs(price - level) / level < 0.01).length;
      
      if (touches >= 2) {
        resistanceLevels.push({
          level,
          strength: Math.min(touches, 10),
          type: 'resistance',
          touches,
          lastTouch: priceData[i].timestamp.toISOString(),
        });
      }
    }
  }
  
  // Sort by strength and keep top 3 of each
  supportLevels.sort((a, b) => b.strength - a.strength);
  resistanceLevels.sort((a, b) => b.strength - a.strength);
  
  return {
    supportLevels: supportLevels.slice(0, 3),
    resistanceLevels: resistanceLevels.slice(0, 3),
  };
};

/**
 * Generate complete chart data for a symbol
 */
export const generateChartData = (
  symbol: string,
  timeframe: TimeFrame = '1M'
): ChartDataResponse => {
  const priceData = generateMockPriceData(symbol, timeframe);
  const indicators = generateMockIndicators(priceData, symbol);
  const { supportLevels, resistanceLevels } = generateSupportResistanceLevels(priceData);
  
  // Generate annotations from support/resistance
  const annotations: ChartAnnotation[] = [
    ...supportLevels.map(level => ({
      type: 'support' as const,
      value: level.level,
      label: `Support: $${level.level.toFixed(2)}`,
    })),
    ...resistanceLevels.map(level => ({
      type: 'resistance' as const,
      value: level.level,
      label: `Resistance: $${level.level.toFixed(2)}`,
    })),
  ];
  
  return {
    symbol,
    timeframe,
    data: priceData,
    indicators,
    annotations,
    supportLevels,
    resistanceLevels,
    metadata: {
      dataPoints: priceData.length,
      startDate: priceData[0]?.timestamp.toISOString() || '',
      endDate: priceData[priceData.length - 1]?.timestamp.toISOString() || '',
      lastUpdated: new Date().toISOString(),
    },
  };
};

/**
 * Create chart data for chat integration
 */
export const createChatChartData = (
  symbol: string,
  timeframe: TimeFrame = '1M'
): ChartData => {
  const chartResponse = generateChartData(symbol, timeframe);
  
  return {
    symbol: chartResponse.symbol,
    timeframe: chartResponse.timeframe,
    data: chartResponse.data,
    indicators: chartResponse.indicators,
    annotations: chartResponse.annotations,
  };
};

export default {
  generateMockPriceData,
  generateMockIndicators,
  generateSupportResistanceLevels,
  generateChartData,
  createChatChartData,
};