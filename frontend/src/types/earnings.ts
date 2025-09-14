/**
 * TypeScript types for earnings calendar and corporate events.
 */

export enum EventType {
  EARNINGS = 'earnings',
  DIVIDEND = 'dividend',
  STOCK_SPLIT = 'stock_split',
  MERGER = 'merger',
  ACQUISITION = 'acquisition',
  SPINOFF = 'spinoff',
  RIGHTS_OFFERING = 'rights_offering',
  SPECIAL_DIVIDEND = 'special_dividend',
  CONFERENCE_CALL = 'conference_call',
  ANALYST_DAY = 'analyst_day'
}

export enum EarningsConfidence {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  UNCONFIRMED = 'unconfirmed'
}

export enum EventImpact {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  UNKNOWN = 'unknown'
}

export interface EarningsEvent {
  id: number;
  symbol: string;
  company_name: string;
  earnings_date: string;
  report_time?: string; // 'BMO', 'AMC', 'DMT'
  fiscal_quarter?: string; // 'Q1', 'Q2', 'Q3', 'Q4'
  fiscal_year?: number;
  
  // Estimates
  eps_estimate?: number;
  eps_estimate_high?: number;
  eps_estimate_low?: number;
  eps_estimate_count?: number;
  revenue_estimate?: number;
  revenue_estimate_high?: number;
  revenue_estimate_low?: number;
  
  // Actuals
  eps_actual?: number;
  revenue_actual?: number;
  eps_surprise?: number;
  revenue_surprise?: number;
  
  // Metadata
  confidence: EarningsConfidence;
  impact_level: EventImpact;
  is_confirmed: boolean;
  notes?: string;
  
  // Timestamps
  created_at: string;
  updated_at: string;
  
  // Calculated fields
  days_until_earnings?: number;
  is_upcoming: boolean;
  has_estimates: boolean;
  has_actuals: boolean;
}

export interface CorporateEvent {
  id: number;
  symbol: string;
  company_name: string;
  event_type: EventType;
  event_date: string;
  ex_date?: string;
  record_date?: string;
  payment_date?: string;
  
  // Event-specific data
  dividend_amount?: number;
  split_ratio?: string;
  split_factor?: number;
  
  // Description and impact
  description?: string;
  impact_level: EventImpact;
  is_confirmed: boolean;
  
  // Timestamps
  created_at: string;
  updated_at: string;
  
  // Calculated fields
  days_until_event?: number;
  is_upcoming: boolean;
}

export interface EarningsHistoricalPerformance {
  id: number;
  symbol: string;
  price_before_earnings?: number;
  price_after_earnings?: number;
  price_change_1d?: number;
  price_change_1w?: number;
  price_change_1m?: number;
  volume_before?: number;
  volume_after?: number;
  volume_change?: number;
  beat_estimate?: boolean;
  surprise_magnitude?: number;
  created_at: string;
}

export interface EarningsCalendarFilter {
  symbols?: string[];
  start_date?: string;
  end_date?: string;
  confirmed_only?: boolean;
  impact_levels?: EventImpact[];
  has_estimates?: boolean;
}

export interface CorporateEventsFilter {
  symbols?: string[];
  event_types?: EventType[];
  start_date?: string;
  end_date?: string;
  confirmed_only?: boolean;
  impact_levels?: EventImpact[];
}

export interface EarningsCalendarResponse {
  total_events: number;
  upcoming_events: number;
  events: EarningsEvent[];
  date_range: {
    start_date?: string;
    end_date?: string;
  };
}

export interface CorporateEventsResponse {
  total_events: number;
  upcoming_events: number;
  events: CorporateEvent[];
  date_range: {
    start_date?: string;
    end_date?: string;
  };
  event_types: EventType[];
}

export interface EarningsImpactAnalysis {
  symbol: string;
  upcoming_earnings?: EarningsEvent;
  historical_performance: EarningsHistoricalPerformance[];
  
  // Analysis metrics
  avg_price_change_1d?: number;
  avg_price_change_1w?: number;
  avg_volume_change?: number;
  beat_rate?: number;
  volatility_increase?: number;
  
  // Predictions
  expected_volatility?: string;
  risk_level?: string;
  key_metrics_to_watch: string[];
}

export interface FetchDataRequest {
  symbol: string;
  days_ahead?: number;
}

export interface FetchDataResponse {
  message: string;
  earnings_events_count: number;
  corporate_events_count: number;
  earnings_events: EarningsEvent[];
  corporate_events: CorporateEvent[];
}

