/**
 * StockChart Component Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import StockChart from '../StockChart';
import { PricePoint, TechnicalIndicator, ChartAnnotation, SupportResistanceLevel } from '../../types';
import { generateMockPriceData, generateMockIndicators } from '../../services/chartService';

// Mocks are handled in setupTests.ts

describe('StockChart Component', () => {
  const mockPriceData: PricePoint[] = generateMockPriceData('AAPL', '1M', 30);
  const mockIndicators: TechnicalIndicator[] = generateMockIndicators(mockPriceData, 'AAPL');
  
  const mockAnnotations: ChartAnnotation[] = [
    {
      type: 'support',
      value: 150.0,
      label: 'Support: $150.00',
    },
    {
      type: 'resistance',
      value: 180.0,
      label: 'Resistance: $180.00',
    },
  ];

  const mockSupportLevels: SupportResistanceLevel[] = [
    {
      level: 150.0,
      strength: 7,
      type: 'support',
      touches: 3,
      lastTouch: '2024-01-15T10:30:00Z',
    },
  ];

  const mockResistanceLevels: SupportResistanceLevel[] = [
    {
      level: 180.0,
      strength: 5,
      type: 'resistance',
      touches: 2,
      lastTouch: '2024-01-20T14:15:00Z',
    },
  ];

  const defaultProps = {
    symbol: 'AAPL',
    data: mockPriceData,
    timeframe: '1M' as const,
    indicators: mockIndicators,
    annotations: mockAnnotations,
    supportLevels: mockSupportLevels,
    resistanceLevels: mockResistanceLevels,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders the stock chart with basic elements', () => {
      render(<StockChart {...defaultProps} />);
      
      expect(screen.getByTestId('mock-chart')).toBeInTheDocument();
      expect(screen.getByText('Timeframe:')).toBeInTheDocument();
      expect(screen.getByText('Chart Type:')).toBeInTheDocument();
      expect(screen.getByText('Indicators:')).toBeInTheDocument();
    });

    it('displays the correct symbol in chart title', () => {
      render(<StockChart {...defaultProps} />);
      
      const chartOptions = JSON.parse(screen.getByTestId('chart-options').textContent || '{}');
      expect(chartOptions.plugins?.title?.text).toContain('AAPL');
    });

    it('renders timeframe selector buttons', () => {
      render(<StockChart {...defaultProps} />);
      
      const timeframes = ['1D', '1W', '1M', '3M', '6M', '1Y', '2Y'];
      timeframes.forEach(timeframe => {
        expect(screen.getByRole('button', { name: timeframe })).toBeInTheDocument();
      });
    });

    it('renders chart type selector buttons', () => {
      render(<StockChart {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: 'candlestick' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'ohlc' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'line' })).toBeInTheDocument();
    });

    it('renders technical indicator toggle buttons', () => {
      render(<StockChart {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: /sma20/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sma50/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /ema12/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /volume/i })).toBeInTheDocument();
    });

    it('shows chart info with data points count', () => {
      render(<StockChart {...defaultProps} />);
      
      expect(screen.getByText(/Data points: \d+/)).toBeInTheDocument();
      expect(screen.getByText(/Indicators: \d+ active/)).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('calls onTimeframeChange when timeframe button is clicked', async () => {
      const user = userEvent.setup();
      const mockOnTimeframeChange = jest.fn();
      
      render(
        <StockChart 
          {...defaultProps} 
          onTimeframeChange={mockOnTimeframeChange}
        />
      );
      
      await user.click(screen.getByRole('button', { name: '1Y' }));
      
      expect(mockOnTimeframeChange).toHaveBeenCalledWith('1Y');
    });

    it('changes chart type when chart type button is clicked', async () => {
      const user = userEvent.setup();
      
      render(<StockChart {...defaultProps} />);
      
      await user.click(screen.getByRole('button', { name: 'ohlc' }));
      
      await waitFor(() => {
        expect(screen.getByTestId('mock-chart')).toHaveAttribute('data-chart-type', 'ohlc');
      });
    });

    it('toggles technical indicators when indicator buttons are clicked', async () => {
      const user = userEvent.setup();
      
      render(<StockChart {...defaultProps} />);
      
      const sma20Button = screen.getByRole('button', { name: /sma20/i });
      
      // Initially should not be active (gray background)
      expect(sma20Button).toHaveClass('bg-gray-100');
      
      await user.click(sma20Button);
      
      // Should become active (purple background)
      await waitFor(() => {
        expect(sma20Button).toHaveClass('bg-purple-600');
      });
    });

    it('toggles support/resistance visibility', async () => {
      const user = userEvent.setup();
      
      render(<StockChart {...defaultProps} />);
      
      const supportResistanceButton = screen.getByRole('button', { name: 'Support/Resistance' });
      
      // Initially should be active (orange background)
      expect(supportResistanceButton).toHaveClass('bg-orange-600');
      
      await user.click(supportResistanceButton);
      
      // Should become inactive (gray background)
      await waitFor(() => {
        expect(supportResistanceButton).toHaveClass('bg-gray-100');
      });
    });
  });

  describe('Chart Data Processing', () => {
    it('processes price data correctly for Chart.js', () => {
      render(<StockChart {...defaultProps} />);
      
      const chartData = JSON.parse(screen.getByTestId('chart-data').textContent || '{}');
      const mainDataset = chartData.datasets[0];
      
      expect(mainDataset.label).toBe('AAPL');
      expect(mainDataset.data).toHaveLength(mockPriceData.length);
      expect(mainDataset.data[0]).toHaveProperty('x');
      expect(mainDataset.data[0]).toHaveProperty('o');
      expect(mainDataset.data[0]).toHaveProperty('h');
      expect(mainDataset.data[0]).toHaveProperty('l');
      expect(mainDataset.data[0]).toHaveProperty('c');
    });

    it('includes indicator datasets when indicators are enabled', async () => {
      const user = userEvent.setup();
      
      render(<StockChart {...defaultProps} />);
      
      // Enable SMA 20 indicator
      await user.click(screen.getByRole('button', { name: /sma20/i }));
      
      await waitFor(() => {
        const chartData = JSON.parse(screen.getByTestId('chart-data').textContent || '{}');
        const indicatorDataset = chartData.datasets.find((ds: any) => ds.label === 'SMA 20');
        expect(indicatorDataset).toBeDefined();
      });
    });

    it('includes volume dataset when volume is enabled', () => {
      render(<StockChart {...defaultProps} />);
      
      const chartData = JSON.parse(screen.getByTestId('chart-data').textContent || '{}');
      const volumeDataset = chartData.datasets.find((ds: any) => ds.label === 'Volume');
      
      expect(volumeDataset).toBeDefined();
      expect(volumeDataset.type).toBe('bar');
      expect(volumeDataset.yAxisID).toBe('volume');
    });
  });

  describe('Chart Configuration', () => {
    it('renders chart controls correctly', () => {
      render(<StockChart {...defaultProps} />);
      
      expect(screen.getByText('Timeframe:')).toBeInTheDocument();
      expect(screen.getByText('Chart Type:')).toBeInTheDocument();
      expect(screen.getByText('Indicators:')).toBeInTheDocument();
    });

    it('shows data points information', () => {
      render(<StockChart {...defaultProps} />);
      
      expect(screen.getByText(/Data points: \d+/)).toBeInTheDocument();
      expect(screen.getByText(/Indicators: \d+ active/)).toBeInTheDocument();
    });

    it('renders chart container with correct height', () => {
      render(<StockChart {...defaultProps} />);
      
      const chartContainer = document.querySelector('.chart-container');
      expect(chartContainer).toBeInTheDocument();
      expect(chartContainer).toHaveStyle('height: 400px');
    });
  });

  describe('Error Handling', () => {
    it('displays no data message when price data is empty', () => {
      render(<StockChart {...defaultProps} data={[]} />);
      
      expect(screen.getByText('No chart data available')).toBeInTheDocument();
      expect(screen.getByText('Unable to load price data for AAPL')).toBeInTheDocument();
    });

    it('handles missing indicators gracefully', () => {
      render(<StockChart {...defaultProps} indicators={[]} />);
      
      // Should render the chart controls
      expect(screen.getByText('Indicators:')).toBeInTheDocument();
      expect(screen.getByText(/Data points: \d+/)).toBeInTheDocument();
    });

    it('handles missing annotations gracefully', () => {
      render(<StockChart {...defaultProps} annotations={[]} />);
      
      // Should render the chart controls
      expect(screen.getByText('Chart Type:')).toBeInTheDocument();
      expect(screen.getByText(/Data points: \d+/)).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('applies custom height when provided', () => {
      render(<StockChart {...defaultProps} height={500} />);
      
      const chartContainer = document.querySelector('.chart-container');
      expect(chartContainer).toHaveStyle('height: 500px');
    });

    it('applies custom className when provided', () => {
      render(<StockChart {...defaultProps} className="custom-chart" />);
      
      const stockChart = document.querySelector('.stock-chart');
      expect(stockChart).toHaveClass('custom-chart');
    });
  });

  describe('Accessibility', () => {
    it('provides accessible button labels', () => {
      render(<StockChart {...defaultProps} />);
      
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveAccessibleName();
      });
    });

    it('provides chart information for screen readers', () => {
      render(<StockChart {...defaultProps} />);
      
      expect(screen.getByText(/Data points:/)).toBeInTheDocument();
      expect(screen.getByText(/Use mouse wheel to zoom/)).toBeInTheDocument();
    });
  });
});