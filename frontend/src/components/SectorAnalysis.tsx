/**
 * Sector Analysis Component
 * 
 * Main component for sector performance analysis, industry comparisons,
 * and sector rotation identification.
 */

import React, { useState, useEffect } from 'react';
import {
  analyzeSectors,
  SectorAnalysisResult,
  formatPerformance,
  getPerformanceColor,
  getTrendDirectionText,
  getMarketPhaseText,
  formatMarketCap
} from '../services/sector';
import SectorPerformanceChart from './SectorPerformanceChart';
import SectorRotationSignals from './SectorRotationSignals';
import SectorComparison from './SectorComparison';
import LoadingSpinner from './LoadingSpinner';
import './SectorAnalysis.css';

interface SectorAnalysisProps {
  className?: string;
}

const SectorAnalysis: React.FC<SectorAnalysisProps> = ({ className = '' }) => {
  const [analysisData, setAnalysisData] = useState<SectorAnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'rotation' | 'comparison'>('overview');
  const [selectedTimeframe, setSelectedTimeframe] = useState<'1m' | '3m' | '1y'>('3m');

  useEffect(() => {
    loadSectorAnalysis();
  }, []);

  const loadSectorAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await analyzeSectors();
      setAnalysisData(data);
    } catch (err) {
      console.error('Failed to load sector analysis:', err);
      setError('Failed to load sector analysis. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadSectorAnalysis();
  };

  const getTopPerformers = () => {
    if (!analysisData) return [];
    
    const timeframeKey = `top_performers_${selectedTimeframe}` as keyof SectorAnalysisResult;
    return analysisData[timeframeKey] as string[] || [];
  };

  const getBottomPerformers = () => {
    if (!analysisData) return [];
    
    const timeframeKey = `bottom_performers_${selectedTimeframe}` as keyof SectorAnalysisResult;
    return analysisData[timeframeKey] as string[] || [];
  };

  const getSectorPerformance = (sectorName: string, timeframe: string) => {
    if (!analysisData) return 0;
    
    const sector = analysisData.sector_performances.find(s => s.sector === sectorName);
    if (!sector) return 0;
    
    const performanceKey = `performance_${timeframe}` as keyof typeof sector;
    return sector[performanceKey] as number || 0;
  };

  if (loading) {
    return (
      <div className={`sector-analysis ${className}`}>
        <div className="sector-analysis-loading">
          <LoadingSpinner />
          <p>Analyzing sector performance...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`sector-analysis ${className}`}>
        <div className="sector-analysis-error">
          <h3>Error Loading Sector Analysis</h3>
          <p>{error}</p>
          <button onClick={handleRefresh} className="retry-button">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!analysisData) {
    return (
      <div className={`sector-analysis ${className}`}>
        <div className="sector-analysis-empty">
          <p>No sector analysis data available.</p>
          <button onClick={handleRefresh} className="retry-button">
            Load Analysis
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`sector-analysis ${className}`}>
      <div className="sector-analysis-header">
        <div className="header-content">
          <h2>Sector Analysis</h2>
          <div className="header-info">
            <span className="market-trend">
              Market Trend: <strong>{getTrendDirectionText(analysisData.market_trend)}</strong>
            </span>
            <span className="market-phase">
              Phase: <strong>{getMarketPhaseText(analysisData.market_phase)}</strong>
            </span>
            <span className="volatility">
              Volatility: <strong>{analysisData.volatility_regime}</strong>
            </span>
          </div>
        </div>
        <div className="header-actions">
          <button onClick={handleRefresh} className="refresh-button">
            Refresh
          </button>
        </div>
      </div>

      <div className="sector-analysis-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'performance' ? 'active' : ''}`}
          onClick={() => setActiveTab('performance')}
        >
          Performance
        </button>
        <button
          className={`tab ${activeTab === 'rotation' ? 'active' : ''}`}
          onClick={() => setActiveTab('rotation')}
        >
          Rotation Signals
        </button>
        <button
          className={`tab ${activeTab === 'comparison' ? 'active' : ''}`}
          onClick={() => setActiveTab('comparison')}
        >
          Comparison
        </button>
      </div>

      <div className="sector-analysis-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <div className="timeframe-selector">
              <label>Timeframe:</label>
              <select
                value={selectedTimeframe}
                onChange={(e) => setSelectedTimeframe(e.target.value as '1m' | '3m' | '1y')}
              >
                <option value="1m">1 Month</option>
                <option value="3m">3 Months</option>
                <option value="1y">1 Year</option>
              </select>
            </div>

            <div className="performance-summary">
              <div className="performance-section">
                <h3>Top Performers ({selectedTimeframe.toUpperCase()})</h3>
                <div className="sector-list">
                  {getTopPerformers().map((sector, index) => (
                    <div key={sector} className="sector-item top-performer">
                      <span className="rank">#{index + 1}</span>
                      <span className="sector-name">{sector}</span>
                      <span 
                        className="performance"
                        style={{ color: getPerformanceColor(getSectorPerformance(sector, selectedTimeframe)) }}
                      >
                        {formatPerformance(getSectorPerformance(sector, selectedTimeframe))}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="performance-section">
                <h3>Bottom Performers ({selectedTimeframe.toUpperCase()})</h3>
                <div className="sector-list">
                  {getBottomPerformers().map((sector, index) => (
                    <div key={sector} className="sector-item bottom-performer">
                      <span className="rank">#{index + 1}</span>
                      <span className="sector-name">{sector}</span>
                      <span 
                        className="performance"
                        style={{ color: getPerformanceColor(getSectorPerformance(sector, selectedTimeframe)) }}
                      >
                        {formatPerformance(getSectorPerformance(sector, selectedTimeframe))}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="sector-grid">
              {analysisData.sector_performances.map((sector) => (
                <div key={sector.sector} className="sector-card">
                  <div className="sector-card-header">
                    <h4>{sector.sector}</h4>
                    <span className="trend-indicator">
                      {getTrendDirectionText(sector.trend_direction)}
                    </span>
                  </div>
                  <div className="sector-card-metrics">
                    <div className="metric">
                      <label>1M Performance:</label>
                      <span style={{ color: getPerformanceColor(sector.performance_1m) }}>
                        {formatPerformance(sector.performance_1m)}
                      </span>
                    </div>
                    <div className="metric">
                      <label>3M Performance:</label>
                      <span style={{ color: getPerformanceColor(sector.performance_3m) }}>
                        {formatPerformance(sector.performance_3m)}
                      </span>
                    </div>
                    <div className="metric">
                      <label>Momentum Score:</label>
                      <span>{sector.momentum_score}/100</span>
                    </div>
                    <div className="metric">
                      <label>Market Cap:</label>
                      <span>{formatMarketCap(sector.market_cap)}</span>
                    </div>
                    {sector.pe_ratio && (
                      <div className="metric">
                        <label>P/E Ratio:</label>
                        <span>{sector.pe_ratio.toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'performance' && (
          <div className="performance-tab">
            <SectorPerformanceChart 
              sectorPerformances={analysisData.sector_performances}
              selectedTimeframe={selectedTimeframe}
            />
          </div>
        )}

        {activeTab === 'rotation' && (
          <div className="rotation-tab">
            <SectorRotationSignals 
              rotationSignals={analysisData.rotation_signals}
              marketPhase={analysisData.market_phase}
            />
          </div>
        )}

        {activeTab === 'comparison' && (
          <div className="comparison-tab">
            <SectorComparison 
              sectorPerformances={analysisData.sector_performances}
            />
          </div>
        )}
      </div>

      <div className="sector-analysis-footer">
        <div className="data-freshness">
          <span>Last updated: {new Date(analysisData.analysis_timestamp).toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
};

export default SectorAnalysis;