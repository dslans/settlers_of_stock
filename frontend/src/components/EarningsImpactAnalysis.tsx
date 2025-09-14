/**
 * Earnings Impact Analysis Component
 * Shows historical earnings performance patterns and predictions.
 */

import React, { useState, useEffect } from 'react';
import {
  EarningsImpactAnalysis,
  EarningsEvent,
  EarningsHistoricalPerformance,
  formatEarningsDate,
  formatEarningsTime,
  getDaysUntilText
} from '../types/earnings';
import { earningsService } from '../services/earnings';
import './EarningsImpactAnalysis.css';

interface EarningsImpactAnalysisProps {
  symbol: string;
  onAnalysisUpdate?: (analysis: EarningsImpactAnalysis) => void;
}

export const EarningsImpactAnalysisComponent: React.FC<EarningsImpactAnalysisProps> = ({
  symbol,
  onAnalysisUpdate
}) => {
  const [analysis, setAnalysis] = useState<EarningsImpactAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (symbol) {
      fetchAnalysis();
    }
  }, [symbol]);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const analysisData = await earningsService.getEarningsImpactAnalysis(symbol);
      setAnalysis(analysisData);
      onAnalysisUpdate?.(analysisData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch earnings impact analysis');
    } finally {
      setLoading(false);
    }
  };

  const formatPercentage = (value?: number): string => {
    if (value === undefined || value === null) return 'N/A';
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatNumber = (value?: number): string => {
    if (value === undefined || value === null) return 'N/A';
    return value.toFixed(2);
  };

  const getRiskLevelColor = (riskLevel?: string): string => {
    switch (riskLevel) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getVolatilityColor = (volatility?: string): string => {
    switch (volatility) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const renderUpcomingEarnings = (earnings: EarningsEvent) => (
    <div className="upcoming-earnings-card">
      <div className="card-header">
        <h3>Upcoming Earnings</h3>
        <span className="earnings-date">
          {formatEarningsDate(earnings.earnings_date)}
        </span>
      </div>
      
      <div className="earnings-details">
        <div className="detail-row">
          <span className="label">Report Time:</span>
          <span className="value">{formatEarningsTime(earnings.report_time)}</span>
        </div>
        
        {earnings.fiscal_quarter && (
          <div className="detail-row">
            <span className="label">Fiscal Period:</span>
            <span className="value">{earnings.fiscal_quarter} {earnings.fiscal_year}</span>
          </div>
        )}
        
        {earnings.days_until_earnings !== undefined && (
          <div className="detail-row">
            <span className="label">Time Until:</span>
            <span className="value countdown">
              {getDaysUntilText(earnings.days_until_earnings)}
            </span>
          </div>
        )}
        
        {earnings.eps_estimate && (
          <div className="detail-row">
            <span className="label">EPS Estimate:</span>
            <span className="value">${earnings.eps_estimate.toFixed(2)}</span>
          </div>
        )}
        
        {earnings.revenue_estimate && (
          <div className="detail-row">
            <span className="label">Revenue Estimate:</span>
            <span className="value">${(earnings.revenue_estimate / 1e9).toFixed(2)}B</span>
          </div>
        )}
      </div>
    </div>
  );

  const renderHistoricalPerformance = (performance: EarningsHistoricalPerformance[]) => (
    <div className="historical-performance-card">
      <div className="card-header">
        <h3>Historical Earnings Performance</h3>
        <span className="performance-count">
          {performance.length} past earnings
        </span>
      </div>
      
      <div className="performance-list">
        {performance.slice(0, 5).map((perf, index) => (
          <div key={perf.id} className="performance-item">
            <div className="performance-date">
              {formatEarningsDate(perf.created_at)}
            </div>
            
            <div className="performance-metrics">
              {perf.price_change_1d !== undefined && (
                <div className="metric">
                  <span className="metric-label">1D Change:</span>
                  <span className={`metric-value ${perf.price_change_1d >= 0 ? 'positive' : 'negative'}`}>
                    {formatPercentage(perf.price_change_1d)}
                  </span>
                </div>
              )}
              
              {perf.price_change_1w !== undefined && (
                <div className="metric">
                  <span className="metric-label">1W Change:</span>
                  <span className={`metric-value ${perf.price_change_1w >= 0 ? 'positive' : 'negative'}`}>
                    {formatPercentage(perf.price_change_1w)}
                  </span>
                </div>
              )}
              
              {perf.beat_estimate !== undefined && (
                <div className="metric">
                  <span className="metric-label">Beat Est:</span>
                  <span className={`metric-value ${perf.beat_estimate ? 'positive' : 'negative'}`}>
                    {perf.beat_estimate ? 'Yes' : 'No'}
                  </span>
                </div>
              )}
              
              {perf.surprise_magnitude !== undefined && (
                <div className="metric">
                  <span className="metric-label">Surprise:</span>
                  <span className={`metric-value ${perf.surprise_magnitude >= 0 ? 'positive' : 'negative'}`}>
                    ${perf.surprise_magnitude.toFixed(2)}
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {performance.length > 5 && (
          <div className="show-more">
            <button className="show-more-btn">
              Show {performance.length - 5} more earnings
            </button>
          </div>
        )}
      </div>
    </div>
  );

  const renderAnalysisMetrics = (analysis: EarningsImpactAnalysis) => (
    <div className="analysis-metrics-card">
      <div className="card-header">
        <h3>Analysis Metrics</h3>
      </div>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-title">Avg 1-Day Change</div>
          <div className={`metric-value large ${(analysis.avg_price_change_1d || 0) >= 0 ? 'positive' : 'negative'}`}>
            {formatPercentage(analysis.avg_price_change_1d)}
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-title">Avg 1-Week Change</div>
          <div className={`metric-value large ${(analysis.avg_price_change_1w || 0) >= 0 ? 'positive' : 'negative'}`}>
            {formatPercentage(analysis.avg_price_change_1w)}
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-title">Beat Rate</div>
          <div className="metric-value large">
            {analysis.beat_rate ? `${analysis.beat_rate.toFixed(0)}%` : 'N/A'}
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-title">Avg Volume Change</div>
          <div className="metric-value large">
            {formatPercentage(analysis.avg_volume_change)}
          </div>
        </div>
      </div>
    </div>
  );

  const renderPredictions = (analysis: EarningsImpactAnalysis) => (
    <div className="predictions-card">
      <div className="card-header">
        <h3>Earnings Predictions</h3>
      </div>
      
      <div className="predictions-content">
        <div className="prediction-item">
          <div className="prediction-label">Expected Volatility</div>
          <div 
            className="prediction-value"
            style={{ color: getVolatilityColor(analysis.expected_volatility) }}
          >
            {analysis.expected_volatility?.toUpperCase() || 'UNKNOWN'}
          </div>
        </div>
        
        <div className="prediction-item">
          <div className="prediction-label">Risk Level</div>
          <div 
            className="prediction-value"
            style={{ color: getRiskLevelColor(analysis.risk_level) }}
          >
            {analysis.risk_level?.toUpperCase() || 'UNKNOWN'}
          </div>
        </div>
        
        {analysis.volatility_increase !== undefined && (
          <div className="prediction-item">
            <div className="prediction-label">Volatility Increase</div>
            <div className="prediction-value">
              {formatPercentage(analysis.volatility_increase)}
            </div>
          </div>
        )}
      </div>
      
      {analysis.key_metrics_to_watch.length > 0 && (
        <div className="key-metrics">
          <div className="key-metrics-title">Key Metrics to Watch</div>
          <div className="key-metrics-list">
            {analysis.key_metrics_to_watch.map((metric, index) => (
              <span key={index} className="key-metric-tag">
                {metric}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="earnings-impact-analysis loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <span>Loading earnings impact analysis...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="earnings-impact-analysis error">
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
          <button onClick={fetchAnalysis} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="earnings-impact-analysis empty">
        <div className="empty-state">
          <span className="empty-icon">📊</span>
          <span>No earnings impact analysis available for {symbol}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="earnings-impact-analysis">
      <div className="analysis-header">
        <h2>Earnings Impact Analysis - {symbol}</h2>
        <button onClick={fetchAnalysis} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>
      
      <div className="analysis-content">
        {analysis.upcoming_earnings && renderUpcomingEarnings(analysis.upcoming_earnings)}
        
        {renderAnalysisMetrics(analysis)}
        
        {renderPredictions(analysis)}
        
        {analysis.historical_performance.length > 0 && 
          renderHistoricalPerformance(analysis.historical_performance)
        }
      </div>
    </div>
  );
};

export default EarningsImpactAnalysisComponent;