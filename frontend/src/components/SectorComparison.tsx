/**
 * Sector Comparison Component
 * 
 * Allows users to compare multiple sectors across different metrics
 */

import React, { useState, useMemo } from 'react';
import { 
  SectorPerformance, 
  compareSectors, 
  SectorComparisonResult,
  formatPerformance,
  getPerformanceColor,
  formatMarketCap
} from '../services/sector';
import LoadingSpinner from './LoadingSpinner';
import './SectorComparison.css';

interface SectorComparisonProps {
  sectorPerformances: SectorPerformance[];
  className?: string;
}

const SectorComparison: React.FC<SectorComparisonProps> = ({
  sectorPerformances,
  className = ''
}) => {
  const [selectedSectors, setSelectedSectors] = useState<string[]>([]);
  const [timeframe, setTimeframe] = useState<string>('3m');
  const [comparisonResult, setComparisonResult] = useState<SectorComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const availableSectors = useMemo(() => 
    sectorPerformances.map(sp => sp.sector).sort(),
    [sectorPerformances]
  );

  const handleSectorToggle = (sector: string) => {
    setSelectedSectors(prev => {
      if (prev.includes(sector)) {
        return prev.filter(s => s !== sector);
      } else if (prev.length < 6) { // Limit to 6 sectors for readability
        return [...prev, sector];
      }
      return prev;
    });
  };

  const handleCompare = async () => {
    if (selectedSectors.length < 2) {
      setError('Please select at least 2 sectors to compare');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const result = await compareSectors({
        sectors: selectedSectors,
        timeframe,
        metrics: ['performance', 'valuation', 'momentum']
      });
      
      setComparisonResult(result);
    } catch (err) {
      console.error('Failed to compare sectors:', err);
      setError('Failed to compare sectors. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getSectorData = (sectorName: string): SectorPerformance | undefined => {
    return sectorPerformances.find(sp => sp.sector === sectorName);
  };

  const renderSectorSelector = () => (
    <div className="sector-selector">
      <div className="selector-header">
        <h4>Select Sectors to Compare</h4>
        <div className="selector-info">
          <span>{selectedSectors.length}/6 selected</span>
          {selectedSectors.length > 0 && (
            <button 
              className="clear-selection"
              onClick={() => setSelectedSectors([])}
            >
              Clear All
            </button>
          )}
        </div>
      </div>
      
      <div className="sectors-grid">
        {availableSectors.map(sector => {
          const sectorData = getSectorData(sector);
          const isSelected = selectedSectors.includes(sector);
          const isDisabled = !isSelected && selectedSectors.length >= 6;
          
          return (
            <div
              key={sector}
              className={`sector-option ${isSelected ? 'selected' : ''} ${isDisabled ? 'disabled' : ''}`}
              onClick={() => !isDisabled && handleSectorToggle(sector)}
            >
              <div className="sector-option-header">
                <span className="sector-name">{sector}</span>
                <div className="selection-indicator">
                  {isSelected && <span className="checkmark">✓</span>}
                </div>
              </div>
              {sectorData && (
                <div className="sector-preview">
                  <div className="preview-metric">
                    <span className="metric-label">3M:</span>
                    <span 
                      className="metric-value"
                      style={{ color: getPerformanceColor(sectorData.performance_3m) }}
                    >
                      {formatPerformance(sectorData.performance_3m)}
                    </span>
                  </div>
                  <div className="preview-metric">
                    <span className="metric-label">Momentum:</span>
                    <span className="metric-value">{sectorData.momentum_score}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderComparisonControls = () => (
    <div className="comparison-controls">
      <div className="control-group">
        <label>Timeframe:</label>
        <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
          <option value="1m">1 Month</option>
          <option value="3m">3 Months</option>
          <option value="1y">1 Year</option>
        </select>
      </div>
      
      <button 
        className="compare-button"
        onClick={handleCompare}
        disabled={selectedSectors.length < 2 || loading}
      >
        {loading ? 'Comparing...' : 'Compare Sectors'}
      </button>
    </div>
  );

  const renderComparisonResults = () => {
    if (!comparisonResult) return null;

    return (
      <div className="comparison-results">
        <div className="results-header">
          <h4>Comparison Results - {timeframe.toUpperCase()}</h4>
          <div className="results-summary">
            <div className="winner-badges">
              <div className="badge performance-winner">
                <span className="badge-label">Best Performance</span>
                <span className="badge-value">{comparisonResult.winner}</span>
              </div>
              <div className="badge value-winner">
                <span className="badge-label">Best Value</span>
                <span className="badge-value">{comparisonResult.best_value}</span>
              </div>
              <div className="badge momentum-winner">
                <span className="badge-label">Strongest Momentum</span>
                <span className="badge-value">{comparisonResult.strongest_momentum}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="rankings-section">
          <div className="ranking-table">
            <h5>Performance Ranking</h5>
            <div className="ranking-list">
              {comparisonResult.performance_ranking.map((item, index) => (
                <div key={item.sector} className="ranking-item">
                  <span className="rank">#{item.rank}</span>
                  <span className="sector-name">{item.sector}</span>
                  <span 
                    className="performance-value"
                    style={{ color: getPerformanceColor(item.performance) }}
                  >
                    {formatPerformance(item.performance)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="ranking-table">
            <h5>Valuation Ranking</h5>
            <div className="ranking-list">
              {comparisonResult.valuation_ranking.map((item, index) => (
                <div key={item.sector} className="ranking-item">
                  <span className="rank">#{item.rank}</span>
                  <span className="sector-name">{item.sector}</span>
                  <span className="valuation-value">
                    P/E: {item.pe_ratio ? item.pe_ratio.toFixed(2) : 'N/A'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="ranking-table">
            <h5>Momentum Ranking</h5>
            <div className="ranking-list">
              {comparisonResult.momentum_ranking.map((item, index) => (
                <div key={item.sector} className="ranking-item">
                  <span className="rank">#{item.rank}</span>
                  <span className="sector-name">{item.sector}</span>
                  <span className="momentum-value">{item.momentum_score}/100</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="insights-section">
          <div className="insights-column">
            <h5>Key Insights</h5>
            <ul className="insights-list">
              {comparisonResult.key_insights.map((insight, index) => (
                <li key={index} className="insight-item">
                  <span className="insight-bullet">💡</span>
                  {insight}
                </li>
              ))}
            </ul>
          </div>

          <div className="recommendations-column">
            <h5>Recommendations</h5>
            <ul className="recommendations-list">
              {comparisonResult.recommendations.map((recommendation, index) => (
                <li key={index} className="recommendation-item">
                  <span className="recommendation-bullet">📈</span>
                  {recommendation}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="detailed-comparison">
          <h5>Detailed Metrics Comparison</h5>
          <div className="comparison-table-container">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Sector</th>
                  <th>1M</th>
                  <th>3M</th>
                  <th>1Y</th>
                  <th>Momentum</th>
                  <th>P/E Ratio</th>
                  <th>Market Cap</th>
                </tr>
              </thead>
              <tbody>
                {selectedSectors.map(sector => {
                  const sectorData = getSectorData(sector);
                  if (!sectorData) return null;
                  
                  return (
                    <tr key={sector}>
                      <td className="sector-name-cell">{sector}</td>
                      <td style={{ color: getPerformanceColor(sectorData.performance_1m) }}>
                        {formatPerformance(sectorData.performance_1m)}
                      </td>
                      <td style={{ color: getPerformanceColor(sectorData.performance_3m) }}>
                        {formatPerformance(sectorData.performance_3m)}
                      </td>
                      <td style={{ color: getPerformanceColor(sectorData.performance_1y) }}>
                        {formatPerformance(sectorData.performance_1y)}
                      </td>
                      <td>{sectorData.momentum_score}/100</td>
                      <td>{sectorData.pe_ratio ? sectorData.pe_ratio.toFixed(2) : 'N/A'}</td>
                      <td>{formatMarketCap(sectorData.market_cap)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`sector-comparison ${className}`}>
      <div className="comparison-header">
        <h3>Sector Comparison Tool</h3>
        <p>Select up to 6 sectors to compare their performance, valuation, and momentum metrics.</p>
      </div>

      {renderSectorSelector()}
      {renderComparisonControls()}

      {error && (
        <div className="comparison-error">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {loading && (
        <div className="comparison-loading">
          <LoadingSpinner />
          <p>Comparing selected sectors...</p>
        </div>
      )}

      {renderComparisonResults()}
    </div>
  );
};

export default SectorComparison;