/**
 * StockChart Component
 * 
 * Interactive price chart with technical indicators and annotations
 * Supports candlestick/OHLC charts with zoom, pan, and indicator toggles
 */

import React, { useState, useMemo, useRef, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  TimeScale,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  TooltipItem,
  InteractionItem,
  ChartEvent,
  BarElement,
  LineElement,
  PointElement,
} from 'chart.js';
import {
  CandlestickController,
  CandlestickElement,
  OhlcController,
  OhlcElement,
} from 'chartjs-chart-financial';
import zoomPlugin from 'chartjs-plugin-zoom';
import annotationPlugin from 'chartjs-plugin-annotation';

// Import date adapter conditionally to avoid Jest issues
let dateAdapter: any;
try {
  dateAdapter = require('chartjs-adapter-date-fns');
} catch (e) {
  // Ignore in test environment
}
import { Chart } from 'react-chartjs-2';
import { 
  ChartData, 
  PricePoint, 
  TechnicalIndicator, 
  ChartAnnotation, 
  TimeFrame,
  SupportResistanceLevel 
} from '../types';
import './StockChart.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  TimeScale,
  CandlestickController,
  CandlestickElement,
  OhlcController,
  OhlcElement,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  zoomPlugin,
  annotationPlugin
);

interface StockChartProps {
  symbol: string;
  data: PricePoint[];
  timeframe: TimeFrame;
  indicators?: TechnicalIndicator[];
  annotations?: ChartAnnotation[];
  supportLevels?: SupportResistanceLevel[];
  resistanceLevels?: SupportResistanceLevel[];
  onTimeframeChange?: (timeframe: TimeFrame) => void;
  className?: string;
  height?: number;
}

type ChartType = 'candlestick' | 'ohlc' | 'line';

interface IndicatorConfig {
  name: string;
  enabled: boolean;
  color: string;
  lineWidth: number;
  yAxisID?: string;
}

