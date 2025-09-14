/**
 * Earnings Calendar Component
 * Displays upcoming and historical earnings events with filtering and analysis.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  EarningsEvent,
  CorporateEvent,
  EarningsCalendarFilter,
  CorporateEventsFilter,
  EventImpact,
  EventType,
  EarningsConfidence,
  formatEarningsDate,
  formatEarningsTime,
  getDaysUntilText,
  getImpactColor,
  getConfidenceColor,
  IMPACT_LEVEL_OPTIONS,
  EVENT_TYPE_OPTIONS
} from '../types/earnings';
import { earningsService } from '../services/earnings';
import './EarningsCalendar.css';

interface EarningsCalendarProps {
  symbols?: string[];
  showFilters?: boolean;
  maxEvents?: number;
  viewType?: 'earnings' | 'corporate' | 'combined';
  onEventClick?: (event: EarningsEvent | CorporateEvent) => void;
}

export const EarningsCalendar: React.FC<EarningsCalendarProps> = ({
  symbols = [],
  showFilters = true,
  maxEvents = 100,
  viewType = 'combined',
  onEventClick
}) => {
  const [earningsEvents, setEarningsEvents] = useState<EarningsEvent[]>([]);
  const [corporateEvents, setCorporateEvents] = useState<CorporateEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Filter states
  const [symbolFilter, setSymbolFilter] = useState<string>(symbols.join(', '));
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [confirmedOnly, setConfirmedOnly] = useState(false);
  const [selectedImpactLevels, setSelectedImpactLevels] = useState<EventImpact[]>([]);
  const [selectedEventTypes, setSelectedEventTypes] = useState<EventType[]>([]);
  const [hasEstimatesFilter, setHasEstimatesFilter] = useState<boolean | undefined>(undefined);
  
  // View states
  const [sortBy, setSortBy] = useState<'date' | 'symbol' | 'impact'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [showUpcomingOnly, setShowUpcomingOnly] = useState(true);

  // Set default date range
  useEffect(() => {
    const today = new Date();
    const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
    const ninetyDaysFromNow = new Date(today.getTime() + 90 * 24 * 60 * 60 * 1000);
    
    setStartDate(showUpcomingOnly ? today.toISOString().split('T')[0] : thirtyDaysAgo.toISOString().split('T')[0]);
    setEndDate(ninetyDaysFromNow.toISOString().split('T')[0]);
  }, [showUpcomingOnly]);

  // Fetch data when filters change
  useEffect(() => {
    fetchData();
  }, [
    symbolFilter,
    startDate,
    endDate,
    confirmedOnly,
    selectedImpactLevels,
    selectedEventTypes,
    hasEstimatesFilter,
    viewType
  ]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const symbolList = symbolFilter
        .split(',')
        .map(s => s.trim().toUpperCase())
        .filter(s => s.length > 0);

      if (viewType === 'earnings' || viewType === 'combined') {
        const earningsFilters: EarningsCalendarFilter = {
          symbols: symbolList.length > 0 ? symbolList : undefined,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
          confirmed_only: confirmedOnly,
          impact_levels: selectedImpactLevels.length > 0 ? selectedImpactLevels : undefined,
          has_estimates: hasEstimatesFilter
        };

        const earningsResponse = await earningsService.getEarningsCalendar(
          earningsFilters,
          maxEvents
        );
        setEarningsEvents(earningsResponse.events);
      }

      if (viewType === 'corporate' || viewType === 'combined') {
        const corporateFilters: CorporateEventsFilter = {
          symbols: symbolList.length > 0 ? symbolList : undefined,
          event_types: selectedEventTypes.length > 0 ? selectedEventTypes : undefined,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
          confirmed_only: confirmedOnly,
          impact_levels: selectedImpactLevels.length > 0 ? selectedImpactLevels : undefined
        };

        const corporateResponse = await earningsService.getCorporateEventsCalendar(
          corporateFilters,
          maxEvents
        );
        setCorporateEvents(corporateResponse.events);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch calendar data');
    } finally {
      setLoading(false);
    }
  };

  // Combined and sorted events
  const sortedEvents = useMemo(() => {
    let allEvents: (EarningsEvent | CorporateEvent)[] = [];
    
    if (viewType === 'earnings' || viewType === 'combined') {
      allEvents = [...allEvents, ...earningsEvents];
    }
    
    if (viewType === 'corporate' || viewType === 'combined') {
      allEvents = [...allEvents, ...corporateEvents];
    }

    // Sort events
    return allEvents.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'date':
          const dateA = 'earnings_date' in a ? new Date(a.earnings_date) : new Date(a.event_date);
          const dateB = 'earnings_date' in b ? new Date(b.earnings_date) : new Date(b.event_date);
          comparison = dateA.getTime() - dateB.getTime();
          break;
        case 'symbol':
          comparison = a.symbol.localeCompare(b.symbol);
          break;
        case 'impact':
          const impactOrder = { high: 3, medium: 2, low: 1, unknown: 0 };
          comparison = impactOrder[b.impact_level] - impactOrder[a.impact_level];
          break;
      }
      
      return sortOrder === 'desc' ? -comparison : comparison;
    });
  }, [earningsEvents, corporateEvents, sortBy, sortOrder, viewType]);

  const handleImpactLevelToggle = (level: EventImpact) => {
    setSelectedImpactLevels(prev =>
      prev.includes(level)
        ? prev.filter(l => l !== level)
        : [...prev, level]
    );
  };

  const handleEventTypeToggle = (type: EventType) => {
    setSelectedEventTypes(prev =>
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  const renderEarningsEvent = (event: EarningsEvent) => (
    <div
      key={`earnings-${event.id}`}
      className={`earnings-event-card ${event.is_upcoming ? 'upcoming' : 'past'}`}
      onClick={() => onEventClick?.(event)}
      style={{ borderLeftColor: getImpactColor(event.impact_level) }}
    >
      <div className="event-header">
        <div className="event-symbol-name">
          <span className="event-symbol">{event.symbol}</span>
          <span className="event-company">{event.company_name}</span>
        </div>
        <div className="event-badges">
          <span
            className="impact-badge"
            style={{ backgroundColor: getImpactColor(event.impact_level) }}
          >
            {event.impact_level}
          </span>
          <span
            className="confidence-badge"
            style={{ backgroundColor: getConfidenceColor(event.confidence) }}
          >
            {event.confidence}
          </span>
        </div>
      </div>
      
      <div className="event-details">
        <div className="event-date-time">
          <span className="event-date">{formatEarningsDate(event.earnings_date)}</span>
          <span className="event-time">{formatEarningsTime(event.report_time)}</span>
          {event.days_until_earnings !== undefined && (
            <span className="days-until">{getDaysUntilText(event.days_until_earnings)}</span>
          )}
        </div>
        
        {event.fiscal_quarter && (
          <div className="fiscal-info">
            {event.fiscal_quarter} {event.fiscal_year}
          </div>
        )}
        
        {(event.has_estimates || event.has_actuals) && (
          <div className="earnings-metrics">
            {event.eps_estimate && (
              <div className="metric">
                <span className="metric-label">EPS Est:</span>
                <span className="metric-value">${event.eps_estimate.toFixed(2)}</span>
              </div>
            )}
            {event.eps_actual && (
              <div className="metric">
                <span className="metric-label">EPS Actual:</span>
                <span className="metric-value">${event.eps_actual.toFixed(2)}</span>
                {event.eps_surprise && (
                  <span className={`surprise ${event.eps_surprise > 0 ? 'positive' : 'negative'}`}>
                    ({event.eps_surprise > 0 ? '+' : ''}${event.eps_surprise.toFixed(2)})
                  </span>
                )}
              </div>
            )}
            {event.revenue_estimate && (
              <div className="metric">
                <span className="metric-label">Rev Est:</span>
                <span className="metric-value">${(event.revenue_estimate / 1e9).toFixed(2)}B</span>
              </div>
            )}
          </div>
        )}
        
        {event.notes && (
          <div className="event-notes">{event.notes}</div>
        )}
      </div>
    </div>
  );

  const renderCorporateEvent = (event: CorporateEvent) => {
    const eventTypeOption = EVENT_TYPE_OPTIONS.find(opt => opt.value === event.event_type);
    
    return (
      <div
        key={`corporate-${event.id}`}
        className={`corporate-event-card ${event.is_upcoming ? 'upcoming' : 'past'}`}
        onClick={() => onEventClick?.(event)}
        style={{ borderLeftColor: getImpactColor(event.impact_level) }}
      >
        <div className="event-header">
          <div className="event-symbol-name">
            <span className="event-symbol">{event.symbol}</span>
            <span className="event-company">{event.company_name}</span>
          </div>
          <div className="event-badges">
            <span className="event-type-badge">
              {eventTypeOption?.icon} {eventTypeOption?.label}
            </span>
            <span
              className="impact-badge"
              style={{ backgroundColor: getImpactColor(event.impact_level) }}
            >
              {event.impact_level}
            </span>
          </div>
        </div>
        
        <div className="event-details">
          <div className="event-date-time">
            <span className="event-date">{formatEarningsDate(event.event_date)}</span>
            {event.days_until_event !== undefined && (
              <span className="days-until">{getDaysUntilText(event.days_until_event)}</span>
            )}
          </div>
          
          {event.event_type === EventType.DIVIDEND && event.dividend_amount && (
            <div className="event-specific-data">
              <span className="metric-label">Dividend:</span>
              <span className="metric-value">${event.dividend_amount.toFixed(2)} per share</span>
            </div>
          )}
          
          {event.event_type === EventType.STOCK_SPLIT && event.split_ratio && (
            <div className="event-specific-data">
              <span className="metric-label">Split Ratio:</span>
              <span className="metric-value">{event.split_ratio}</span>
            </div>
          )}
          
          {event.description && (
            <div className="event-description">{event.description}</div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="earnings-calendar">
      <div className="calendar-header">
        <h2>
          {viewType === 'earnings' && 'Earnings Calendar'}
          {viewType === 'corporate' && 'Corporate Events Calendar'}
          {viewType === 'combined' && 'Events Calendar'}
        </h2>
        
        <div className="calendar-controls">
          <div className="view-toggle">
            <button
              className={showUpcomingOnly ? 'active' : ''}
              onClick={() => setShowUpcomingOnly(true)}
            >
              Upcoming
            </button>
            <button
              className={!showUpcomingOnly ? 'active' : ''}
              onClick={() => setShowUpcomingOnly(false)}
            >
              All Events
            </button>
          </div>
          
          <div className="sort-controls">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'date' | 'symbol' | 'impact')}
            >
              <option value="date">Sort by Date</option>
              <option value="symbol">Sort by Symbol</option>
              <option value="impact">Sort by Impact</option>
            </select>
            <button
              className="sort-order-btn"
              onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
          </div>
        </div>
      </div>

      {showFilters && (
        <div className="calendar-filters">
          <div className="filter-row">
            <div className="filter-group">
              <label>Symbols:</label>
              <input
                type="text"
                value={symbolFilter}
                onChange={(e) => setSymbolFilter(e.target.value)}
                placeholder="AAPL, GOOGL, MSFT..."
              />
            </div>
            
            <div className="filter-group">
              <label>Start Date:</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            
            <div className="filter-group">
              <label>End Date:</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            
            <div className="filter-group">
              <label>
                <input
                  type="checkbox"
                  checked={confirmedOnly}
                  onChange={(e) => setConfirmedOnly(e.target.checked)}
                />
                Confirmed Only
              </label>
            </div>
          </div>
          
          <div className="filter-row">
            <div className="filter-group">
              <label>Impact Levels:</label>
              <div className="checkbox-group">
                {IMPACT_LEVEL_OPTIONS.map(option => (
                  <label key={option.value} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={selectedImpactLevels.includes(option.value)}
                      onChange={() => handleImpactLevelToggle(option.value)}
                    />
                    <span style={{ color: option.color }}>{option.label}</span>
                  </label>
                ))}
              </div>
            </div>
            
            {(viewType === 'corporate' || viewType === 'combined') && (
              <div className="filter-group">
                <label>Event Types:</label>
                <div className="checkbox-group">
                  {EVENT_TYPE_OPTIONS.slice(0, 5).map(option => (
                    <label key={option.value} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={selectedEventTypes.includes(option.value)}
                        onChange={() => handleEventTypeToggle(option.value)}
                      />
                      <span>{option.icon} {option.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
            
            {(viewType === 'earnings' || viewType === 'combined') && (
              <div className="filter-group">
                <label>Has Estimates:</label>
                <select
                  value={hasEstimatesFilter === undefined ? 'all' : hasEstimatesFilter.toString()}
                  onChange={(e) => {
                    const value = e.target.value;
                    setHasEstimatesFilter(
                      value === 'all' ? undefined : value === 'true'
                    );
                  }}
                >
                  <option value="all">All Events</option>
                  <option value="true">With Estimates</option>
                  <option value="false">Without Estimates</option>
                </select>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="calendar-content">
        {loading && (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <span>Loading calendar data...</span>
          </div>
        )}

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
            <button onClick={fetchData} className="retry-btn">
              Retry
            </button>
          </div>
        )}

        {!loading && !error && sortedEvents.length === 0 && (
          <div className="no-events">
            <span className="no-events-icon">📅</span>
            <span>No events found for the selected criteria</span>
          </div>
        )}

        {!loading && !error && sortedEvents.length > 0 && (
          <div className="events-list">
            {sortedEvents.map(event => 
              'earnings_date' in event 
                ? renderEarningsEvent(event as EarningsEvent)
                : renderCorporateEvent(event as CorporateEvent)
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EarningsCalendar;