/**
 * Quick Price Alert Component - Simple interface for creating price alerts
 */

import React, { useState } from 'react';
import { Alert, PriceAlertQuickCreate } from '../types/alert';
import { alertService } from '../services/alert';
import './QuickPriceAlert.css';

interface QuickPriceAlertProps {
  onAlertCreated: (alert: Alert) => void;
  onCancel: () => void;
  initialSymbol?: string;
}

export const QuickPriceAlert: React.FC<QuickPriceAlertProps> = ({
  onAlertCreated,
  onCancel,
  initialSymbol = ''
}) => {
  const [formData, setFormData] = useState<PriceAlertQuickCreate>({
    symbol: initialSymbol.toUpperCase(),
    target_price: 0,
    alert_when: 'above',
    name: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleInputChange = (field: keyof PriceAlertQuickCreate, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }

    // Auto-generate name if not manually set
    if (field !== 'name' && !formData.name) {
      const symbol = field === 'symbol' ? (value as string) : formData.symbol;
      const price = field === 'target_price' ? (value as number) : formData.target_price;
      const direction = field === 'alert_when' ? (value as string) : formData.alert_when;
      
      if (symbol && price > 0) {
        setFormData(prev => ({
          ...prev,
          name: `${symbol} ${direction} $${price}`
        }));
      }
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.symbol.trim()) {
      newErrors.symbol = 'Stock symbol is required';
    } else if (!/^[A-Z]{1,5}$/.test(formData.symbol.trim())) {
      newErrors.symbol = 'Enter a valid stock symbol (1-5 letters)';
    }

    if (!formData.target_price || formData.target_price <= 0) {
      newErrors.target_price = 'Target price must be greater than 0';
    } else if (formData.target_price > 10000) {
      newErrors.target_price = 'Target price seems too high';
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
      const alert = await alertService.createQuickPriceAlert(formData);
      onAlertCreated(alert);
    } catch (err: any) {
      console.error('Error creating quick price alert:', err);
      
      if (err.response?.data?.detail) {
        if (err.response.data.detail.includes('Invalid stock symbol')) {
          setErrors({ symbol: err.response.data.detail });
        } else {
          setErrors({ general: err.response.data.detail });
        }
      } else {
        setErrors({ general: 'Failed to create alert. Please try again.' });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      symbol: '',
      target_price: 0,
      alert_when: 'above',
      name: ''
    });
    setErrors({});
  };

  return (
    <div className="quick-price-alert">
      <div className="form-header">
        <h3>Quick Price Alert</h3>
        <p>Get notified when a stock reaches your target price</p>
      </div>

      <form onSubmit={handleSubmit} className="quick-alert-form">
        {errors.general && (
          <div className="error-message general-error">
            {errors.general}
          </div>
        )}

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="symbol">Stock Symbol</label>
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
            <label htmlFor="alert_when">Alert When Price Goes</label>
            <select
              id="alert_when"
              value={formData.alert_when}
              onChange={(e) => handleInputChange('alert_when', e.target.value as 'above' | 'below')}
            >
              <option value="above">Above</option>
              <option value="below">Below</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="target_price">Target Price</label>
            <div className="price-input">
              <span className="currency-symbol">$</span>
              <input
                id="target_price"
                type="number"
                value={formData.target_price || ''}
                onChange={(e) => handleInputChange('target_price', parseFloat(e.target.value) || 0)}
                placeholder="0.00"
                min="0.01"
                step="0.01"
                className={errors.target_price ? 'error' : ''}
              />
            </div>
            {errors.target_price && <span className="error-text">{errors.target_price}</span>}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="name">Alert Name (Optional)</label>
          <input
            id="name"
            type="text"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            placeholder="Auto-generated if left empty"
            maxLength={255}
          />
        </div>

        <div className="alert-preview">
          <h4>Alert Preview</h4>
          <div className="preview-content">
            {formData.symbol && formData.target_price > 0 ? (
              <p>
                You will be notified when <strong>{formData.symbol}</strong> goes{' '}
                <strong>{formData.alert_when}</strong> <strong>${formData.target_price}</strong>
              </p>
            ) : (
              <p className="preview-placeholder">
                Fill in the details above to see your alert preview
              </p>
            )}
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
            type="button"
            onClick={handleReset}
            className="reset-btn"
            disabled={loading}
          >
            Reset
          </button>
          <button
            type="submit"
            className="submit-btn"
            disabled={loading || !formData.symbol || !formData.target_price}
          >
            {loading ? 'Creating...' : 'Create Alert'}
          </button>
        </div>
      </form>

      <div className="quick-alert-tips">
        <h4>💡 Tips</h4>
        <ul>
          <li>Use standard stock symbols (e.g., AAPL for Apple, TSLA for Tesla)</li>
          <li>Set realistic target prices based on current market conditions</li>
          <li>You'll receive notifications via email and push notifications</li>
          <li>Alerts are checked every minute during market hours</li>
        </ul>
      </div>
    </div>
  );
};