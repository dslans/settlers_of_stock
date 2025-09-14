/**
 * Earnings calendar and corporate events API service.
 */

import { api } from './api';
import {
  EarningsEvent,
  CorporateEvent,
  EarningsCalendarResponse,
  CorporateEventsResponse,
  EarningsImpactAnalysis,
  EarningsCalendarFilter,
  CorporateEventsFilter,
  FetchDataRequest,
  FetchDataResponse,
  EarningsApiError,
  EventType,
  EventImpact
} from '../types/earnings';

export class EarningsService {
  private baseUrl = '/earnings';

  /**
   * Get earnings calendar with optional filtering.
   */
  async getEarningsCalendar(
    filters: EarningsCalendarFilter = {},
    limit: number = 100,
    offset: number = 0
  ): Promise<EarningsCalendarResponse> {
    try {
      const params = new URLSearchParams();
      
      if (filters.symbols && filters.symbols.length > 0) {
        params.append('symbols', filters.symbols.join(','));
      }
      
      if (filters.start_date) {
        params.append('start_date', filters.start_date);
      }
      
      if (filters.end_date) {
        params.append('end_date', filters.end_date);
      }
      
      if (filters.confirmed_only) {
        params.append('confirmed_only', 'true');
      }
      
      if (filters.impact_levels && filters.impact_levels.length > 0) {
        params.append('impact_levels', filters.impact_levels.join(','));
      }
      
      if (filters.has_estimates !== undefined) {
        params.append('has_estimates', filters.has_estimates.toString());
      }
      
      params.append('limit', limit.toString());
      params.append('offset', offset.toString());
      
      const response = await api.get(`${this.baseUrl}/calendar?${params.toString()}`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Get corporate events calendar with optional filtering.
   */
  async getCorporateEventsCalendar(
    filters: CorporateEventsFilter = {},
    limit: number = 100,
    offset: number = 0
  ): Promise<CorporateEventsResponse> {
    try {
      const params = new URLSearchParams();
      
      if (filters.symbols && filters.symbols.length > 0) {
        params.append('symbols', filters.symbols.join(','));
      }
      
      if (filters.event_types && filters.event_types.length > 0) {
        params.append('event_types', filters.event_types.join(','));
      }
      
      if (filters.start_date) {
        params.append('start_date', filters.start_date);
      }
      
      if (filters.end_date) {
        params.append('end_date', filters.end_date);
      }
      
      if (filters.confirmed_only) {
        params.append('confirmed_only', 'true');
      }
      
      if (filters.impact_levels && filters.impact_levels.length > 0) {
        params.append('impact_levels', filters.impact_levels.join(','));
      }
      
      params.append('limit', limit.toString());
      params.append('offset', offset.toString());
      
      const response = await api.get(`${this.baseUrl}/events?${params.toString()}`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Get upcoming earnings events for a specific symbol.
   */
  async getUpcomingEarnings(
    symbol: string,
    daysAhead: number = 90
  ): Promise<EarningsEvent[]> {
    try {
      const params = new URLSearchParams();
      params.append('days_ahead', daysAhead.toString());
      
      const response = await api.get(
        `${this.baseUrl}/${symbol.toUpperCase()}/upcoming?${params.toString()}`
      );
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Get corporate events for a specific symbol.
   */
  async getCorporateEventsForSymbol(
    symbol: string,
    daysAhead: number = 90,
    eventTypes?: EventType[]
  ): Promise<CorporateEvent[]> {
    try {
      const params = new URLSearchParams();
      params.append('days_ahead', daysAhead.toString());
      
      if (eventTypes && eventTypes.length > 0) {
        params.append('event_types', eventTypes.join(','));
      }
      
      const response = await api.get(
        `${this.baseUrl}/${symbol.toUpperCase()}/events?${params.toString()}`
      );
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Get earnings impact analysis for a symbol.
   */
  async getEarningsImpactAnalysis(symbol: string): Promise<EarningsImpactAnalysis> {
    try {
      const response = await api.get(
        `${this.baseUrl}/${symbol.toUpperCase()}/impact-analysis`
      );
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Fetch and store earnings data for a symbol from external sources.
   */
  async fetchEarningsData(request: FetchDataRequest): Promise<FetchDataResponse> {
    try {
      const params = new URLSearchParams();
      if (request.days_ahead) {
        params.append('days_ahead', request.days_ahead.toString());
      }
      
      const response = await api.post(
        `${this.baseUrl}/${request.symbol.toUpperCase()}/fetch-data?${params.toString()}`
      );
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Get today's earnings events.
   */
  async getTodaysEarnings(): Promise<EarningsCalendarResponse> {
    try {
      const response = await api.get(`${this.baseUrl}/today`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Get this week's earnings events.
   */
  async getThisWeeksEarnings(): Promise<EarningsCalendarResponse> {
    try {
      const response = await api.get(`${this.baseUrl}/this-week`);
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Get combined calendar data (earnings + corporate events) for a symbol.
   */
  async getCombinedCalendarForSymbol(
    symbol: string,
    daysAhead: number = 90
  ): Promise<{
    earnings: EarningsEvent[];
    corporateEvents: CorporateEvent[];
  }> {
    try {
      const [earnings, corporateEvents] = await Promise.all([
        this.getUpcomingEarnings(symbol, daysAhead),
        this.getCorporateEventsForSymbol(symbol, daysAhead)
      ]);
      
      return {
        earnings,
        corporateEvents
      };
    } catch (error: any) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Get earnings events for multiple symbols.
   */
  async getEarningsForSymbols(
    symbols: string[],
    daysAhead: number = 90
  ): Promise<EarningsCalendarResponse> {
    try {
      const filters: EarningsCalendarFilter = {
        symbols: symbols.map(s => s.toUpperCase()),
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date(Date.now() + daysAhead * 24 * 60 * 60 * 1000)
          .toISOString().split('T')[0]
      };
      
      return await this.getEarningsCalendar(filters, 200);
    } catch (error: any) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Get high-impact events for the next week.
   */
  async getHighImpactEvents(): Promise<{
    earnings: EarningsEvent[];
    corporateEvents: CorporateEvent[];
  }> {
    try {
      const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
      
      const earningsFilters: EarningsCalendarFilter = {
        start_date: new Date().toISOString().split('T')[0],
        end_date: nextWeek.toISOString().split('T')[0],
        impact_levels: [EventImpact.HIGH],
        confirmed_only: true
      };
      
      const corporateFilters: CorporateEventsFilter = {
        start_date: new Date().toISOString().split('T')[0],
        end_date: nextWeek.toISOString().split('T')[0],
        impact_levels: [EventImpact.HIGH],
        confirmed_only: true
      };
      
      const [earningsResponse, corporateResponse] = await Promise.all([
        this.getEarningsCalendar(earningsFilters, 50),
        this.getCorporateEventsCalendar(corporateFilters, 50)
      ]);
      
      return {
        earnings: earningsResponse.events,
        corporateEvents: corporateResponse.events
      };
    } catch (error: any) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Search for events by company name or symbol.
   */
  async searchEvents(
    query: string,
    eventType: 'earnings' | 'corporate' | 'both' = 'both'
  ): Promise<{
    earnings: EarningsEvent[];
    corporateEvents: CorporateEvent[];
  }> {
    try {
      const searchSymbols = [query.toUpperCase()];
      
      const promises: Promise<any>[] = [];
      
      if (eventType === 'earnings' || eventType === 'both') {
        const earningsFilters: EarningsCalendarFilter = {
          symbols: searchSymbols
        };
        promises.push(this.getEarningsCalendar(earningsFilters, 50));
      } else {
        promises.push(Promise.resolve({ events: [] }));
      }
      
      if (eventType === 'corporate' || eventType === 'both') {
        const corporateFilters: CorporateEventsFilter = {
          symbols: searchSymbols
        };
        promises.push(this.getCorporateEventsCalendar(corporateFilters, 50));
      } else {
        promises.push(Promise.resolve({ events: [] }));
      }
      
      const [earningsResponse, corporateResponse] = await Promise.all(promises);
      
      return {
        earnings: earningsResponse.events || [],
        corporateEvents: corporateResponse.events || []
      };
    } catch (error: any) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Handle API errors and convert to user-friendly format.
   */
  private handleApiError(error: any): EarningsApiError {
    if (error.response?.data) {
      const errorData = error.response.data;
      if (errorData.detail && typeof errorData.detail === 'object') {
        return {
          message: errorData.detail.message || 'An error occurred',
          error_type: errorData.detail.error_type || 'UNKNOWN_ERROR',
          suggestions: errorData.detail.suggestions || []
        };
      } else if (errorData.detail && typeof errorData.detail === 'string') {
        return {
          message: errorData.detail,
          error_type: 'API_ERROR',
          suggestions: []
        };
      }
    }
    
    return {
      message: error.message || 'An unexpected error occurred',
      error_type: 'NETWORK_ERROR',
      suggestions: ['Check your internet connection', 'Try again later']
    };
  }
}

// Export singleton instance
export const earningsService = new EarningsService();