const StockChart: React.FC<StockChartProps> = ({
  symbol,
  data,
  timeframe,
  indicators = [],
  annotations = [],
  supportLevels = [],
  resistanceLevels = [],
  onTimeframeChange,
  className = '',
  height = 400,
}) => {
  const chartRef = useRef<ChartJS>(null);
  const [chartType, setChartType] = useState<ChartType>('candlestick');
  const [enabledIndicators, setEnabledIndicators] = useState<Record<string, boolean>>({
    sma20: false,
    sma50: false,
    ema12: false,
    ema26: false,
    rsi: false,
    macd: false,
    bollingerBands: false,
    volume: true,
  });
  const [showSupportResistance, setShowSupportResistance] = useState(true);
  const [isZoomed, setIsZoomed] = useState(false);

  // Available timeframes
  const timeframes: TimeFrame[] = ['1D', '1W', '1M', '3M', '6M', '1Y', '2Y'];

  // Process price data for Chart.js
  const processedData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    return data.map(point => ({
      x: point.timestamp,
      o: point.open,
      h: point.high,
      l: point.low,
      c: point.close,
      v: point.volume,
    }));
  }, [data]);

  // Create indicator datasets
  const indicatorDatasets = useMemo(() => {
    const datasets: any[] = [];

    // Moving Averages
    if (enabledIndicators.sma20) {
      const sma20Data = indicators
        .filter(ind => ind.name === 'SMA_20')
        .map(ind => ({ x: ind.timestamp, y: ind.value }));
      
      if (sma20Data.length > 0) {
        datasets.push({
          label: 'SMA 20',
          data: sma20Data,
          type: 'line',
          borderColor: '#3B82F6',
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 0,
          yAxisID: 'price',
        });
      }
    }

    if (enabledIndicators.sma50) {
      const sma50Data = indicators
        .filter(ind => ind.name === 'SMA_50')
        .map(ind => ({ x: ind.timestamp, y: ind.value }));
      
      if (sma50Data.length > 0) {
        datasets.push({
          label: 'SMA 50',
          data: sma50Data,
          type: 'line',
          borderColor: '#EF4444',
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 0,
          yAxisID: 'price',
        });
      }
    }

    if (enabledIndicators.ema12) {
      const ema12Data = indicators
        .filter(ind => ind.name === 'EMA_12')
        .map(ind => ({ x: ind.timestamp, y: ind.value }));
      
      if (ema12Data.length > 0) {
        datasets.push({
          label: 'EMA 12',
          data: ema12Data,
          type: 'line',
          borderColor: '#10B981',
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 0,
          yAxisID: 'price',
        });
      }
    }

    if (enabledIndicators.ema26) {
      const ema26Data = indicators
        .filter(ind => ind.name === 'EMA_26')
        .map(ind => ({ x: ind.timestamp, y: ind.value }));
      
      if (ema26Data.length > 0) {
        datasets.push({
          label: 'EMA 26',
          data: ema26Data,
          type: 'line',
          borderColor: '#F59E0B',
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 0,
          yAxisID: 'price',
        });
      }
    }

    // Bollinger Bands
    if (enabledIndicators.bollingerBands) {
      const upperBand = indicators
        .filter(ind => ind.name === 'BB_UPPER')
        .map(ind => ({ x: ind.timestamp, y: ind.value }));
      const lowerBand = indicators
        .filter(ind => ind.name === 'BB_LOWER')
        .map(ind => ({ x: ind.timestamp, y: ind.value }));
      
      if (upperBand.length > 0 && lowerBand.length > 0) {
        datasets.push({
          label: 'Bollinger Upper',
          data: upperBand,
          type: 'line',
          borderColor: '#8B5CF6',
          backgroundColor: 'transparent',
          borderWidth: 1,
          borderDash: [5, 5],
          pointRadius: 0,
          yAxisID: 'price',
        });
        
        datasets.push({
          label: 'Bollinger Lower',
          data: lowerBand,
          type: 'line',
          borderColor: '#8B5CF6',
          backgroundColor: 'transparent',
          borderWidth: 1,
          borderDash: [5, 5],
          pointRadius: 0,
          yAxisID: 'price',
          fill: '-1',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
        });
      }
    }

    // Volume
    if (enabledIndicators.volume) {
      const volumeData = processedData.map(point => ({
        x: point.x,
        y: point.v,
      }));
      
      datasets.push({
        label: 'Volume',
        data: volumeData,
        type: 'bar',
        backgroundColor: 'rgba(107, 114, 128, 0.3)',
        borderColor: 'rgba(107, 114, 128, 0.5)',
        borderWidth: 1,
        yAxisID: 'volume',
      });
    }

    return datasets;
  }, [indicators, enabledIndicators, processedData]);

  // Create support/resistance annotations
  const annotationLines = useMemo(() => {
    const lines: any[] = [];

    if (showSupportResistance) {
      // Support levels
      supportLevels.forEach((level, index) => {
        lines.push({
          type: 'line',
          yMin: level.level,
          yMax: level.level,
          borderColor: '#10B981',
          borderWidth: 2,
          borderDash: [10, 5],
          label: {
            content: `Support: $${level.level.toFixed(2)}`,
            enabled: true,
            position: 'end',
          },
        });
      });

      // Resistance levels
      resistanceLevels.forEach((level, index) => {
        lines.push({
          type: 'line',
          yMin: level.level,
          yMax: level.level,
          borderColor: '#EF4444',
          borderWidth: 2,
          borderDash: [10, 5],
          label: {
            content: `Resistance: $${level.level.toFixed(2)}`,
            enabled: true,
            position: 'end',
          },
        });
      });
    }

    return lines;
  }, [supportLevels, resistanceLevels, showSupportResistance]);

  // Chart configuration
  const chartData = {
    datasets: [
      {
        label: symbol,
        data: processedData,
        type: chartType,
        borderColor: '#1F2937',
        backgroundColor: (ctx: any) => {
          const point = ctx.parsed;
          return point && point.c >= point.o ? '#10B981' : '#EF4444';
        },
        borderWidth: 1,
        yAxisID: 'price',
      },
      ...indicatorDatasets,
    ],
  };

  const chartOptions: ChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: 'index',
    },
    plugins: {
      title: {
        display: true,
        text: `${symbol} - ${timeframe}`,
        font: {
          size: 16,
          weight: 'bold',
        },
      },
      legend: {
        display: true,
        position: 'top',
        labels: {
          filter: (legendItem) => {
            return legendItem.text !== symbol; // Hide main dataset from legend
          },
        },
      },
      tooltip: {
        callbacks: {
          title: (tooltipItems: TooltipItem<any>[]) => {
            if (tooltipItems.length > 0) {
              const date = new Date(tooltipItems[0].parsed.x);
              return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            }
            return '';
          },
          label: (context: TooltipItem<any>) => {
            const point = context.parsed;
            if (context.dataset.label === symbol) {
              return [
                `Open: $${point.o?.toFixed(2)}`,
                `High: $${point.h?.toFixed(2)}`,
                `Low: $${point.l?.toFixed(2)}`,
                `Close: $${point.c?.toFixed(2)}`,
                `Volume: ${point.v?.toLocaleString()}`,
              ];
            }
            return `${context.dataset.label}: ${point.y?.toFixed(2)}`;
          },
        },
      },
      zoom: {
        pan: {
          enabled: true,
          mode: 'x',
          onPanComplete: () => setIsZoomed(true),
        },
        zoom: {
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true,
          },
          mode: 'x',
          onZoomComplete: () => setIsZoomed(true),
        },
      },
      annotation: {
        annotations: annotationLines,
      },
    },
    scales: {
      x: {
        type: 'time',
        time: {
          displayFormats: {
            day: 'MMM dd',
            week: 'MMM dd',
            month: 'MMM yyyy',
          },
        },
        title: {
          display: true,
          text: 'Date',
        },
      },
      price: {
        type: 'linear',
        position: 'left',
        title: {
          display: true,
          text: 'Price ($)',
        },
        ticks: {
          callback: (value: any) => `$${value.toFixed(2)}`,
        },
      },
      volume: {
        type: 'linear',
        position: 'right',
        display: enabledIndicators.volume,
        title: {
          display: enabledIndicators.volume,
          text: 'Volume',
        },
        ticks: {
          callback: (value: any) => {
            if (value >= 1000000) {
              return `${(value / 1000000).toFixed(1)}M`;
            } else if (value >= 1000) {
              return `${(value / 1000).toFixed(1)}K`;
            }
            return value.toString();
          },
        },
        grid: {
          display: false,
        },
      },
    },
  };

  // Reset zoom function
  const resetZoom = () => {
    if (chartRef.current) {
      chartRef.current.resetZoom();
      setIsZoomed(false);
    }
  };

  // Toggle indicator
  const toggleIndicator = (indicator: string) => {
    setEnabledIndicators(prev => ({
      ...prev,
      [indicator]: !prev[indicator],
    }));
  };

  return (
    <div className={`stock-chart ${className}`}>
      {/* Chart Controls */}
      <div className="chart-controls mb-4 space-y-3">
        {/* Timeframe Selector */}
        <div className="flex flex-wrap gap-2">
          <span className="text-sm font-medium text-gray-700 mr-2">Timeframe:</span>
          {timeframes.map((tf) => (
            <button
              key={tf}
              onClick={() => onTimeframeChange?.(tf)}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                timeframe === tf
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>

        {/* Chart Type Selector */}
        <div className="flex flex-wrap gap-2">
          <span className="text-sm font-medium text-gray-700 mr-2">Chart Type:</span>
          {(['candlestick', 'ohlc', 'line'] as ChartType[]).map((type) => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              className={`px-3 py-1 text-sm rounded-md transition-colors capitalize ${
                chartType === type
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {type}
            </button>
          ))}
        </div>

        {/* Technical Indicators */}
        <div className="flex flex-wrap gap-2">
          <span className="text-sm font-medium text-gray-700 mr-2">Indicators:</span>
          {Object.entries(enabledIndicators).map(([key, enabled]) => (
            <button
              key={key}
              onClick={() => toggleIndicator(key)}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                enabled
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
            </button>
          ))}
        </div>

        {/* Additional Controls */}
        <div className="flex flex-wrap gap-2 items-center">
          <button
            onClick={() => setShowSupportResistance(!showSupportResistance)}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              showSupportResistance
                ? 'bg-orange-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Support/Resistance
          </button>
          
          {isZoomed && (
            <button
              onClick={resetZoom}
              className="px-3 py-1 text-sm rounded-md bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
            >
              Reset Zoom
            </button>
          )}
        </div>
      </div>

      {/* Chart Container */}
      <div 
        className="chart-container bg-white rounded-lg border border-gray-200 p-4"
        style={{ height: `${height}px` }}
      >
        {processedData.length > 0 ? (
          <Chart
            ref={chartRef}
            type={chartType as any}
            data={chartData}
            options={chartOptions}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <div className="text-lg font-medium">No chart data available</div>
              <div className="text-sm">Unable to load price data for {symbol}</div>
            </div>
          </div>
        )}
      </div>

      {/* Chart Info */}
      <div className="chart-info mt-2 text-xs text-gray-500 space-y-1">
        <div>
          Data points: {processedData.length} | 
          Indicators: {Object.values(enabledIndicators).filter(Boolean).length} active |
          Support/Resistance: {showSupportResistance ? 'Visible' : 'Hidden'}
        </div>
        <div>
          Use mouse wheel to zoom, drag to pan. Click "Reset Zoom" to return to full view.
        </div>
      </div>
    </div>
  );
};

export default StockChart;