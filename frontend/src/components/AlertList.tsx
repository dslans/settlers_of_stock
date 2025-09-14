/**
 * Alert List Component - Displays and manages a list of alerts
 */

import React, { useState } from 'react';
import {
  Alert,
  AlertStatus,
  ALERT_TYPE_LABELS,
  ALERT_STATUS_LABELS,
  ALERT_STATUS_COLORS
} from '../types/alert';
import { alertService } from '../services/alert';
import './AlertList.css';

interface AlertListProps {
  alerts: Alert[];
  loading: boolean;
  onAlertUpdated: (alert: Alert) => void;
  onAlertDeleted: (alertId: number) => void;
  onStatusToggle: (alert: Alert) => void;
}

export const AlertList: React.FC<AlertListProps> = ({
  alerts,
  loading,
  onAlertUpdated,
  onAlertDeleted,
  onStatusToggle
}) => {
  const [expandedAlert, setExpandedAlert] = useState<number | null>(null);
  const [testingAlert, setTestingAlert] = useState<number | null>(null);
  const [deletingAlert, setDeletingAlert] = useState<number | null>(null);

  const handleDeleteAlert = async (alertId: number) => {
    if (!window.confirm('Are you sure you want to delete this alert?')) {
      return;
    }

    try {
      setDeletingAlert(alertId);
      await alertService.deleteAlert(alertId);
      onAlertDeleted(alertId);
    } catch (err) {
      console.error('Error deleting alert:', err);
      alert('Failed to delete alert. Please try again.');
    } finally {
      setDeletingAlert(null);
    }
  };

  const handleTestAlert = async (alert: Alert) => {
    try {
      setTestingAlert(alert.id);
      const result = await alertService.testAlert({
        alert_id: alert.id,
        force_trigger: false
      });

      const message = result.would_trigger
        ? `✅ Alert would trigger: ${result.trigger_reason}`
        : `ℹ️ Alert would not trigger: ${result.trigger_reason}`;

      alert(message);
    } catch (err) {
      console.error('Error testing alert:', err);
      alert('Failed to test alert. Please try again.');
    } finally {
      setTestingAlert(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const getStatusBadgeClass = (status: AlertStatus) => {
    return `status-badge status-${ALERT_STATUS_COLORS[status]}`;
  };

  const canToggleStatus = (status: AlertStatus) => {
    return status === AlertStatus.ACTIVE || status === AlertStatus.PAUSED;
  };

  const getToggleButtonText = (status: AlertStatus) => {
    return status === AlertStatus.ACTIVE ? 'Pause' : 'Resume';
  };

  if (loading) {
    return (
      <div className="alert-list-loading">
        <div className="loading-spinner"></div>
        <p>Loading alerts...</p>
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="alert-list-empty">
        <div className="empty-state">
          <div className="empty-icon">🔔</div>
          <h3>No alerts yet</h3>
          <p>Create your first alert to get notified about stock price movements.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="alert-list">
      {alerts.map((alert) => (
        <div key={alert.id} className="alert-card">
          <div className="alert-header">
            <div className="alert-main-info">
              <div className="alert-symbol-name">
                <span className="alert-symbol">{alert.symbol}</span>
                <span className="alert-name">{alert.name}</span>
              </div>
              <div className="alert-condition">
                {alertService.formatAlertCondition(alert)}
              </div>
            </div>
            
            <div className="alert-status-actions">
              <span className={getStatusBadgeClass(alert.status)}>
                {ALERT_STATUS_LABELS[alert.status]}
              </span>
              
              <div className="alert-actions">
                {canToggleStatus(alert.status) && (
                  <button
                    className="action-btn toggle-btn"
                    onClick={() => onStatusToggle(alert)}
                    title={getToggleButtonText(alert.status)}
                  >
                    {alert.status === AlertStatus.ACTIVE ? '⏸️' : '▶️'}
                  </button>
                )}
                
                <button
                  className="action-btn test-btn"
                  onClick={() => handleTestAlert(alert)}
                  disabled={testingAlert === alert.id}
                  title="Test alert conditions"
                >
                  {testingAlert === alert.id ? '⏳' : '🧪'}
                </button>
                
                <button
                  className="action-btn expand-btn"
                  onClick={() => setExpandedAlert(
                    expandedAlert === alert.id ? null : alert.id
                  )}
                  title="View details"
                >
                  {expandedAlert === alert.id ? '▲' : '▼'}
                </button>
                
                <button
                  className="action-btn delete-btn"
                  onClick={() => handleDeleteAlert(alert.id)}
                  disabled={deletingAlert === alert.id}
                  title="Delete alert"
                >
                  {deletingAlert === alert.id ? '⏳' : '🗑️'}
                </button>
              </div>
            </div>
          </div>

          {expandedAlert === alert.id && (
            <div className="alert-details">
              <div className="details-grid">
                <div className="detail-section">
                  <h4>Alert Information</h4>
                  <div className="detail-row">
                    <span className="detail-label">Type:</span>
                    <span className="detail-value">
                      {ALERT_TYPE_LABELS[alert.alert_type]}
                    </span>
                  </div>
                  {alert.description && (
                    <div className="detail-row">
                      <span className="detail-label">Description:</span>
                      <span className="detail-value">{alert.description}</span>
                    </div>
                  )}
                  <div className="detail-row">
                    <span className="detail-label">Created:</span>
                    <span className="detail-value">{formatDate(alert.created_at)}</span>
                  </div>
                  {alert.expires_at && (
                    <div className="detail-row">
                      <span className="detail-label">Expires:</span>
                      <span className="detail-value">
                        {formatDate(alert.expires_at)}
                        <span className="time-remaining">
                          ({alertService.formatTimeUntilExpiration(alert.expires_at)})
                        </span>
                      </span>
                    </div>
                  )}
                </div>

                <div className="detail-section">
                  <h4>Trigger Settings</h4>
                  <div className="detail-row">
                    <span className="detail-label">Max Triggers:</span>
                    <span className="detail-value">
                      {alert.trigger_count} / {alert.max_triggers}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Cooldown:</span>
                    <span className="detail-value">{alert.cooldown_minutes} minutes</span>
                  </div>
                  {alert.last_triggered_at && (
                    <div className="detail-row">
                      <span className="detail-label">Last Triggered:</span>
                      <span className="detail-value">
                        {formatDate(alert.last_triggered_at)}
                        {alertService.isInCooldown(alert) && (
                          <span className="cooldown-indicator">
                            (Cooldown: {alertService.getCooldownRemaining(alert)})
                          </span>
                        )}
                      </span>
                    </div>
                  )}
                  {alert.last_checked_at && (
                    <div className="detail-row">
                      <span className="detail-label">Last Checked:</span>
                      <span className="detail-value">{formatDate(alert.last_checked_at)}</span>
                    </div>
                  )}
                </div>

                <div className="detail-section">
                  <h4>Notifications</h4>
                  <div className="notification-settings">
                    <span className={`notification-type ${alert.notify_email ? 'enabled' : 'disabled'}`}>
                      📧 Email {alert.notify_email ? '✓' : '✗'}
                    </span>
                    <span className={`notification-type ${alert.notify_push ? 'enabled' : 'disabled'}`}>
                      📱 Push {alert.notify_push ? '✓' : '✗'}
                    </span>
                    <span className={`notification-type ${alert.notify_sms ? 'enabled' : 'disabled'}`}>
                      💬 SMS {alert.notify_sms ? '✓' : '✗'}
                    </span>
                  </div>
                </div>
              </div>

              {alert.triggers && alert.triggers.length > 0 && (
                <div className="alert-triggers">
                  <h4>Recent Triggers</h4>
                  <div className="triggers-list">
                    {alert.triggers.slice(0, 5).map((trigger) => (
                      <div key={trigger.id} className="trigger-item">
                        <div className="trigger-time">
                          {formatDate(trigger.triggered_at)}
                        </div>
                        <div className="trigger-message">
                          {trigger.message}
                        </div>
                        {trigger.market_price && (
                          <div className="trigger-price">
                            Price: {formatCurrency(trigger.market_price)}
                          </div>
                        )}
                        <div className="trigger-notifications">
                          {trigger.email_sent && <span className="notification-sent">📧</span>}
                          {trigger.push_sent && <span className="notification-sent">📱</span>}
                          {trigger.sms_sent && <span className="notification-sent">💬</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};