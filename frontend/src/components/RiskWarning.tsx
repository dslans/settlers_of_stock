/**
 * Risk Warning Component
 * 
 * A compact component that displays risk warnings and can be embedded
 * in other components like chat responses, stock displays, etc.
 */

import React, { useState } from 'react';
import { riskAssessmentService, RiskMetric } from '../services/riskAssessment';
import { disclaimerService } from '../services/disclaimer';
import DisclaimerBanner from './DisclaimerBanner';
import './RiskWarning.css';

interface RiskWarningProps {
  riskLevel: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH';
  riskScore?: number;
  riskMetrics?: RiskMetric[];
  warnings?: string[];
  mitigations?: string[];
  symbol?: string;
  compact?: boolean;
  showDetails?: boolean;
}

const RiskWarning: React.FC<RiskWarningProps> = ({
  riskLevel,
  riskScore,
  riskMetrics = [],
  warnings = [],
  mitigations = [],
  symbol,
  compact = false,
  showDetails = false
}) => {
  const [expanded, setExpanded] = useState(showDetails);

  const getRiskLevelInfo = (level: string) => {
    switch (level) {
      case 'LOW':
        return {
          color: '#4CAF50',
          backgroundColor: '#E8F5E8',
          borderColor: '#4CAF50',
          icon: '🟢',
          title: 'Low Risk',
          description: 'This investment has low risk characteristics'
        };
      case 'MODERATE':
        return {
          color: '#FF9800',
          backgroundColor: '#FFF3E0',
          borderColor: '#FF9800',
          icon: '🟡',
          title: 'Moderate Risk',
          description: 'This investment carries moderate risk'
        };
      case 'HIGH':
        return {
          color: '#F44336',
          backgroundColor: '#FFEBEE',
          borderColor: '#F44336',
          icon: '🔴',
          title: 'High Risk',
          description: 'This investment has high risk - careful consideration required'
        };
      case 'VERY_HIGH':
        return {
          color: '#9C27B0',
          backgroundColor: '#F3E5F5',
          borderColor: '#9C27B0',
          icon: '🟣',
          title: 'Very High Risk',
          description: 'This investment carries very high risk - suitable only for risk-tolerant investors'
        };
      default:
        return {
          color: '#757575',
          backgroundColor: '#F5F5F5',
          borderColor: '#757575',
          icon: '⚪',
          title: 'Unknown Risk',
          description: 'Risk level could not be determined'
        };
    }
  };

  const riskInfo = getRiskLevelInfo(riskLevel);

  const getHighPriorityMetrics = () => {
    return riskMetrics.filter(metric => 
      metric.risk_level === 'HIGH' || metric.risk_level === 'VERY_HIGH'
    ).slice(0, 3); // Show top 3 high-risk metrics
  };

  const getTopWarnings = () => {
    return warnings.slice(0, 3); // Show top 3 warnings
  };

  const getTopMitigations = () => {
    return mitigations.slice(0, 3); // Show top 3 mitigations
  };

  if (compact) {
    return (
      <div 
        className="risk-warning-compact"
        style={{
          backgroundColor: riskInfo.backgroundColor,
          borderColor: riskInfo.borderColor,
          color: riskInfo.color
        }}
        onClick={() => setExpanded(!expanded)}
        title={riskInfo.description}
      >
        <span className="risk-icon">{riskInfo.icon}</span>
        <span className="risk-text">{riskInfo.title}</span>
        {riskScore && (
          <span className="risk-score">({riskScore})</span>
        )}
        {(warnings.length > 0 || riskMetrics.length > 0) && (
          <span className="expand-indicator">
            {expanded ? '▼' : '▶'}
          </span>
        )}
        
        {expanded && (
          <div className="risk-details-popup">
            {getTopWarnings().map((warning, index) => (
              <div key={index} className="warning-item">
                ⚠️ {warning}
              </div>
            ))}
            {getHighPriorityMetrics().map((metric, index) => (
              <div key={index} className="metric-item">
                <strong>{metric.name}:</strong> {metric.description}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div 
      className="risk-warning-full"
      style={{
        backgroundColor: riskInfo.backgroundColor,
        borderColor: riskInfo.borderColor
      }}
    >
      <div className="risk-header">
        <div className="risk-title">
          <span className="risk-icon">{riskInfo.icon}</span>
          <span className="risk-text">{riskInfo.title}</span>
          {symbol && <span className="risk-symbol">({symbol})</span>}
        </div>
        {riskScore && (
          <div className="risk-score-badge">
            Risk Score: {riskScore}/100
          </div>
        )}
      </div>

      <div className="risk-description" style={{ color: riskInfo.color }}>
        {riskInfo.description}
      </div>

      {warnings.length > 0 && (
        <div className="risk-warnings-section">
          <h4>⚠️ Risk Warnings</h4>
          <ul>
            {getTopWarnings().map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
            {warnings.length > 3 && (
              <li className="more-items">
                +{warnings.length - 3} more warnings
                <button 
                  className="expand-button"
                  onClick={() => setExpanded(!expanded)}
                >
                  {expanded ? 'Show Less' : 'Show All'}
                </button>
              </li>
            )}
          </ul>
          
          {expanded && warnings.length > 3 && (
            <ul className="additional-warnings">
              {warnings.slice(3).map((warning, index) => (
                <li key={index + 3}>{warning}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {riskMetrics.length > 0 && (
        <div className="risk-metrics-section">
          <h4>📊 Key Risk Factors</h4>
          <div className="metrics-grid">
            {getHighPriorityMetrics().map((metric, index) => (
              <div 
                key={index} 
                className={`metric-card risk-${metric.risk_level.toLowerCase()}`}
              >
                <div className="metric-name">{metric.name}</div>
                <div className="metric-level">
                  {riskAssessmentService.getRiskLevelIcon(metric.risk_level)} 
                  {metric.risk_level}
                </div>
                <div className="metric-description">{metric.description}</div>
              </div>
            ))}
          </div>
          
          {riskMetrics.length > 3 && (
            <button 
              className="show-all-metrics"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? 'Show Less' : `Show All ${riskMetrics.length} Risk Factors`}
            </button>
          )}
          
          {expanded && riskMetrics.length > 3 && (
            <div className="additional-metrics">
              {riskMetrics.slice(3).map((metric, index) => (
                <div 
                  key={index + 3} 
                  className={`metric-card risk-${metric.risk_level.toLowerCase()}`}
                >
                  <div className="metric-name">{metric.name}</div>
                  <div className="metric-level">
                    {riskAssessmentService.getRiskLevelIcon(metric.risk_level)} 
                    {metric.risk_level}
                  </div>
                  <div className="metric-description">{metric.description}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {mitigations.length > 0 && (
        <div className="risk-mitigations-section">
          <h4>💡 Risk Mitigation</h4>
          <ul>
            {getTopMitigations().map((mitigation, index) => (
              <li key={index}>{mitigation}</li>
            ))}
            {mitigations.length > 3 && (
              <li className="more-items">
                +{mitigations.length - 3} more suggestions
                <button 
                  className="expand-button"
                  onClick={() => setExpanded(!expanded)}
                >
                  {expanded ? 'Show Less' : 'Show All'}
                </button>
              </li>
            )}
          </ul>
          
          {expanded && mitigations.length > 3 && (
            <ul className="additional-mitigations">
              {mitigations.slice(3).map((mitigation, index) => (
                <li key={index + 3}>{mitigation}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {(riskLevel === 'HIGH' || riskLevel === 'VERY_HIGH') && (
        <DisclaimerBanner
          context="analysis_result"
          riskLevel={riskLevel}
          symbol={symbol}
          compact={true}
        />
      )}
    </div>
  );
};

export default RiskWarning;