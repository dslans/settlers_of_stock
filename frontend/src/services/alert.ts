/**
 * Alert service for API communication
 */

import { api } from './api';
import {
  Alert,
  AlertCreate,
  AlertUpdate,
  AlertStats,
  PriceAlertQuickCreate,
  AlertTestRequest,
  AlertTestResponse,
  AlertNotificationTest,
  AlertNotificationTestResponse,
  AlertStatus
} from '../types/alert';

export class AlertService {
  private baseUrl = '/alerts';

  /**
   * Create a new alert
   */
  async createAlert(alertData: AlertCreate): Promise<Alert> {
    const response = await api.post<Alert>(this.baseUrl, alertData);
    return response.data;
  }

  /**
   * Create a quick price alert
   */
  async createQuickPriceAlert(quickAlert: PriceAlertQuickCreate): Promise<Alert> {
    const response = await api.post<Alert>(`${this.baseUrl}/quick-price`, quickAlert);
    return response.data;
  }

  /**
   * Get all alerts for the current user
   */
  async getUserAlerts(statusFilter?: AlertStatus): Promise<Alert[]> {
    const params = statusFilter ? { status_filter: statusFilter } : {};
    const response = await api.get<Alert[]>(this.baseUrl, { params });
    return response.data;
  }

  /**
   * Get alert statistics
   */
  async getAlertStats(): Promise<AlertStats> {
    const response = await api.get<AlertStats>(`${this.baseUrl}/stats`);
    return response.data;
  }

  /**
   * Get a specific alert by ID
   */
  async getAlert(alertId: number): Promise<Alert> {
    const response = await api.get<Alert>(`${this.baseUrl}/${alertId}`);
    return response.data;
  }

  /**
   * Update an alert
   */
  async updateAlert(alertId: number, updateData: AlertUpdate): Promise<Alert> {
    const response = await api.put<Alert>(`${this.baseUrl}/${alertId}`, updateData);
    return response.data;
  }

  /**
   * Delete an alert
   */
  async deleteAlert(alertId: number): Promise<void> {
    await api.delete(`${this.baseUrl}/${alertId}`);
  }

  /**
   * Pause an alert
   */
  async pauseAlert(alertId: number): Promise<Alert> {
    const response = await api.post<Alert>(`${this.baseUrl}/${alertId}/pause`);
    return response.data;
  }

  /**
   * Resume a paused alert
   */
  async resumeAlert(alertId: number): Promise<Alert> {
    const response = await api.post<Alert>(`${this.baseUrl}/${alertId}/resume`);
    return response.data;
  }

  /**
   * Test an alert's conditions
   */
  async testAlert(testRequest: AlertTestRequest): Promise<AlertTestResponse> {
    const response = await api.post<AlertTestResponse>(
      `${this.baseUrl}/${testRequest.alert_id}/test`,
      testRequest
    );
    return response.data;
  }

  /**
   * Test notification delivery
   */
  async testNotifications(testRequest: AlertNotificationTest): Promise<AlertNotificationTestResponse> {
    const response = await api.post<AlertNotificationTestResponse>(
      `${this.baseUrl}/test-notifications`,
      testRequest
    );
    return response.data;
  }

  /**
   * Trigger alert processing (admin function)
   */
  async triggerAlertProcessing(): Promise<{ message: string; task_id: string; timestamp: string }> {
    const response = await api.post<{ message: string; task_id: string; timestamp: string }>(
      `${this.baseUrl}/system/process-all`
    );
    return response.data;
  }

  /**
   * Get alert system health
   */
  async getSystemHealth(): Promise<any> {
    const response = await api.get(`${this.baseUrl}/system/health`);
    return response.data;
  }