// UI-specific types
export interface EarningsCalendarViewProps {
  symbols?: string[];
  showFilters?: boolean;
  maxEvents?: number;
  onEventClick?: (event: EarningsEvent) => void;
}

export interface CorporateEventsViewProps {
  symbols?: string[];
  eventTypes?: EventType[];
  showFilters?: boolean;
  maxEvents?: number;
  onEventClick?: (event: CorporateEvent) => void;
}

export interface EarningsImpactViewProps {
  symbol: string;
  onAnalysisUpdate?: (analysis: EarningsImpactAnalysis) => void;
}

export interface EventCalendarProps {
  events: (EarningsEvent | CorporateEvent)[];
  viewType: 'earnings' | 'corporate' | 'combined';
  onDateSelect?: (date: Date) => void;
  onEventSelect?: (event: EarningsEvent | CorporateEvent) => void;
}

// Utility types for formatting
export interface FormattedEarningsEvent extends EarningsEvent {
  formatted_date: string;
  formatted_time: string;
  impact_color: string;
  confidence_color: string;
  days_text: string;
}

export interface FormattedCorporateEvent extends CorporateEvent {
  formatted_date: string;
  event_type_display: string;
  impact_color: string;
  days_text: string;
}

// API error types
export interface EarningsApiError {
  message: string;
  error_type: string;
  suggestions: string[];
}

// Filter options for UI components
export const IMPACT_LEVEL_OPTIONS = [
  { value: EventImpact.HIGH, label: 'High Impact', color: '#ef4444' },
  { value: EventImpact.MEDIUM, label: 'Medium Impact', color: '#f59e0b' },
  { value: EventImpact.LOW, label: 'Low Impact', color: '#10b981' },
  { value: EventImpact.UNKNOWN, label: 'Unknown Impact', color: '#6b7280' }
];

export const CONFIDENCE_LEVEL_OPTIONS = [
  { value: EarningsConfidence.HIGH, label: 'High Confidence', color: '#10b981' },
  { value: EarningsConfidence.MEDIUM, label: 'Medium Confidence', color: '#f59e0b' },
  { value: EarningsConfidence.LOW, label: 'Low Confidence', color: '#ef4444' },
  { value: EarningsConfidence.UNCONFIRMED, label: 'Unconfirmed', color: '#6b7280' }
];

export const EVENT_TYPE_OPTIONS = [
  { value: EventType.EARNINGS, label: 'Earnings', icon: '📊' },
  { value: EventType.DIVIDEND, label: 'Dividend', icon: '💰' },
  { value: EventType.STOCK_SPLIT, label: 'Stock Split', icon: '✂️' },
  { value: EventType.MERGER, label: 'Merger', icon: '🤝' },
  { value: EventType.ACQUISITION, label: 'Acquisition', icon: '🏢' },
  { value: EventType.SPINOFF, label: 'Spinoff', icon: '🔄' },
  { value: EventType.RIGHTS_OFFERING, label: 'Rights Offering', icon: '📜' },
  { value: EventType.SPECIAL_DIVIDEND, label: 'Special Dividend', icon: '💎' },
  { value: EventType.CONFERENCE_CALL, label: 'Conference Call', icon: '📞' },
  { value: EventType.ANALYST_DAY, label: 'Analyst Day', icon: '👥' }
];

// Date formatting utilities
export const formatEarningsDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
};

export const formatEarningsTime = (reportTime?: string): string => {
  switch (reportTime) {
    case 'BMO':
      return 'Before Market Open';
    case 'AMC':
      return 'After Market Close';
    case 'DMT':
      return 'During Market Hours';
    default:
      return 'Time TBD';
  }
};

export const getDaysUntilText = (days?: number): string => {
  if (days === undefined || days === null) return '';
  
  if (days === 0) return 'Today';
  if (days === 1) return 'Tomorrow';
  if (days === -1) return 'Yesterday';
  if (days > 0) return `In ${days} days`;
  return `${Math.abs(days)} days ago`;
};

export const getImpactColor = (impact: EventImpact): string => {
  const option = IMPACT_LEVEL_OPTIONS.find(opt => opt.value === impact);
  return option?.color || '#6b7280';
};

export const getConfidenceColor = (confidence: EarningsConfidence): string => {
  const option = CONFIDENCE_LEVEL_OPTIONS.find(opt => opt.value === confidence);
  return option?.color || '#6b7280';
};