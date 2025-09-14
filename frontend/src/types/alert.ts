/**
 * TypeScript types for the alert system
 */

export enum AlertType {
  PRICE_ABOVE = 'price_above',
  PRICE_BELOW = 'price_below',
  PRICE_CHANGE_PERCENT = 'price_change_percent',
  VOLUME_SPIKE = 'volume_spike',
  TECHNICAL_BREAKOUT = 'technical_breakout',
  TECHNICAL_BREAKDOWN = 'technical_breakdown',
  RSI_OVERBOUGHT = 'rsi_overbought',
  RSI_OVERSOLD = 'rsi_oversold',
  MOVING_AVERAGE_CROSS = 'moving_average_cross',
  NEWS_SENTIMENT = 'news_sentiment',
  EARNINGS_DATE = 'earnings_date',
  ANALYST_UPGRADE = 'analyst_upgrade',
  ANALYST_DOWNGRADE = 'analyst_downgrade'
}

export enum AlertStatus {
  ACTIVE = 'active',
  TRIGGERED = 'triggered',
  PAUSED = 'paused',
  EXPIRED = 'expired',
  CANCELLED = 'cancelled'
}

export interface NotificationSettings {
  email: boolean;
  push: boolean;
  sms: boolean;
}

export interface AlertCondition {
  type: AlertType;
  value: number;
  operator?: string;
}

export interface AlertCreate {
  symbol: string;
  alert_type: AlertType;
  condition_value: number;
  condition_operator?: string;
  name: string;
  description?: string;
  message_template?: string;
  notification_settings?: NotificationSettings;
  expires_at?: string;
  max_triggers?: number;
  cooldown_minutes?: number;
}

export interface AlertUpdate {
  name?: string;
  description?: string;
  message_template?: string;
  condition_value?: number;
  condition_operator?: string;
  notification_settings?: NotificationSettings;
  expires_at?: string;
  max_triggers?: number;
  cooldown_minutes?: number;
}

export interface AlertTrigger {
  id: number;
  alert_id: number;
  triggered_at: string;
  trigger_value?: number;
  market_price?: number;
  message?: string;
  email_sent: boolean;
  push_sent: boolean;
  sms_sent: boolean;
}

export interface Alert {
  id: number;
  user_id: number;
  symbol: string;
  alert_type: AlertType;
  status: AlertStatus;
  condition_value?: number;
  condition_operator?: string;
  name: string;
  description?: string;
  message_template?: string;
  notify_email: boolean;
  notify_push: boolean;
  notify_sms: boolean;
  expires_at?: string;
  max_triggers: number;
  trigger_count: number;
  cooldown_minutes: number;
  created_at: string;
  updated_at: string;
  last_checked_at?: string;
  last_triggered_at?: string;
  triggers?: AlertTrigger[];
}

export interface AlertStats {
  total_alerts: number;
  active_alerts: number;
  paused_alerts: number;
  triggered_alerts: number;
  recent_triggers: Array<{
    alert_id: number;
    triggered_at: string;
    message: string;
  }>;
}

export interface PriceAlertQuickCreate {
  symbol: string;
  target_price: number;
  alert_when: 'above' | 'below';
  name?: string;
}

export interface AlertTestRequest {
  alert_id: number;
  force_trigger?: boolean;
}

export interface AlertTestResponse {
  alert_id: number;
  symbol: string;
  current_conditions: Record<string, any>;
  would_trigger: boolean;
  trigger_reason?: string;
  test_timestamp: string;
}

export interface AlertNotificationTest {
  notification_types: string[];
}

export interface AlertNotificationTestResponse {
  results: Record<string, boolean>;
  timestamp: string;
  message: string;
}

// UI-specific types

export interface AlertFormData {
  symbol: string;
  alertType: AlertType;
  conditionValue: string;
  conditionOperator: string;
  name: string;
  description: string;
  messageTemplate: string;
  notificationSettings: NotificationSettings;
  expiresAt: string;
  maxTriggers: string;
  cooldownMinutes: string;
}

export interface AlertListFilters {
  status?: AlertStatus;
  symbol?: string;
  alertType?: AlertType;
}

export interface AlertFormErrors {
  symbol?: string;
  conditionValue?: string;
  name?: string;
  expiresAt?: string;
  maxTriggers?: string;
  cooldownMinutes?: string;
}

// WebSocket message types for real-time updates

export interface AlertWebSocketMessage {
  type: 'alert_triggered';
  alert_id: number;
  symbol: string;
  message: string;
  trigger_data: Record<string, any>;
  timestamp: string;
}

export interface AlertStatusUpdate {
  type: 'alert_status_update';
  alert_id: number;
  old_status: AlertStatus;
  new_status: AlertStatus;
  timestamp: string;
}

// Alert type display information

export const ALERT_TYPE_LABELS: Record<AlertType, string> = {
  [AlertType.PRICE_ABOVE]: 'Price Above',
  [AlertType.PRICE_BELOW]: 'Price Below',
  [AlertType.PRICE_CHANGE_PERCENT]: 'Price Change %',
  [AlertType.VOLUME_SPIKE]: 'Volume Spike',
  [AlertType.TECHNICAL_BREAKOUT]: 'Technical Breakout',
  [AlertType.TECHNICAL_BREAKDOWN]: 'Technical Breakdown',
  [AlertType.RSI_OVERBOUGHT]: 'RSI Overbought',
  [AlertType.RSI_OVERSOLD]: 'RSI Oversold',
  [AlertType.MOVING_AVERAGE_CROSS]: 'Moving Average Cross',
  [AlertType.NEWS_SENTIMENT]: 'News Sentiment',
  [AlertType.EARNINGS_DATE]: 'Earnings Date',
  [AlertType.ANALYST_UPGRADE]: 'Analyst Upgrade',
  [AlertType.ANALYST_DOWNGRADE]: 'Analyst Downgrade'
};

export const ALERT_STATUS_LABELS: Record<AlertStatus, string> = {
  [AlertStatus.ACTIVE]: 'Active',
  [AlertStatus.TRIGGERED]: 'Triggered',
  [AlertStatus.PAUSED]: 'Paused',
  [AlertStatus.EXPIRED]: 'Expired',
  [AlertStatus.CANCELLED]: 'Cancelled'
};

export const ALERT_STATUS_COLORS: Record<AlertStatus, string> = {
  [AlertStatus.ACTIVE]: 'green',
  [AlertStatus.TRIGGERED]: 'blue',
  [AlertStatus.PAUSED]: 'yellow',
  [AlertStatus.EXPIRED]: 'gray',
  [AlertStatus.CANCELLED]: 'red'
};