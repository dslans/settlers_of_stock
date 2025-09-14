/**
 * Alert Form Component - Advanced interface for creating detailed alerts
 */

import React, { useState } from 'react';
import {
  Alert,
  AlertCreate,
  AlertType,
  AlertFormData,
  AlertFormErrors,
  ALERT_TYPE_LABELS
} from '../types/alert';
import { alertService } from '../services/alert';
import './AlertForm.css';

interface AlertFormProps {
  onAlertCreated: (alert: Alert) => void;
  onCancel: () => void;
  initialData?: Partial<AlertCreate>;
}

export const AlertForm: React.FC<AlertFormProps> = ({
  onAlertCreated,
  onCancel,
  initialData
}) => {
  const [formData, setFormData] = useState<AlertFormData>({
    symbol: initialData?.symbol || '',
    alertType: initialData?.alert_type || AlertType.PRICE_ABOVE,
    conditionValue: initialData?.condition_value?.toString() || '',
    conditionOperator: initialData?.condition_operator || '>=',
    name: initialData?.name || '',
    description: initialData?.description || '',
    messageTemplate: initialData?.message_template || '',
    notificationSettings: initialData?.notification_settings || {
      email: true,
      push: true,
      sms: false
    },
    expiresAt: initialData?.expires_at || '',
    maxTriggers: initialData?.max_triggers?.toString() || '1',
    cooldownMinutes: initialData?.cooldown_minutes?.toString() || '60'
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<AlertFormErrors>({});

  const handleInputChange = (field: keyof AlertFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error when user starts typing
    if (errors[field as keyof AlertFormErrors]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }

    // Auto-generate name if not manually set
    if (field !== 'name' && !formData.name) {
      generateAlertName();
    }
  };

  const generateAlertName = () => {
    const symbol = formData.symbol;
    const type = ALERT_TYPE_LABELS[formData.alertType];
    const value = formData.conditionValue;

    if (symbol && value) {
      const name = `${symbol} ${type} ${value}`;
      setFormData(prev => ({ ...prev, name }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: AlertFormErrors = {};

    if (!formData.symbol.trim()) {
      newErrors.symbol = 'Stock symbol is required';
    }

    if (!formData.conditionValue || parseFloat(formData.conditionValue) <= 0) {
      newErrors.conditionValue = 'Condition value must be greater than 0';
    }

    if (!formData.name.trim()) {
      newErrors.name = 'Alert name is required';
    }

    if (formData.expiresAt) {
      const expirationDate = new Date(formData.expiresAt);
      if (expirationDate <= new Date()) {
        newErrors.expiresAt = 'Expiration date must be in the future';
      }
    }

    const maxTriggers = parseInt(formData.maxTriggers);
    if (isNaN(maxTriggers) || maxTriggers < 1 || maxTriggers > 100) {
      newErrors.maxTriggers = 'Max triggers must be between 1 and 100';
    }

    const cooldownMinutes = parseInt(formData.cooldownMinutes);
    if (isNaN(cooldownMinutes) || cooldownMinutes < 0 || cooldownMinutes > 1440) {
      newErrors.cooldownMinutes = 'Cooldown must be between 0 and 1440 minutes';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);

      const alertData: AlertCreate = {
        symbol: formData.symbol.toUpperCase().trim(),
        alert_type: formData.alertType,
        condition_value: parseFloat(formData.conditionValue),
        condition_operator: formData.conditionOperator,
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        message_template: formData.messageTemplate.trim() || undefined,
        notification_settings: formData.notificationSettings,
        expires_at: formData.expiresAt || undefined,
        max_triggers: parseInt(formData.maxTriggers),
        cooldown_minutes: parseInt(formData.cooldownMinutes)
      };

      const alert = await alertService.createAlert(alertData);
      onAlertCreated(alert);
    } catch (err: any) {
      console.error('Error creating alert:', err);
      
      if (err.response?.data?.detail) {
        if (err.response.data.detail.includes('Invalid stock symbol')) {
          setErrors({ symbol: err.response.data.detail });
        } else {
          setErrors({ symbol: err.response.data.detail });
        }
      } else {
        setErrors({ symbol: 'Failed to create alert. Please try again.' });
      }
    } finally {
      setLoading(false);
    }
  };

  const getAlertTypeDescription = (alertType: AlertType): string => {
    return alertService.getAlertTypeDescription(alertType);
  };

  const getOperatorOptions = (alertType: AlertType): Array<{ value: string; label: string }> => {
    switch (alertType) {
      case AlertType.PRICE_ABOVE:
        return [{ value: '>=', label: 'Greater than or equal to' }];
      case AlertType.PRICE_BELOW:
        return [{ value: '<=', label: 'Less than or equal to' }];
      case AlertType.PRICE_CHANGE_PERCENT:
        return [
          { value: '>=', label: 'Greater than or equal to' },
          { value: '<=', label: 'Less than or equal to' }
        ];
      default:
        return [
          { value: '>=', label: 'Greater than or equal to' },
          { value: '<=', label: 'Less than or equal to' },
          { value: '>', label: 'Greater than' },
          { value: '<', label: 'Less than' },
          { value: '==', label: 'Equal to' }
        ];
    }
  };

  const getConditionValueLabel = (alertType: AlertType): string => {
    switch (alertType) {
      case AlertType.PRICE_ABOVE:
      case AlertType.PRICE_BELOW:
        return 'Price ($)';
      case AlertType.PRICE_CHANGE_PERCENT:
        return 'Percentage (%)';
      case AlertType.VOLUME_SPIKE:
        return 'Volume Multiplier (x)';
      case AlertType.RSI_OVERBOUGHT:
      case AlertType.RSI_OVERSOLD:
        return 'RSI Value';
      default:
        return 'Value';
    }
  };

  return (
    <div className="alert-form">
      <div className="form-header">
        <h3>Create Advanced Alert</h3>
        <p>Set up detailed alert conditions and notification preferences</p>
      </div>

      <form onSubmit={handleSubmit} className="advanced-alert-form">
        <div className="form-section">
          <h4>Basic Information</h4>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="symbol">Stock Symbol *</label>
              <input
                id="symbol"
                type="text"
                value={formData.symbol}
                onChange={(e) => handleInputChange('symbol', e.target.value.toUpperCase())}
                placeholder="e.g., AAPL"
                className={errors.symbol ? 'error' : ''}
                maxLength={5}
              />
              {errors.symbol && <span className="error-text">{errors.symbol}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="name">Alert Name *</label>
              <input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder="Enter a descriptive name"
                className={errors.name ? 'error' : ''}
                maxLength={255}
              />
              {errors.name && <span className="error-text">{errors.name}</span>}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="description">Description (Optional)</label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Add notes about this alert"
              maxLength={1000}
              rows={3}
            />
          </div>
        </div>

        <div className="form-section">
          <h4>Alert Conditions</h4>
          
          <div className="form-group">
            <label htmlFor="alertType">Alert Type *</label>
            <select
              id="alertType"
              value={formData.alertType}
              onChange={(e) => handleInputChange('alertType', e.target.value as AlertType)}
            >
              {Object.values(AlertType).map(type => (
                <option key={type} value={type}>
                  {ALERT_TYPE_LABELS[type]}
                </option>
              ))}
            </select>
            <div className="alert-type-description">
              {getAlertTypeDescription(formData.alertType)}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="conditionOperator">Condition</label>
              <select
                id="conditionOperator"
                value={formData.conditionOperator}
                onChange={(e) => handleInputChange('conditionOperator', e.target.value)}
              >
                {getOperatorOptions(formData.alertType).map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="conditionValue">{getConditionValueLabel(formData.alertType)} *</label>
              <input
                id="conditionValue"
                type="number"
                value={formData.conditionValue}
                onChange={(e) => handleInputChange('conditionValue', e.target.value)}
                placeholder="0.00"
                min="0.01"
                step="0.01"
                className={errors.conditionValue ? 'error' : ''}
              />
              {errors.conditionValue && <span className="error-text">{errors.conditionValue}</span>}
            </div>
          </div>
        </div>

        <div className="form-section">
          <h4>Notification Settings</h4>
          
          <div className="notification-checkboxes">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.notificationSettings.email}
                onChange={(e) => handleInputChange('notificationSettings', {
                  ...formData.notificationSettings,
                  email: e.target.checked
                })}
              />
              <span>📧 Email notifications</span>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.notificationSettings.push}
                onChange={(e) => handleInputChange('notificationSettings', {
                  ...formData.notificationSettings,
                  push: e.target.checked
                })}
              />
              <span>📱 Push notifications</span>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.notificationSettings.sms}
                onChange={(e) => handleInputChange('notificationSettings', {
                  ...formData.notificationSettings,
                  sms: e.target.checked
                })}
              />
              <span>💬 SMS notifications</span>
            </label>
          </div>

          <div className="form-group">
            <label htmlFor="messageTemplate">Custom Message Template (Optional)</label>
            <textarea
              id="messageTemplate"
              value={formData.messageTemplate}
              onChange={(e) => handleInputChange('messageTemplate', e.target.value)}
              placeholder="Use {symbol}, {condition}, {price}, {trigger_value} as placeholders"
              maxLength={500}
              rows={3}
            />
            <div className="template-help">
              Available placeholders: {'{symbol}'}, {'{condition}'}, {'{price}'}, {'{trigger_value}'}
            </div>
          </div>
        </div>

        <div className="form-section">
          <h4>Advanced Settings</h4>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="maxTriggers">Max Triggers *</label>
              <input
                id="maxTriggers"
                type="number"
                value={formData.maxTriggers}
                onChange={(e) => handleInputChange('maxTriggers', e.target.value)}
                min="1"
                max="100"
                className={errors.maxTriggers ? 'error' : ''}
              />
              {errors.maxTriggers && <span className="error-text">{errors.maxTriggers}</span>}
              <div className="field-help">How many times this alert can trigger</div>
            </div>

            <div className="form-group">
              <label htmlFor="cooldownMinutes">Cooldown (minutes) *</label>
              <input
                id="cooldownMinutes"
                type="number"
                value={formData.cooldownMinutes}
                onChange={(e) => handleInputChange('cooldownMinutes', e.target.value)}
                min="0"
                max="1440"
                className={errors.cooldownMinutes ? 'error' : ''}
              />
              {errors.cooldownMinutes && <span className="error-text">{errors.cooldownMinutes}</span>}
              <div className="field-help">Minimum time between triggers</div>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="expiresAt">Expiration Date (Optional)</label>
            <input
              id="expiresAt"
              type="datetime-local"
              value={formData.expiresAt}
              onChange={(e) => handleInputChange('expiresAt', e.target.value)}
              min={new Date().toISOString().slice(0, 16)}
              className={errors.expiresAt ? 'error' : ''}
            />
            {errors.expiresAt && <span className="error-text">{errors.expiresAt}</span>}
            <div className="field-help">Leave empty for no expiration</div>
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={onCancel}
            className="cancel-btn"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="submit-btn"
            disabled={loading}
          >
            {loading ? 'Creating Alert...' : 'Create Alert'}
          </button>
        </div>
      </form>
    </div>
  );
};