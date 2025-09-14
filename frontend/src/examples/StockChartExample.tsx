/**
 * StockChart Integration Example
 * 
 * Demonstrates how to use the StockChart component with mock data
 */

import React, { useState } from 'react';
import StockChart from '../components/StockChart';
import { createChatChartData } from '../services/chartService';
import { TimeFrame } from '../types';

const StockChartExample: React.FC = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [timeframe, setTimeframe] = useState<TimeFrame>('1M');
  
  // Generate chart data
  const chartData = createChatChartData(symbol, timeframe);
  
  const handleTimeframeChange = (newTimeframe: TimeFrame) => {
    setTimeframe(newTimeframe);
  };
  
  const handleSymbolChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSymbol(event.target.value.toUpperCase());
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Interactive Stock Chart Example</h1>
      
      {/* Symbol Input */}
      <div className="mb-6">
        <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 mb-2">
          Stock Symbol:
        </label>
        <input
          id="symbol"
          type="text"
          value={symbol}
          onChange={handleSymbolChange}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter stock symbol (e.g., AAPL)"
        />
      </div>
      
      {/* Chart Component */}
      <StockChart
        symbol={symbol}
        data={chartData.data}
        timeframe={timeframe}
        indicators={chartData.indicators}
        annotations={chartData.annotations}
        onTimeframeChange={handleTimeframeChange}
        height={500}
        className="mb-6"
      />
      
      {/* Usage Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h2 className="text-lg font-semibold text-blue-900 mb-2">How to Use:</h2>
        <ul className="text-blue-800 space-y-1">
          <li>• Change the stock symbol in the input above</li>
          <li>• Click different timeframe buttons to see different data ranges</li>
          <li>• Toggle technical indicators on/off using the indicator buttons</li>
          <li>• Switch between candlestick, OHLC, and line chart types</li>
          <li>• Use mouse wheel to zoom and drag to pan the chart</li>
          <li>• Toggle support/resistance levels visibility</li>
        </ul>
      </div>
      
      {/* Integration Example */}
      <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Chat Integration Example:</h2>
        <pre className="text-sm text-gray-700 overflow-x-auto">
{`// In ChatMessage component, add chart rendering:
{message.metadata?.charts && message.metadata.charts.length > 0 && (
  <Box sx={{ mt: 2 }}>
    {message.metadata.charts.map((chartData, index) => (
      <StockChart
        key={index}
        symbol={chartData.symbol}
        data={chartData.data}
        timeframe={chartData.timeframe}
        indicators={chartData.indicators}
        annotations={chartData.annotations}
        height={350}
      />
    ))}
  </Box>
)}

// To add chart data to a chat message:
const chartData = createChatChartData(symbol, timeframe);
const message: ChatMessage = {
  id: generateId(),
  type: 'assistant',
  content: 'Here is the price chart for ' + symbol,
  timestamp: new Date(),
  metadata: {
    stockSymbol: symbol,
    charts: [chartData]
  }
};`}
        </pre>
      </div>
    </div>
  );
};

export default StockChartExample;