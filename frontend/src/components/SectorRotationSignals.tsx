/**
 * Sector Rotation Signals Component
 * 
 * Displays sector rotation signals and momentum analysis
 */

import React, { useState } from 'react';
import { SectorRotationSignal, getMarketPhaseText } from '../services/sector';
import './SectorRotationSignals.css';

interface SectorRotationSignalsProps {
  rotationSignals: SectorRotationSignal[];
  marketPhase: string;
  className?: string;
}

const SectorRotationSignals: React.FC<SectorRotationSignalsProps> = ({
  rotationSignals,
  marketPhase,
  className = ''
}) => {
  const [selectedSignal, setSelectedSignal] = useState<SectorRotationSignal | null>(null);
  const [filterStrength, setFilterStrength] = useState<number>(0);

  const filteredSignals = rotationSignals.filter(signal => 
    signal.signal_strength >= filterStrength
  );

  const getSignalStrengthColor = (strength: number): string => {
    if (strength >= 80) return '#22c55e'; // green
    if (strength >= 60) return '#84cc16'; // lime
    if (strength >= 40) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 80) return '#22c55e';
    if (confidence >= 60) return '#84cc16';
    if (confidence >= 40) return '#f59e0b';
    return '#ef4444';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const renderSignalCard = (signal: SectorRotationSignal) => (
    <div 
      key={`${signal.from_sector}-${signal.to_sector}`}
      className="rotation-signal-card"
      onClick={() => setSelectedSignal(signal)}
    >
      <div className="signal-header">
        <div className="rotation-flow">
          <span className="from-sector">{signal.from_sector}</span>
          <div className="rotation-arrow">→</div>
          <span className="to-sector">{signal.to_sector}</span>
        </div>
        <div className="signal-metrics">
          <div className="metric">
            <span className="metric-label">Strength</span>
            <span 
              className="metric-value"
              style={{ color: getSignalStrengthColor(signal.signal_strength) }}
            >
              {signal.signal_strength}%
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Confidence</span>
            <span 
              className="metric-value"
              style={{ color: getConfidenceColor(signal.confidence) }}
            >
              {signal.confidence}%
            </span>
          </div>
        </div>
      </div>

      <div className="signal-details">
        <div className="detail-row">
          <span className="detail-label">Momentum Shift:</span>
          <span className="detail-value">{signal.momentum_shift.toFixed(2)}%</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Volume Confirmation:</span>
          <span className={`detail-value ${signal.volume_confirmation ? 'confirmed' : 'unconfirmed'}`}>
            {signal.volume_confirmation ? 'Yes' : 'No'}
          </span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Expected Duration:</span>
          <span className="detail-value">{signal.expected_duration}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Signal Date:</span>
          <span className="detail-value">{formatDate(signal.signal_date)}</span>
        </div>
      </div>

      <div className="signal-driver">
        <span className="driver-label">Economic Driver:</span>
        <span className="driver-text">{signal.economic_driver}</span>
      </div>

      <div className="signal-strength-bar">
        <div 
          className="strength-fill"
          style={{ 
            width: `${signal.signal_strength}%`,
            backgroundColor: getSignalStrengthColor(signal.signal_strength)
          }}
        />
      </div>
    </div>
  );

  const renderSignalDetails = () => {
    if (!selectedSignal) return null;

    return (
      <div className="signal-details-modal">
        <div className="modal-overlay" onClick={() => setSelectedSignal(null)} />
        <div className="modal-content">
          <div className="modal-header">
            <h3>Rotation Signal Details</h3>
            <button 
              className="close-button"
              onClick={() => setSelectedSignal(null)}
            >
              ×
            </button>
          </div>

          <div className="modal-body">
            <div className="rotation-overview">
              <div className="rotation-flow-large">
                <div className="sector-box from">
                  <span className="sector-label">From</span>
                  <span className="sector-name">{selectedSignal.from_sector}</span>
                </div>
                <div className="rotation-arrow-large">→</div>
                <div className="sector-box to">
                  <span className="sector-label">To</span>
                  <span className="sector-name">{selectedSignal.to_sector}</span>
                </div>
              </div>

              <div className="signal-metrics-large">
                <div className="metric-large">
                  <span className="metric-label">Signal Strength</span>
                  <div className="metric-bar">
                    <div 
                      className="metric-fill"
                      style={{ 
                        width: `${selectedSignal.signal_strength}%`,
                        backgroundColor: getSignalStrengthColor(selectedSignal.signal_strength)
                      }}
                    />
                    <span className="metric-text">{selectedSignal.signal_strength}%</span>
                  </div>
                </div>
                <div className="metric-large">
                  <span className="metric-label">Confidence</span>
                  <div className="metric-bar">
                    <div 
                      className="metric-fill"
                      style={{ 
                        width: `${selectedSignal.confidence}%`,
                        backgroundColor: getConfidenceColor(selectedSignal.confidence)
                      }}
                    />
                    <span className="metric-text">{selectedSignal.confidence}%</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="signal-analysis">
              <div className="analysis-section">
                <h4>Supporting Reasons</h4>
                <ul className="reasons-list">
                  {selectedSignal.reasons.map((reason, index) => (
                    <li key={index} className="reason-item">
                      <span className="reason-bullet">✓</span>
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="analysis-section">
                <h4>Risk Factors</h4>
                <ul className="risks-list">
                  {selectedSignal.risks.map((risk, index) => (
                    <li key={index} className="risk-item">
                      <span className="risk-bullet">⚠</span>
                      {risk}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="signal-context">
              <div className="context-item">
                <span className="context-label">Market Phase:</span>
                <span className="context-value">{getMarketPhaseText(selectedSignal.market_phase)}</span>
              </div>
              <div className="context-item">
                <span className="context-label">Economic Driver:</span>
                <span className="context-value">{selectedSignal.economic_driver}</span>
              </div>
              <div className="context-item">
                <span className="context-label">Expected Duration:</span>
                <span className="context-value">{selectedSignal.expected_duration}</span>
              </div>
              <div className="context-item">
                <span className="context-label">Volume Confirmation:</span>
                <span className={`context-value ${selectedSignal.volume_confirmation ? 'confirmed' : 'unconfirmed'}`}>
                  {selectedSignal.volume_confirmation ? 'Confirmed' : 'Not Confirmed'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`sector-rotation-signals ${className}`}>
      <div className="rotation-header">
        <div className="header-content">
          <h3>Sector Rotation Signals</h3>
          <div className="market-phase-indicator">
            <span className="phase-label">Current Market Phase:</span>
            <span className="phase-value">{getMarketPhaseText(marketPhase)}</span>
          </div>
        </div>
        <div className="header-controls">
          <div className="strength-filter">
            <label>Min Strength:</label>
            <input
              type="range"
              min="0"
              max="100"
              value={filterStrength}
              onChange={(e) => setFilterStrength(Number(e.target.value))}
            />
            <span>{filterStrength}%</span>
          </div>
        </div>
      </div>

      <div className="signals-content">
        {filteredSignals.length === 0 ? (
          <div className="no-signals">
            <div className="no-signals-icon">📊</div>
            <h4>No Rotation Signals</h4>
            <p>
              {rotationSignals.length === 0 
                ? "No sector rotation signals detected at this time."
                : `No signals above ${filterStrength}% strength threshold.`
              }
            </p>
            {filterStrength > 0 && (
              <button 
                className="reset-filter-button"
                onClick={() => setFilterStrength(0)}
              >
                Show All Signals
              </button>
            )}
          </div>
        ) : (
          <div className="signals-grid">
            {filteredSignals.map(renderSignalCard)}
          </div>
        )}
      </div>

      <div className="rotation-summary">
        <div className="summary-stats">
          <div className="stat">
            <span className="stat-value">{rotationSignals.length}</span>
            <span className="stat-label">Total Signals</span>
          </div>
          <div className="stat">
            <span className="stat-value">{filteredSignals.length}</span>
            <span className="stat-label">Above Threshold</span>
          </div>
          <div className="stat">
            <span className="stat-value">
              {filteredSignals.filter(s => s.signal_strength >= 70).length}
            </span>
            <span className="stat-label">Strong Signals</span>
          </div>
        </div>
      </div>

      {renderSignalDetails()}
    </div>
  );
};

export default SectorRotationSignals;