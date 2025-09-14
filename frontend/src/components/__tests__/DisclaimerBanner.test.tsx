/**
 * Tests for DisclaimerBanner Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import DisclaimerBanner from '../DisclaimerBanner';

// Mock the disclaimer service
jest.mock('../../services/disclaimer', () => ({
  disclaimerService: {
    getDisclaimersForContext: jest.fn(),
    shouldShowHighRiskDisclaimer: jest.fn(),
  }
}));

import { disclaimerService } from '../../services/disclaimer';

const mockDisclaimerService = disclaimerService as jest.Mocked<typeof disclaimerService>;

describe('DisclaimerBanner', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockDisclaimers = [
    {
      id: 'investment_advice',
      title: 'Investment Disclaimer',
      content: 'This is for informational purposes only and not investment advice.',
      severity: 'warning' as const,
      required: true,
      contexts: ['chat_response']
    }
  ];

  it('should render compact disclaimer banner', () => {
    mockDisclaimerService.getDisclaimersForContext.mockReturnValue(mockDisclaimers);
    mockDisclaimerService.shouldShowHighRiskDisclaimer.mockReturnValue(false);

    render(
      <DisclaimerBanner
        context="chat_response"
        compact={true}
      />
    );

    expect(screen.getByText(/Important: This information is for educational purposes only/)).toBeInTheDocument();
  });

  it('should render full disclaimer banner', () => {
    mockDisclaimerService.getDisclaimersForContext.mockReturnValue(mockDisclaimers);
    mockDisclaimerService.shouldShowHighRiskDisclaimer.mockReturnValue(false);

    render(
      <DisclaimerBanner
        context="analysis_result"
        compact={false}
      />
    );

    expect(screen.getByText('Important Disclaimers')).toBeInTheDocument();
    expect(screen.getByText('Investment Disclaimer:')).toBeInTheDocument();
  });

  it('should show high risk warning when applicable', () => {
    mockDisclaimerService.getDisclaimersForContext.mockReturnValue(mockDisclaimers);
    mockDisclaimerService.shouldShowHighRiskDisclaimer.mockReturnValue(true);

    render(
      <DisclaimerBanner
        context="recommendation"
        riskLevel="HIGH"
        symbol="TSLA"
        compact={true}
      />
    );

    expect(screen.getByText(/High Risk \(TSLA\)/)).toBeInTheDocument();
  });

  it('should expand and collapse when clicked', async () => {
    mockDisclaimerService.getDisclaimersForContext.mockReturnValue(mockDisclaimers);
    mockDisclaimerService.shouldShowHighRiskDisclaimer.mockReturnValue(false);

    render(
      <DisclaimerBanner
        context="chat_response"
        compact={true}
      />
    );

    const expandButton = screen.getByLabelText('expand disclaimer');
    
    // Initially collapsed
    expect(screen.queryByText('Investment Disclaimer:')).not.toBeInTheDocument();
    
    // Click to expand
    fireEvent.click(expandButton);
    
    // Wait for the collapse animation to complete
    await waitFor(() => {
      expect(screen.getByText('Investment Disclaimer:')).toBeInTheDocument();
    });
    
    // Click to collapse
    fireEvent.click(expandButton);
    
    // Wait for the collapse animation to complete
    await waitFor(() => {
      expect(screen.queryByText('Investment Disclaimer:')).not.toBeInTheDocument();
    });
  });

  it('should show appropriate disclaimer text for recommendation context', () => {
    mockDisclaimerService.getDisclaimersForContext.mockReturnValue(mockDisclaimers);
    mockDisclaimerService.shouldShowHighRiskDisclaimer.mockReturnValue(false);

    render(
      <DisclaimerBanner
        context="recommendation"
        compact={true}
      />
    );

    expect(screen.getByText(/Investment Disclaimer: This recommendation is for informational purposes only/)).toBeInTheDocument();
  });

  it('should show appropriate disclaimer text for backtest context', () => {
    mockDisclaimerService.getDisclaimersForContext.mockReturnValue(mockDisclaimers);
    mockDisclaimerService.shouldShowHighRiskDisclaimer.mockReturnValue(false);

    render(
      <DisclaimerBanner
        context="backtest"
        compact={true}
      />
    );

    expect(screen.getByText(/Backtesting Disclaimer: Past performance does not guarantee future results/)).toBeInTheDocument();
  });

  it('should not render when no disclaimers are available', () => {
    mockDisclaimerService.getDisclaimersForContext.mockReturnValue([]);
    mockDisclaimerService.shouldShowHighRiskDisclaimer.mockReturnValue(false);

    const { container } = render(
      <DisclaimerBanner
        context="chat_response"
        compact={true}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should show high risk chip in expanded view', () => {
    mockDisclaimerService.getDisclaimersForContext.mockReturnValue(mockDisclaimers);
    mockDisclaimerService.shouldShowHighRiskDisclaimer.mockReturnValue(true);

    render(
      <DisclaimerBanner
        context="recommendation"
        riskLevel="HIGH"
        compact={true}
      />
    );

    // Expand the disclaimer
    const expandButton = screen.getByLabelText('expand disclaimer');
    fireEvent.click(expandButton);

    expect(screen.getByText('High Risk Investment')).toBeInTheDocument();
  });

  it('should use correct severity icons', () => {
    const errorDisclaimers = [
      {
        ...mockDisclaimers[0],
        severity: 'error' as const
      }
    ];

    mockDisclaimerService.getDisclaimersForContext.mockReturnValue(errorDisclaimers);
    mockDisclaimerService.shouldShowHighRiskDisclaimer.mockReturnValue(false);

    render(
      <DisclaimerBanner
        context="recommendation"
        compact={true}
      />
    );

    // Check that error severity is applied (would need to check CSS classes or aria attributes)
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('MuiAlert-standardError');
  });

  it('should handle volatility-based high risk detection', () => {
    mockDisclaimerService.getDisclaimersForContext.mockReturnValue(mockDisclaimers);
    mockDisclaimerService.shouldShowHighRiskDisclaimer.mockReturnValue(true);

    render(
      <DisclaimerBanner
        context="analysis_result"
        volatility={0.4}
        symbol="VOLATILE"
        compact={true}
      />
    );

    expect(screen.getByText(/High Risk \(VOLATILE\)/)).toBeInTheDocument();
  });
});