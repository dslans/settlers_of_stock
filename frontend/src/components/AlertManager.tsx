/**
 * Alert Manager Component - Main interface for managing stock alerts
 */

import React, { useState, useEffect } from 'react';
import {
  Alert,
  AlertStatus,
  AlertStats,
  ALERT_STATUS_LABELS,
  ALERT_STATUS_COLORS
} from '../types/alert';
import { alertService } from '../services/alert';
import { AlertList } from './AlertList';
import { AlertForm } from './AlertForm';
import { QuickPriceAlert } from './QuickPriceAlert';
import './AlertManager.css';

interface AlertManagerProps {
  className?: string;
}

export const AlertManager: React.FC<AlertManagerProps> = ({ className }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'list' | 'create' | 'quick'>('list');
  const [statusFilter, setStatusFilter] = useState<AlertStatus | undefined>(undefined);
  const [refreshing, setRefreshing] = useState(false);

  // Load alerts and stats on component mount
  useEffect(() => {
    loadAlertsAndStats();
  }, [statusFilter]);

  const loadAlertsAndStats = async () => {
    try {
      setLoading(true);
      setError(null);

      const [alertsData, statsData] = await Promise.all([
        alertService.getUserAlerts(statusFilter),
        alertService.getAlertStats()
      ]);

      setAlerts(alertsData);
      setStats(statsData);
    } catch (err) {
      console.error('Error loading alerts:', err);
      setError('Failed to load alerts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAlertsAndStats();
    setRefreshing(false);
  };

  const handleAlertCreated = (newAlert: Alert) => {
    setAlerts(prev => [newAlert, ...prev]);
    setActiveTab('list');
    // Refresh stats
    loadAlertsAndStats();
  };

  const handleAlertUpdated = (updatedAlert: Alert) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === updatedAlert.id ? updatedAlert : alert
    ));
  };

  const handleAlertDeleted = (alertId: number) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
    // Refresh stats
    loadAlertsAndStats();
  };

  const handleStatusToggle = async (alert: Alert) => {
    try {
      let updatedAlert: Alert;
      
      if (alert.status === AlertStatus.ACTIVE) {
        updatedAlert = await alertService.pauseAlert(alert.id);
      } else if (alert.status === AlertStatus.PAUSED) {
        updatedAlert = await alertService.resumeAlert(alert.id);
      } else {
        return; // Can't toggle other statuses
      }

      handleAlertUpdated(updatedAlert);
    } catch (err) {
      console.error('Error toggling alert status:', err);
      setError('Failed to update alert status');
    }
  };

  const renderStats = () => {
    if (!stats) return null;

    return (
      <div className="alert-stats">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total_alerts}</div>
            <div className="stat-label">Total Alerts</div>
          </div>
          <div className="stat-card active">
            <div className="stat-value">{stats.active_alerts}</div>
            <div className="stat-label">Active</div>
          </div>
          <div className="stat-card paused">
            <div className="stat-value">{stats.paused_alerts}</div>
            <div className="stat-label">Paused</div>
          </div>
          <div className="stat-card triggered">
            <div className="stat-value">{stats.triggered_alerts}</div>
            <div className="stat-label">Triggered</div>
          </div>
        </div>
      </div>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'create':
        return (
          <AlertForm
            onAlertCreated={handleAlertCreated}
            onCancel={() => setActiveTab('list')}
          />
        );
      case 'quick':
        return (
          <QuickPriceAlert
            onAlertCreated={handleAlertCreated}
            onCancel={() => setActiveTab('list')}
          />
        );
      case 'list':
      default:
        return (
          <AlertList
            alerts={alerts}
            loading={loading}
            onAlertUpdated={handleAlertUpdated}
            onAlertDeleted={handleAlertDeleted}
            onStatusToggle={handleStatusToggle}
          />
        );
    }
  };

  if (loading && alerts.length === 0) {
    return (
      <div className={`alert-manager ${className || ''}`}>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading alerts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`alert-manager ${className || ''}`}>
      <div className="alert-manager-header">
        <h2>Stock Alerts</h2>
        <div className="header-actions">
          <button
            className="refresh-btn"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? '↻' : '⟳'} Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {renderStats()}

      <div className="alert-tabs">
        <button
          className={`tab-button ${activeTab === 'list' ? 'active' : ''}`}
          onClick={() => setActiveTab('list')}
        >
          My Alerts ({alerts.length})
        </button>
        <button
          className={`tab-button ${activeTab === 'quick' ? 'active' : ''}`}
          onClick={() => setActiveTab('quick')}
        >
          Quick Alert
        </button>
        <button
          className={`tab-button ${activeTab === 'create' ? 'active' : ''}`}
          onClick={() => setActiveTab('create')}
        >
          Advanced Alert
        </button>
      </div>

      {activeTab === 'list' && (
        <div className="alert-filters">
          <label>Filter by status:</label>
          <select
            value={statusFilter || ''}
            onChange={(e) => setStatusFilter(e.target.value as AlertStatus || undefined)}
          >
            <option value="">All Statuses</option>
            {Object.values(AlertStatus).map(status => (
              <option key={status} value={status}>
                {ALERT_STATUS_LABELS[status]}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="alert-content">
        {renderTabContent()}
      </div>
    </div>
  );
};