  /**
   * Format alert condition for display
   */
  formatAlertCondition(alert: Alert): string {
    const { alert_type, condition_value, condition_operator } = alert;
    
    switch (alert_type) {
      case 'price_above':
        return `Price >= $${condition_value}`;
      case 'price_below':
        return `Price <= $${condition_value}`;
      case 'price_change_percent':
        return `Price change >= ${condition_value}%`;
      case 'volume_spike':
        return `Volume >= ${condition_value}x average`;
      case 'rsi_overbought':
        return `RSI >= ${condition_value}`;
      case 'rsi_oversold':
        return `RSI <= ${condition_value}`;
      default:
        return `${condition_operator || '>='} ${condition_value}`;
    }
  }

  /**
   * Get alert type description
   */
  getAlertTypeDescription(alertType: string): string {
    const descriptions: Record<string, string> = {
      'price_above': 'Alert when stock price goes above target',
      'price_below': 'Alert when stock price goes below target',
      'price_change_percent': 'Alert when price changes by percentage',
      'volume_spike': 'Alert when volume spikes above average',
      'technical_breakout': 'Alert on technical breakout patterns',
      'technical_breakdown': 'Alert on technical breakdown patterns',
      'rsi_overbought': 'Alert when RSI indicates overbought conditions',
      'rsi_oversold': 'Alert when RSI indicates oversold conditions',
      'moving_average_cross': 'Alert on moving average crossovers',
      'news_sentiment': 'Alert on significant news sentiment changes',
      'earnings_date': 'Alert before earnings announcements',
      'analyst_upgrade': 'Alert on analyst upgrades',
      'analyst_downgrade': 'Alert on analyst downgrades'
    };
    
    return descriptions[alertType] || 'Custom alert condition';
  }

  /**
   * Validate alert form data
   */
  validateAlertData(data: Partial<AlertCreate>): string[] {
    const errors: string[] = [];

    if (!data.symbol || data.symbol.trim().length === 0) {
      errors.push('Stock symbol is required');
    }

    if (!data.name || data.name.trim().length === 0) {
      errors.push('Alert name is required');
    }

    if (!data.condition_value || data.condition_value <= 0) {
      errors.push('Condition value must be greater than 0');
    }

    if (data.max_triggers && (data.max_triggers < 1 || data.max_triggers > 100)) {
      errors.push('Max triggers must be between 1 and 100');
    }

    if (data.cooldown_minutes && (data.cooldown_minutes < 0 || data.cooldown_minutes > 1440)) {
      errors.push('Cooldown must be between 0 and 1440 minutes');
    }

    if (data.expires_at) {
      const expirationDate = new Date(data.expires_at);
      if (expirationDate <= new Date()) {
        errors.push('Expiration date must be in the future');
      }
    }

    return errors;
  }

  /**
   * Get default notification settings
   */
  getDefaultNotificationSettings() {
    return {
      email: true,
      push: true,
      sms: false
    };
  }

  /**
   * Format time remaining until expiration
   */
  formatTimeUntilExpiration(expiresAt: string): string {
    const now = new Date();
    const expiration = new Date(expiresAt);
    const diff = expiration.getTime() - now.getTime();

    if (diff <= 0) {
      return 'Expired';
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (days > 0) {
      return `${days}d ${hours}h`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  }

  /**
   * Check if alert is in cooldown
   */
  isInCooldown(alert: Alert): boolean {
    if (!alert.last_triggered_at || alert.cooldown_minutes === 0) {
      return false;
    }

    const lastTriggered = new Date(alert.last_triggered_at);
    const cooldownEnd = new Date(lastTriggered.getTime() + alert.cooldown_minutes * 60 * 1000);
    
    return new Date() < cooldownEnd;
  }

  /**
   * Get cooldown remaining time
   */
  getCooldownRemaining(alert: Alert): string | null {
    if (!this.isInCooldown(alert)) {
      return null;
    }

    const lastTriggered = new Date(alert.last_triggered_at!);
    const cooldownEnd = new Date(lastTriggered.getTime() + alert.cooldown_minutes * 60 * 1000);
    const remaining = cooldownEnd.getTime() - new Date().getTime();

    const minutes = Math.ceil(remaining / (1000 * 60));
    return `${minutes}m`;
  }
}

// Export singleton instance
export const alertService = new AlertService();