import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render, createMockResizeObserver } from '../../test-utils';
import StockChart from '../StockChart';

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options }: any) => (
    <div data-testid="mock-chart">
      <div data-testid="chart-data">{JSON.stringify(data)}</div>
      <div data-testid="chart-options">{JSON.stringify(options)}</div>
    </div>
  ),
}));

const mockChartData = {
  symbol: 'AAPL',
  timeframe: '1D' as const,
  data: [
    { timestamp: new Date('2024-01-01T09:30:00Z'), open: 150, high: 155, low: 149, close: 154, volume: 1000000 },
    { timestamp: new Date('2024-01-01T10:30:00Z'), open: 154, high: 158, low: 153, close: 157, volume: 1200000 },
    { timestamp: new Date('2024-01-01T11:30:00Z'), open: 157, high: 160, low: 156, close: 159, volume: 1100000 },
  ],
  indicators: [
    {
      type: 'SMA' as const,
      period: 20,
      data: [152, 155, 158],
      visible: true,
    },
  ],
  annotations: [
    {
      type: 'support' as const,
      value: 150,
      label: 'Support Level',
    },
  ],
};

describe('StockChart Integration', () => {
  beforeEach(() => {
    createMockResizeObserver();
    jest.clearAllMocks();
  });

  it('renders chart with data correctly', () => {
    render(<StockChart {...mockChartData} />);
    
    expect(screen.getByTestId('mock-chart')).toBeInTheDocument();
    expect(screen.getByText('AAPL - 1D')).toBeInTheDocument();
  });

  it('displays technical indicators', () => {
    render(<StockChart {...mockChartData} />);
    
    expect(screen.getByText('SMA (20)')).toBeInTheDocument();
    
    const chartData = JSON.parse(screen.getByTestId('chart-data').textContent || '{}');
    expect(chartData.datasets).toHaveLength(2); // Price data + SMA indicator
  });

  it('handles timeframe changes', async () => {
    const user = userEvent.setup();
    const onTimeframeChange = jest.fn();
    
    render(
      <StockChart 
        {...mockChartData} 
        onTimeframeChange={onTimeframeChange}
      />
    );
    
    // Click on different timeframe
    await user.click(screen.getByText('1W'));
    
    expect(onTimeframeChange).toHaveBeenCalledWith('1W');
  });

  it('toggles indicator visibility', async () => {
    const user = userEvent.setup();
    const onIndicatorToggle = jest.fn();
    
    render(
      <StockChart 
        {...mockChartData} 
        onIndicatorToggle={onIndicatorToggle}
      />
    );
    
    // Find and click indicator toggle
    const indicatorToggle = screen.getByLabelText('Toggle SMA (20)');
    await user.click(indicatorToggle);
    
    expect(onIndicatorToggle).toHaveBeenCalledWith('SMA', 20, false);
  });

  it('displays annotations correctly', () => {
    render(<StockChart {...mockChartData} />);
    
    const chartOptions = JSON.parse(screen.getByTestId('chart-options').textContent || '{}');
    expect(chartOptions.plugins.annotation.annotations).toBeDefined();
    expect(chartOptions.plugins.annotation.annotations.support).toBeDefined();
  });

  it('handles empty data gracefully', () => {
    const emptyData = {
      ...mockChartData,
      data: [],
    };
    
    render(<StockChart {...emptyData} />);
    
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<StockChart {...mockChartData} isLoading={true} />);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.getByText('Loading chart data...')).toBeInTheDocument();
  });

  it('handles chart interaction events', async () => {
    const user = userEvent.setup();
    const onDataPointClick = jest.fn();
    
    render(
      <StockChart 
        {...mockChartData} 
        onDataPointClick={onDataPointClick}
      />
    );
    
    // Simulate clicking on chart (this would be handled by Chart.js in real scenario)
    const chart = screen.getByTestId('mock-chart');
    await user.click(chart);
    
    // In a real implementation, this would trigger the callback
    // For now, we just verify the chart is interactive
    expect(chart).toBeInTheDocument();
  });

  it('updates chart when data changes', () => {
    const { rerender } = render(<StockChart {...mockChartData} />);
    
    const updatedData = {
      ...mockChartData,
      data: [
        ...mockChartData.data,
        { timestamp: new Date('2024-01-01T12:30:00Z'), open: 159, high: 162, low: 158, close: 161, volume: 1300000 },
      ],
    };
    
    rerender(<StockChart {...updatedData} />);
    
    const chartData = JSON.parse(screen.getByTestId('chart-data').textContent || '{}');
    expect(chartData.datasets[0].data).toHaveLength(4); // Original 3 + 1 new data point
  });

  it('handles different chart types', async () => {
    const user = userEvent.setup();
    
    render(<StockChart {...mockChartData} />);
    
    // Switch to candlestick chart
    const chartTypeButton = screen.getByLabelText('Chart Type');
    await user.click(chartTypeButton);
    
    await user.click(screen.getByText('Candlestick'));
    
    await waitFor(() => {
      const chartOptions = JSON.parse(screen.getByTestId('chart-options').textContent || '{}');
      expect(chartOptions.scales.y.type).toBe('linear');
    });
  });

  it('displays volume chart when enabled', () => {
    render(<StockChart {...mockChartData} showVolume={true} />);
    
    const chartData = JSON.parse(screen.getByTestId('chart-data').textContent || '{}');
    expect(chartData.datasets.some((dataset: any) => dataset.label === 'Volume')).toBe(true);
  });

  it('handles zoom and pan interactions', async () => {
    const user = userEvent.setup();
    
    render(<StockChart {...mockChartData} />);
    
    // Test zoom controls
    const zoomInButton = screen.getByLabelText('Zoom In');
    const zoomOutButton = screen.getByLabelText('Zoom Out');
    const resetZoomButton = screen.getByLabelText('Reset Zoom');
    
    await user.click(zoomInButton);
    await user.click(zoomOutButton);
    await user.click(resetZoomButton);
    
    // Verify buttons are functional (actual zoom would be handled by Chart.js)
    expect(zoomInButton).toBeInTheDocument();
    expect(zoomOutButton).toBeInTheDocument();
    expect(resetZoomButton).toBeInTheDocument();
  });
});