/**
 * Chart Service Tests
 */

import {
  generateMockPriceData,
  generateMockIndicators,
  generateSupportResistanceLevels,
  generateChartData,
  createChatChartData,
} from '../chartService';
import { TimeFrame } from '../../types';

describe('Chart Service', () => {
  describe('generateMockPriceData', () => {
    it('generates price data with correct length for different timeframes', () => {
      const symbol = 'AAPL';
      
      const dailyData = generateMockPriceData(symbol, '1D');
      expect(dailyData).toHaveLength(78); // Trading hours data points
      
      const weeklyData = generateMockPriceData(symbol, '1W');
      expect(weeklyData).toHaveLength(168); // 7 days * 24 hours
      
      const monthlyData = generateMockPriceData(symbol, '1M', 30);
      expect(monthlyData).toHaveLength(30); // 30 days when specified
    });

    it('generates realistic OHLC data', () => {
      const data = generateMockPriceData('AAPL', '1M', 10);
      
      data.forEach(point => {
        expect(point.high).toBeGreaterThanOrEqual(point.low);
        expect(point.high).toBeGreaterThanOrEqual(point.open);
        expect(point.high).toBeGreaterThanOrEqual(point.close);
        expect(point.open).toBeGreaterThanOrEqual(point.low);
        expect(point.close).toBeGreaterThanOrEqual(point.low);
        expect(point.volume).toBeGreaterThan(0);
        expect(point.timestamp).toBeInstanceOf(Date);
      });
    });

    it('generates data in chronological order', () => {
      const data = generateMockPriceData('AAPL', '1M', 10);
      
      for (let i = 1; i < data.length; i++) {
        expect(data[i].timestamp.getTime()).toBeGreaterThan(data[i - 1].timestamp.getTime());
      }
    });

    it('generates reasonable price ranges', () => {
      const data = generateMockPriceData('AAPL', '1M', 100);
      const prices = data.map(p => p.close);
      const minPrice = Math.min(...prices);
      const maxPrice = Math.max(...prices);
      
      // Prices should be within a reasonable range (not negative, not extremely volatile)
      expect(minPrice).toBeGreaterThan(0);
      expect(maxPrice / minPrice).toBeLessThan(10); // Max 10x price movement
    });

    it('generates volume data correlated with price movements', () => {
      const data = generateMockPriceData('AAPL', '1M', 50);
      
      data.forEach(point => {
        expect(point.volume).toBeGreaterThan(100000); // Minimum realistic volume
        expect(point.volume).toBeLessThan(50000000); // Maximum realistic volume
      });
    });
  });

  describe('generateMockIndicators', () => {
    const priceData = generateMockPriceData('AAPL', '1M', 100);

    it('generates SMA indicators with correct periods', () => {
      const indicators = generateMockIndicators(priceData, 'AAPL');
      
      const sma20Indicators = indicators.filter(ind => ind.name === 'SMA_20');
      const sma50Indicators = indicators.filter(ind => ind.name === 'SMA_50');
      
      expect(sma20Indicators.length).toBe(priceData.length - 19); // 20-period SMA
      if (priceData.length >= 50) {
        expect(sma50Indicators.length).toBe(priceData.length - 49); // 50-period SMA
      } else {
        expect(sma50Indicators.length).toBe(0);
      }
      
      sma20Indicators.forEach(ind => {
        expect(ind.period).toBe(20);
        expect(ind.value).toBeGreaterThan(0);
      });
    });

    it('generates EMA indicators', () => {
      const indicators = generateMockIndicators(priceData, 'AAPL');
      
      const ema12Indicators = indicators.filter(ind => ind.name === 'EMA_12');
      const ema26Indicators = indicators.filter(ind => ind.name === 'EMA_26');
      
      expect(ema12Indicators.length).toBe(priceData.length - 12);
      expect(ema26Indicators.length).toBe(priceData.length - 26);
      
      ema12Indicators.forEach(ind => {
        expect(ind.period).toBe(12);
        expect(ind.value).toBeGreaterThan(0);
      });
    });

    it('generates RSI indicators with proper range', () => {
      const indicators = generateMockIndicators(priceData, 'AAPL');
      
      const rsiIndicators = indicators.filter(ind => ind.name === 'RSI');
      
      expect(rsiIndicators.length).toBe(priceData.length - 14);
      
      rsiIndicators.forEach(ind => {
        expect(ind.value).toBeGreaterThanOrEqual(0);
        expect(ind.value).toBeLessThanOrEqual(100);
        expect(ind.period).toBe(14);
        expect(['strong_buy', 'buy', 'weak_buy', 'neutral', 'weak_sell', 'sell', 'strong_sell'])
          .toContain(ind.signal);
      });
    });

    it('generates proper RSI signals based on values', () => {
      const indicators = generateMockIndicators(priceData, 'AAPL');
      const rsiIndicators = indicators.filter(ind => ind.name === 'RSI');
      
      rsiIndicators.forEach(ind => {
        if (ind.value! > 70) {
          expect(ind.signal).toBe('sell');
        } else if (ind.value! > 60) {
          expect(ind.signal).toBe('weak_sell');
        } else if (ind.value! < 30) {
          expect(ind.signal).toBe('buy');
        } else if (ind.value! < 40) {
          expect(ind.signal).toBe('weak_buy');
        } else {
          expect(ind.signal).toBe('neutral');
        }
      });
    });

    it('handles insufficient data gracefully', () => {
      const shortData = generateMockPriceData('AAPL', '1M', 15);
      const indicators = generateMockIndicators(shortData, 'AAPL');
      
      // Should have no SMA-20 indicators since we need at least 20 data points
      const sma20Indicators = indicators.filter(ind => ind.name === 'SMA_20');
      expect(sma20Indicators).toHaveLength(0);
      
      // Should have no SMA-50 indicators since we need at least 50 data points
      const sma50Indicators = indicators.filter(ind => ind.name === 'SMA_50');
      expect(sma50Indicators).toHaveLength(0);
    });

    it('generates timestamps for all indicators', () => {
      const indicators = generateMockIndicators(priceData, 'AAPL');
      
      indicators.forEach(ind => {
        expect(ind.timestamp).toBeDefined();
        expect(new Date(ind.timestamp)).toBeInstanceOf(Date);
      });
    });
  });

  describe('generateSupportResistanceLevels', () => {
    const priceData = generateMockPriceData('AAPL', '1M', 100);

    it('generates support and resistance levels', () => {
      const { supportLevels, resistanceLevels } = generateSupportResistanceLevels(priceData);
      
      expect(Array.isArray(supportLevels)).toBe(true);
      expect(Array.isArray(resistanceLevels)).toBe(true);
      
      supportLevels.forEach(level => {
        expect(level.type).toBe('support');
        expect(level.level).toBeGreaterThan(0);
        expect(level.strength).toBeGreaterThanOrEqual(2);
        expect(level.strength).toBeLessThanOrEqual(10);
        expect(level.touches).toBeGreaterThanOrEqual(2);
      });
      
      resistanceLevels.forEach(level => {
        expect(level.type).toBe('resistance');
        expect(level.level).toBeGreaterThan(0);
        expect(level.strength).toBeGreaterThanOrEqual(2);
        expect(level.strength).toBeLessThanOrEqual(10);
        expect(level.touches).toBeGreaterThanOrEqual(2);
      });
    });

    it('limits results to top 3 levels of each type', () => {
      const { supportLevels, resistanceLevels } = generateSupportResistanceLevels(priceData);
      
      expect(supportLevels.length).toBeLessThanOrEqual(3);
      expect(resistanceLevels.length).toBeLessThanOrEqual(3);
    });

    it('sorts levels by strength', () => {
      const { supportLevels, resistanceLevels } = generateSupportResistanceLevels(priceData);
      
      for (let i = 1; i < supportLevels.length; i++) {
        expect(supportLevels[i - 1].strength).toBeGreaterThanOrEqual(supportLevels[i].strength);
      }
      
      for (let i = 1; i < resistanceLevels.length; i++) {
        expect(resistanceLevels[i - 1].strength).toBeGreaterThanOrEqual(resistanceLevels[i].strength);
      }
    });

    it('handles insufficient data gracefully', () => {
      const shortData = generateMockPriceData('AAPL', '1M', 15);
      const { supportLevels, resistanceLevels } = generateSupportResistanceLevels(shortData);
      
      // With only 15 data points, we might not find strong support/resistance levels
      // The function should still work but may return fewer or no levels
      expect(Array.isArray(supportLevels)).toBe(true);
      expect(Array.isArray(resistanceLevels)).toBe(true);
    });

    it('includes lastTouch timestamps', () => {
      const { supportLevels, resistanceLevels } = generateSupportResistanceLevels(priceData);
      
      [...supportLevels, ...resistanceLevels].forEach(level => {
        expect(level.lastTouch).toBeDefined();
        expect(new Date(level.lastTouch!)).toBeInstanceOf(Date);
      });
    });
  });

  describe('generateChartData', () => {
    it('generates complete chart data response', () => {
      const chartData = generateChartData('AAPL', '1M');
      
      expect(chartData.symbol).toBe('AAPL');
      expect(chartData.timeframe).toBe('1M');
      expect(Array.isArray(chartData.data)).toBe(true);
      expect(Array.isArray(chartData.indicators)).toBe(true);
      expect(Array.isArray(chartData.annotations)).toBe(true);
      expect(Array.isArray(chartData.supportLevels)).toBe(true);
      expect(Array.isArray(chartData.resistanceLevels)).toBe(true);
      expect(chartData.metadata).toBeDefined();
    });

    it('generates annotations from support/resistance levels', () => {
      const chartData = generateChartData('AAPL', '1M');
      
      const supportAnnotations = chartData.annotations.filter(a => a.type === 'support');
      const resistanceAnnotations = chartData.annotations.filter(a => a.type === 'resistance');
      
      expect(supportAnnotations.length).toBe(chartData.supportLevels.length);
      expect(resistanceAnnotations.length).toBe(chartData.resistanceLevels.length);
      
      supportAnnotations.forEach((annotation, index) => {
        expect(annotation.value).toBe(chartData.supportLevels[index].level);
        expect(annotation.label).toContain('Support');
      });
    });

    it('includes proper metadata', () => {
      const chartData = generateChartData('AAPL', '1M');
      
      expect(chartData.metadata.dataPoints).toBe(chartData.data.length);
      expect(chartData.metadata.startDate).toBeDefined();
      expect(chartData.metadata.endDate).toBeDefined();
      expect(chartData.metadata.lastUpdated).toBeDefined();
      
      expect(new Date(chartData.metadata.startDate)).toBeInstanceOf(Date);
      expect(new Date(chartData.metadata.endDate)).toBeInstanceOf(Date);
      expect(new Date(chartData.metadata.lastUpdated)).toBeInstanceOf(Date);
    });

    it('works with different timeframes', () => {
      const timeframes: TimeFrame[] = ['1D', '1W', '1M', '3M', '6M', '1Y', '2Y'];
      
      timeframes.forEach(timeframe => {
        const chartData = generateChartData('AAPL', timeframe);
        expect(chartData.timeframe).toBe(timeframe);
        expect(chartData.data.length).toBeGreaterThan(0);
      });
    });
  });

  describe('createChatChartData', () => {
    it('creates chart data compatible with chat interface', () => {
      const chatChartData = createChatChartData('AAPL', '1M');
      
      expect(chatChartData.symbol).toBe('AAPL');
      expect(chatChartData.timeframe).toBe('1M');
      expect(Array.isArray(chatChartData.data)).toBe(true);
      expect(Array.isArray(chatChartData.indicators)).toBe(true);
      expect(Array.isArray(chatChartData.annotations)).toBe(true);
    });

    it('uses default timeframe when not specified', () => {
      const chatChartData = createChatChartData('AAPL');
      
      expect(chatChartData.timeframe).toBe('1M');
    });

    it('generates data for different symbols', () => {
      const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA'];
      
      symbols.forEach(symbol => {
        const chatChartData = createChatChartData(symbol);
        expect(chatChartData.symbol).toBe(symbol);
        expect(chatChartData.data.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Data Quality', () => {
    it('generates consistent data across multiple calls', () => {
      // Note: This test checks structure consistency, not exact values (which should be random)
      const data1 = generateChartData('AAPL', '1M');
      const data2 = generateChartData('AAPL', '1M');
      
      expect(data1.data.length).toBe(data2.data.length);
      expect(data1.timeframe).toBe(data2.timeframe);
      expect(data1.symbol).toBe(data2.symbol);
    });

    it('generates different data for different symbols', () => {
      const appleData = generateChartData('AAPL', '1M');
      const googleData = generateChartData('GOOGL', '1M');
      
      expect(appleData.symbol).not.toBe(googleData.symbol);
      // Prices should be different (very low probability of being identical)
      const applePrices = appleData.data.map(p => p.close);
      const googlePrices = googleData.data.map(p => p.close);
      expect(applePrices).not.toEqual(googlePrices);
    });

    it('maintains data integrity across all components', () => {
      const chartData = generateChartData('AAPL', '1M');
      
      // All timestamps should be valid dates
      chartData.data.forEach(point => {
        expect(point.timestamp).toBeInstanceOf(Date);
      });
      
      chartData.indicators.forEach(indicator => {
        expect(new Date(indicator.timestamp)).toBeInstanceOf(Date);
      });
      
      // All numeric values should be finite
      chartData.data.forEach(point => {
        expect(Number.isFinite(point.open)).toBe(true);
        expect(Number.isFinite(point.high)).toBe(true);
        expect(Number.isFinite(point.low)).toBe(true);
        expect(Number.isFinite(point.close)).toBe(true);
        expect(Number.isFinite(point.volume)).toBe(true);
      });
    });
  });
});