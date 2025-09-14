/**
 * Tests for EarningsImpactAnalysis component.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import EarningsImpactAnalysisComponent from '../EarningsImpactAnalysis';
import { earningsService } from '../../services/earnings';
import {
  EarningsImpactAnalysis,
  EarningsEvent,
  EarningsHistoricalPerformance,
  EventImpact,
  EarningsConfidence
} from '../../types/earnings';

// Mock the earnings service
jest.mock('../../services/earnings');
const mockEarningsService = earningsService as jest.Mocked<typeof earningsService>;

// Mock CSS import
jest.mock('../EarningsImpactAnalysis.css', () => ({}));

describe('EarningsImpactAnalysis', () => {
  const mockUpcomingEarnings: EarningsEvent = {
    id: 1,
    symbol: 'AAPL',
    company_name: 'Apple Inc.',
    earnings_date: '2024-02-01T16:00:00Z',
    report_time: 'AMC',
    fiscal_quarter: 'Q1',
    fiscal_year: 2024,
    eps_estimate: 1.50,
    revenue_estimate: 90000000000,
    confidence: EarningsConfidence.HIGH,
    impact_level: EventImpact.HIGH,
    is_confirmed: true,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    days_until_earnings: 7,
    is_upcoming: true,
    has_estimates: true,
    has_actuals: false
  };

  const mockHistoricalPerformance: EarningsHistoricalPerformance[] = [
    {
      id: 1,
      symbol: 'AAPL',
      price_before_earnings: 150.00,
      price_after_earnings: 155.00,
      price_change_1d: 3.33,
      price_change_1w: 2.50,
      price_change_1m: 1.80,
      volume_before: 50000000,
      volume_after: 75000000,
      volume_change: 50.00,
      beat_estimate: true,
      surprise_magnitude: 0.05,
      created_at: '2024-01-01T10:00:00Z'
    },
    {
      id: 2,
      symbol: 'AAPL',
      price_before_earnings: 145.00,
      price_after_earnings: 142.00,
      price_change_1d: -2.07,
      price_change_1w: -1.50,
      price_change_1m: 0.50,
      volume_before: 45000000,
      volume_after: 80000000,
      volume_change: 77.78,
      beat_estimate: false,
      surprise_magnitude: -0.03,
      created_at: '2023-10-01T10:00:00Z'
    }
  ];

  const mockAnalysis: EarningsImpactAnalysis = {
    symbol: 'AAPL',
    upcoming_earnings: mockUpcomingEarnings,
    historical_performance: mockHistoricalPerformance,
    avg_price_change_1d: 0.63,
    avg_price_change_1w: 0.50,
    avg_volume_change: 63.89,
    beat_rate: 50.0,
    volatility_increase: 2.70,
    expected_volatility: 'medium',
    risk_level: 'medium',
    key_metrics_to_watch: ['EPS', 'Revenue', 'Guidance', 'Trading Volume']
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockEarningsService.getEarningsImpactAnalysis.mockResolvedValue(mockAnalysis);
  });

  it('renders analysis for given symbol', async () => {
    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    expect(screen.getByText('Earnings Impact Analysis - AAPL')).toBeInTheDocument();

    await waitFor(() => {
      expect(mockEarningsService.getEarningsImpactAnalysis).toHaveBeenCalledWith('AAPL');
    });
  });

  it('displays upcoming earnings information', async () => {
    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText('Upcoming Earnings')).toBeInTheDocument();
      expect(screen.getByText('After Market Close')).toBeInTheDocument();
      expect(screen.getByText('Q1 2024')).toBeInTheDocument();
      expect(screen.getByText('In 7 days')).toBeInTheDocument();
      expect(screen.getByText('$1.50')).toBeInTheDocument();
      expect(screen.getByText('$90.00B')).toBeInTheDocument();
    });
  });

  it('displays analysis metrics correctly', async () => {
    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText('Analysis Metrics')).toBeInTheDocument();
      expect(screen.getByText('+0.63%')).toBeInTheDocument(); // avg_price_change_1d
      expect(screen.getByText('+0.50%')).toBeInTheDocument(); // avg_price_change_1w
      expect(screen.getByText('50%')).toBeInTheDocument(); // beat_rate
      expect(screen.getByText('+63.89%')).toBeInTheDocument(); // avg_volume_change
    });
  });

  it('displays predictions correctly', async () => {
    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText('Earnings Predictions')).toBeInTheDocument();
      expect(screen.getByText('MEDIUM')).toBeInTheDocument(); // expected_volatility
      expect(screen.getByText('MEDIUM')).toBeInTheDocument(); // risk_level
      expect(screen.getByText('+2.70%')).toBeInTheDocument(); // volatility_increase
    });
  });

  it('displays key metrics to watch', async () => {
    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText('Key Metrics to Watch')).toBeInTheDocument();
      expect(screen.getByText('EPS')).toBeInTheDocument();
      expect(screen.getByText('Revenue')).toBeInTheDocument();
      expect(screen.getByText('Guidance')).toBeInTheDocument();
      expect(screen.getByText('Trading Volume')).toBeInTheDocument();
    });
  });

  it('displays historical performance data', async () => {
    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText('Historical Earnings Performance')).toBeInTheDocument();
      expect(screen.getByText('2 past earnings')).toBeInTheDocument();
      
      // Check first historical performance
      expect(screen.getByText('+3.33%')).toBeInTheDocument(); // price_change_1d
      expect(screen.getByText('+2.50%')).toBeInTheDocument(); // price_change_1w
      expect(screen.getByText('Yes')).toBeInTheDocument(); // beat_estimate
      expect(screen.getByText('$0.05')).toBeInTheDocument(); // surprise_magnitude
      
      // Check second historical performance
      expect(screen.getByText('-2.07%')).toBeInTheDocument(); // price_change_1d
      expect(screen.getByText('-1.50%')).toBeInTheDocument(); // price_change_1w
      expect(screen.getByText('No')).toBeInTheDocument(); // beat_estimate
      expect(screen.getByText('$-0.03')).toBeInTheDocument(); // surprise_magnitude
    });
  });

  it('handles refresh button click', async () => {
    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(mockEarningsService.getEarningsImpactAnalysis).toHaveBeenCalledTimes(1);
    });

    const refreshButton = screen.getByText('🔄 Refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(mockEarningsService.getEarningsImpactAnalysis).toHaveBeenCalledTimes(2);
    });
  });

  it('calls onAnalysisUpdate callback when analysis is loaded', async () => {
    const onAnalysisUpdate = jest.fn();
    render(
      <EarningsImpactAnalysisComponent 
        symbol="AAPL" 
        onAnalysisUpdate={onAnalysisUpdate} 
      />
    );

    await waitFor(() => {
      expect(onAnalysisUpdate).toHaveBeenCalledWith(mockAnalysis);
    });
  });

  it('displays loading state', () => {
    mockEarningsService.getEarningsImpactAnalysis.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    expect(screen.getByText('Loading earnings impact analysis...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { hidden: true })).toBeInTheDocument();
  });

  it('displays error state', async () => {
    const errorMessage = 'Failed to fetch analysis';
    mockEarningsService.getEarningsImpactAnalysis.mockRejectedValue(
      new Error(errorMessage)
    );

    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  it('handles retry on error', async () => {
    const errorMessage = 'Network error';
    mockEarningsService.getEarningsImpactAnalysis
      .mockRejectedValueOnce(new Error(errorMessage))
      .mockResolvedValueOnce(mockAnalysis);

    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('Upcoming Earnings')).toBeInTheDocument();
    });
  });

  it('displays empty state when no analysis available', async () => {
    mockEarningsService.getEarningsImpactAnalysis.mockResolvedValue(null as any);

    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText('No earnings impact analysis available for AAPL')).toBeInTheDocument();
    });
  });

  it('handles analysis without upcoming earnings', async () => {
    const analysisWithoutUpcoming = {
      ...mockAnalysis,
      upcoming_earnings: undefined
    };
    mockEarningsService.getEarningsImpactAnalysis.mockResolvedValue(analysisWithoutUpcoming);

    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.queryByText('Upcoming Earnings')).not.toBeInTheDocument();
      expect(screen.getByText('Analysis Metrics')).toBeInTheDocument();
    });
  });

  it('handles analysis without historical performance', async () => {
    const analysisWithoutHistory = {
      ...mockAnalysis,
      historical_performance: []
    };
    mockEarningsService.getEarningsImpactAnalysis.mockResolvedValue(analysisWithoutHistory);

    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.queryByText('Historical Earnings Performance')).not.toBeInTheDocument();
      expect(screen.getByText('Analysis Metrics')).toBeInTheDocument();
    });
  });

  it('formats percentage values correctly', async () => {
    const analysisWithNegativeValues = {
      ...mockAnalysis,
      avg_price_change_1d: -1.25,
      avg_price_change_1w: -0.75
    };
    mockEarningsService.getEarningsImpactAnalysis.mockResolvedValue(analysisWithNegativeValues);

    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText('-1.25%')).toBeInTheDocument();
      expect(screen.getByText('-0.75%')).toBeInTheDocument();
    });
  });

  it('handles null/undefined metric values', async () => {
    const analysisWithNullValues = {
      ...mockAnalysis,
      avg_price_change_1d: undefined,
      beat_rate: null,
      expected_volatility: undefined
    };
    mockEarningsService.getEarningsImpactAnalysis.mockResolvedValue(analysisWithNullValues);

    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText('N/A')).toBeInTheDocument();
      expect(screen.getByText('UNKNOWN')).toBeInTheDocument();
    });
  });

  it('displays show more button when there are many historical performances', async () => {
    const manyHistoricalPerformances = Array.from({ length: 10 }, (_, i) => ({
      ...mockHistoricalPerformance[0],
      id: i + 1,
      created_at: `2024-0${(i % 9) + 1}-01T10:00:00Z`
    }));

    const analysisWithManyHistory = {
      ...mockAnalysis,
      historical_performance: manyHistoricalPerformances
    };
    mockEarningsService.getEarningsImpactAnalysis.mockResolvedValue(analysisWithManyHistory);

    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText('Show 5 more earnings')).toBeInTheDocument();
    });
  });

  it('updates analysis when symbol prop changes', async () => {
    const { rerender } = render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(mockEarningsService.getEarningsImpactAnalysis).toHaveBeenCalledWith('AAPL');
    });

    rerender(<EarningsImpactAnalysisComponent symbol="GOOGL" />);

    await waitFor(() => {
      expect(mockEarningsService.getEarningsImpactAnalysis).toHaveBeenCalledWith('GOOGL');
    });
  });

  it('applies correct color styling for risk levels', async () => {
    const highRiskAnalysis = {
      ...mockAnalysis,
      risk_level: 'high',
      expected_volatility: 'high'
    };
    mockEarningsService.getEarningsImpactAnalysis.mockResolvedValue(highRiskAnalysis);

    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      const riskElement = screen.getByText('HIGH');
      expect(riskElement).toHaveStyle({ color: '#ef4444' }); // High risk color
    });
  });

  it('handles earnings with different report times', async () => {
    const bmoEarnings = {
      ...mockUpcomingEarnings,
      report_time: 'BMO'
    };
    const analysisWithBMO = {
      ...mockAnalysis,
      upcoming_earnings: bmoEarnings
    };
    mockEarningsService.getEarningsImpactAnalysis.mockResolvedValue(analysisWithBMO);

    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText('Before Market Open')).toBeInTheDocument();
    });
  });

  it('handles earnings without estimates', async () => {
    const earningsWithoutEstimates = {
      ...mockUpcomingEarnings,
      eps_estimate: undefined,
      revenue_estimate: undefined
    };
    const analysisWithoutEstimates = {
      ...mockAnalysis,
      upcoming_earnings: earningsWithoutEstimates
    };
    mockEarningsService.getEarningsImpactAnalysis.mockResolvedValue(analysisWithoutEstimates);

    render(<EarningsImpactAnalysisComponent symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.queryByText('EPS Estimate:')).not.toBeInTheDocument();
      expect(screen.queryByText('Revenue Estimate:')).not.toBeInTheDocument();
    });
  });
});