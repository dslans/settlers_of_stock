/**
 * Tests for EarningsCalendar component.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { EarningsCalendar } from '../EarningsCalendar';
import { earningsService } from '../../services/earnings';
import {
  EarningsEvent,
  CorporateEvent,
  EventType,
  EventImpact,
  EarningsConfidence,
  EarningsCalendarResponse,
  CorporateEventsResponse
} from '../../types/earnings';

// Mock the earnings service
jest.mock('../../services/earnings');
const mockEarningsService = earningsService as jest.Mocked<typeof earningsService>;

// Mock CSS import
jest.mock('../EarningsCalendar.css', () => ({}));

describe('EarningsCalendar', () => {
  const mockEarningsEvent: EarningsEvent = {
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

  const mockCorporateEvent: CorporateEvent = {
    id: 1,
    symbol: 'AAPL',
    company_name: 'Apple Inc.',
    event_type: EventType.DIVIDEND,
    event_date: '2024-02-15T09:00:00Z',
    dividend_amount: 0.25,
    impact_level: EventImpact.LOW,
    is_confirmed: true,
    description: 'Quarterly dividend payment',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    days_until_event: 21,
    is_upcoming: true
  };

  const mockEarningsCalendarResponse: EarningsCalendarResponse = {
    total_events: 1,
    upcoming_events: 1,
    events: [mockEarningsEvent],
    date_range: {
      start_date: '2024-01-15',
      end_date: '2024-04-15'
    }
  };

  const mockCorporateEventsResponse: CorporateEventsResponse = {
    total_events: 1,
    upcoming_events: 1,
    events: [mockCorporateEvent],
    date_range: {
      start_date: '2024-01-15',
      end_date: '2024-04-15'
    },
    event_types: [EventType.DIVIDEND]
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockEarningsService.getEarningsCalendar.mockResolvedValue(mockEarningsCalendarResponse);
    mockEarningsService.getCorporateEventsCalendar.mockResolvedValue(mockCorporateEventsResponse);
  });

  it('renders earnings calendar with default props', async () => {
    render(<EarningsCalendar />);

    expect(screen.getByText('Events Calendar')).toBeInTheDocument();
    expect(screen.getByText('Upcoming')).toBeInTheDocument();
    expect(screen.getByText('All Events')).toBeInTheDocument();

    await waitFor(() => {
      expect(mockEarningsService.getEarningsCalendar).toHaveBeenCalled();
      expect(mockEarningsService.getCorporateEventsCalendar).toHaveBeenCalled();
    });
  });

  it('renders earnings only view', async () => {
    render(<EarningsCalendar viewType="earnings" />);

    expect(screen.getByText('Earnings Calendar')).toBeInTheDocument();

    await waitFor(() => {
      expect(mockEarningsService.getEarningsCalendar).toHaveBeenCalled();
      expect(mockEarningsService.getCorporateEventsCalendar).not.toHaveBeenCalled();
    });
  });

  it('renders corporate events only view', async () => {
    render(<EarningsCalendar viewType="corporate" />);

    expect(screen.getByText('Corporate Events Calendar')).toBeInTheDocument();

    await waitFor(() => {
      expect(mockEarningsService.getEarningsCalendar).not.toHaveBeenCalled();
      expect(mockEarningsService.getCorporateEventsCalendar).toHaveBeenCalled();
    });
  });

  it('displays earnings event correctly', async () => {
    render(<EarningsCalendar viewType="earnings" />);

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
      expect(screen.getByText('After Market Close')).toBeInTheDocument();
      expect(screen.getByText('Q1 2024')).toBeInTheDocument();
      expect(screen.getByText('$1.50')).toBeInTheDocument();
    });
  });

  it('displays corporate event correctly', async () => {
    render(<EarningsCalendar viewType="corporate" />);

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
      expect(screen.getByText('💰 Dividend')).toBeInTheDocument();
      expect(screen.getByText('$0.25 per share')).toBeInTheDocument();
      expect(screen.getByText('Quarterly dividend payment')).toBeInTheDocument();
    });
  });

  it('handles symbol filter input', async () => {
    render(<EarningsCalendar showFilters={true} />);

    const symbolInput = screen.getByPlaceholderText('AAPL, GOOGL, MSFT...');
    fireEvent.change(symbolInput, { target: { value: 'AAPL, GOOGL' } });

    await waitFor(() => {
      expect(mockEarningsService.getEarningsCalendar).toHaveBeenCalledWith(
        expect.objectContaining({
          symbols: ['AAPL', 'GOOGL']
        }),
        expect.any(Number)
      );
    });
  });

  it('handles date filter inputs', async () => {
    render(<EarningsCalendar showFilters={true} />);

    const startDateInput = screen.getByLabelText('Start Date:');
    const endDateInput = screen.getByLabelText('End Date:');

    fireEvent.change(startDateInput, { target: { value: '2024-01-01' } });
    fireEvent.change(endDateInput, { target: { value: '2024-03-31' } });

    await waitFor(() => {
      expect(mockEarningsService.getEarningsCalendar).toHaveBeenCalledWith(
        expect.objectContaining({
          start_date: '2024-01-01',
          end_date: '2024-03-31'
        }),
        expect.any(Number)
      );
    });
  });

  it('handles confirmed only filter', async () => {
    render(<EarningsCalendar showFilters={true} />);

    const confirmedOnlyCheckbox = screen.getByLabelText('Confirmed Only');
    fireEvent.click(confirmedOnlyCheckbox);

    await waitFor(() => {
      expect(mockEarningsService.getEarningsCalendar).toHaveBeenCalledWith(
        expect.objectContaining({
          confirmed_only: true
        }),
        expect.any(Number)
      );
    });
  });

  it('handles impact level filters', async () => {
    render(<EarningsCalendar showFilters={true} />);

    const highImpactCheckbox = screen.getByLabelText('High Impact');
    fireEvent.click(highImpactCheckbox);

    await waitFor(() => {
      expect(mockEarningsService.getEarningsCalendar).toHaveBeenCalledWith(
        expect.objectContaining({
          impact_levels: [EventImpact.HIGH]
        }),
        expect.any(Number)
      );
    });
  });

  it('handles event type filters for corporate events', async () => {
    render(<EarningsCalendar viewType="corporate" showFilters={true} />);

    const dividendCheckbox = screen.getByLabelText('💰 Dividend');
    fireEvent.click(dividendCheckbox);

    await waitFor(() => {
      expect(mockEarningsService.getCorporateEventsCalendar).toHaveBeenCalledWith(
        expect.objectContaining({
          event_types: [EventType.DIVIDEND]
        }),
        expect.any(Number)
      );
    });
  });

  it('handles has estimates filter for earnings', async () => {
    render(<EarningsCalendar viewType="earnings" showFilters={true} />);

    const hasEstimatesSelect = screen.getByLabelText('Has Estimates:');
    fireEvent.change(hasEstimatesSelect, { target: { value: 'true' } });

    await waitFor(() => {
      expect(mockEarningsService.getEarningsCalendar).toHaveBeenCalledWith(
        expect.objectContaining({
          has_estimates: true
        }),
        expect.any(Number)
      );
    });
  });

  it('handles sorting options', async () => {
    render(<EarningsCalendar />);

    const sortSelect = screen.getByDisplayValue('Sort by Date');
    fireEvent.change(sortSelect, { target: { value: 'symbol' } });

    // Should re-render with sorted events
    await waitFor(() => {
      expect(screen.getByDisplayValue('Sort by Symbol')).toBeInTheDocument();
    });
  });

  it('handles sort order toggle', async () => {
    render(<EarningsCalendar />);

    const sortOrderButton = screen.getByText('↑');
    fireEvent.click(sortOrderButton);

    expect(screen.getByText('↓')).toBeInTheDocument();
  });

  it('handles view toggle between upcoming and all events', async () => {
    render(<EarningsCalendar />);

    const allEventsButton = screen.getByText('All Events');
    fireEvent.click(allEventsButton);

    expect(allEventsButton).toHaveClass('active');
    expect(screen.getByText('Upcoming')).not.toHaveClass('active');
  });

  it('handles event click callback', async () => {
    const onEventClick = jest.fn();
    render(<EarningsCalendar viewType="earnings" onEventClick={onEventClick} />);

    await waitFor(() => {
      const eventCard = screen.getByText('AAPL').closest('.earnings-event-card');
      expect(eventCard).toBeInTheDocument();
      
      if (eventCard) {
        fireEvent.click(eventCard);
        expect(onEventClick).toHaveBeenCalledWith(mockEarningsEvent);
      }
    });
  });

  it('displays loading state', () => {
    mockEarningsService.getEarningsCalendar.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<EarningsCalendar />);

    expect(screen.getByText('Loading calendar data...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { hidden: true })).toBeInTheDocument();
  });

  it('displays error state', async () => {
    const errorMessage = 'Failed to fetch calendar data';
    mockEarningsService.getEarningsCalendar.mockRejectedValue(new Error(errorMessage));

    render(<EarningsCalendar />);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  it('handles retry on error', async () => {
    const errorMessage = 'Network error';
    mockEarningsService.getEarningsCalendar
      .mockRejectedValueOnce(new Error(errorMessage))
      .mockResolvedValueOnce(mockEarningsCalendarResponse);

    render(<EarningsCalendar />);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });
  });

  it('displays no events message when empty', async () => {
    mockEarningsService.getEarningsCalendar.mockResolvedValue({
      total_events: 0,
      upcoming_events: 0,
      events: [],
      date_range: {}
    });

    mockEarningsService.getCorporateEventsCalendar.mockResolvedValue({
      total_events: 0,
      upcoming_events: 0,
      events: [],
      date_range: {},
      event_types: []
    });

    render(<EarningsCalendar />);

    await waitFor(() => {
      expect(screen.getByText('No events found for the selected criteria')).toBeInTheDocument();
    });
  });

  it('handles symbols prop correctly', async () => {
    render(<EarningsCalendar symbols={['AAPL', 'GOOGL']} />);

    await waitFor(() => {
      expect(mockEarningsService.getEarningsCalendar).toHaveBeenCalledWith(
        expect.objectContaining({
          symbols: ['AAPL', 'GOOGL']
        }),
        expect.any(Number)
      );
    });
  });

  it('respects maxEvents prop', async () => {
    render(<EarningsCalendar maxEvents={50} />);

    await waitFor(() => {
      expect(mockEarningsService.getEarningsCalendar).toHaveBeenCalledWith(
        expect.any(Object),
        50
      );
    });
  });

  it('hides filters when showFilters is false', () => {
    render(<EarningsCalendar showFilters={false} />);

    expect(screen.queryByPlaceholderText('AAPL, GOOGL, MSFT...')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Start Date:')).not.toBeInTheDocument();
  });

  it('formats earnings event data correctly', async () => {
    render(<EarningsCalendar viewType="earnings" />);

    await waitFor(() => {
      // Check that earnings data is formatted properly
      expect(screen.getByText('high')).toBeInTheDocument(); // Impact level
      expect(screen.getByText('high')).toBeInTheDocument(); // Confidence level
      expect(screen.getByText('In 7 days')).toBeInTheDocument(); // Days until
    });
  });

  it('formats corporate event data correctly', async () => {
    render(<EarningsCalendar viewType="corporate" />);

    await waitFor(() => {
      // Check that corporate event data is formatted properly
      expect(screen.getByText('low')).toBeInTheDocument(); // Impact level
      expect(screen.getByText('In 21 days')).toBeInTheDocument(); // Days until
    });
  });

  it('handles multiple impact level selections', async () => {
    render(<EarningsCalendar showFilters={true} />);

    const highImpactCheckbox = screen.getByLabelText('High Impact');
    const mediumImpactCheckbox = screen.getByLabelText('Medium Impact');

    fireEvent.click(highImpactCheckbox);
    fireEvent.click(mediumImpactCheckbox);

    await waitFor(() => {
      expect(mockEarningsService.getEarningsCalendar).toHaveBeenCalledWith(
        expect.objectContaining({
          impact_levels: [EventImpact.HIGH, EventImpact.MEDIUM]
        }),
        expect.any(Number)
      );
    });
  });

  it('handles deselecting filters', async () => {
    render(<EarningsCalendar showFilters={true} />);

    const highImpactCheckbox = screen.getByLabelText('High Impact');

    // Select then deselect
    fireEvent.click(highImpactCheckbox);
    fireEvent.click(highImpactCheckbox);

    await waitFor(() => {
      expect(mockEarningsService.getEarningsCalendar).toHaveBeenCalledWith(
        expect.objectContaining({
          impact_levels: []
        }),
        expect.any(Number)
      );
    });
  });
});