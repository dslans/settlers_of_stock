/**
 * Sector Performance Chart Component
 * 
 * Displays sector performance data in various chart formats
 */

import React, { useState, useMemo } from 'react';
import { SectorPerformance, formatPerformance, getPerformanceColor } from '../services/sector';
import './SectorPerformanceChart.css';

interface SectorPerformanceChartProps {
  sectorPerformances: SectorPerformance[];
  selectedTimeframe: '1m' | '3m' | '1y';
  className?: string;
}

type ChartType = 'bar' | 'heatmap' | 'table';

const SectorPerformanceChart: React.FC<SectorPerformanceChartProps> = ({
  sectorPerformances,
  selectedTimeframe,
  className = ''
}) => {
  const [chartType, setChartType] = useState<ChartType>('bar');
  const [sortBy, setSortBy] = useState<'performance' | 'momentum' | 'alphabetical'>('performance');

  const sortedData = useMemo(() => {
    const performanceKey = `performance_${selectedTimeframe}` as keyof SectorPerformance;
    
    return [...sectorPerformances].sort((a, b) => {
      switch (sortBy) {
        case 'performance':
          return (b[performanceKey] as number) - (a[performanceKey] as number);
        case 'momentum':
          return b.momentum_score - a.momentum_score;
        case 'alphabetical':
          return a.sector.localeCompare(b.sector);
        default:
          return 0;
      }
    });
  }, [sectorPerformances, selectedTimeframe, sortBy]);

  const maxPerformance = useMemo(() => {
    const performanceKey = `performance_${selectedTimeframe}` as keyof SectorPerformance;
    return Math.max(...sectorPerformances.map(s => Math.abs(s[performanceKey] as number)));
  }, [sectorPerformances, selectedTimeframe]);

  const getBarWidth = (performance: number): number => {
    return Math.abs(performance) / maxPerformance * 100;
  };

  const renderBarChart = () => (
    <div className="bar-chart">
      <div className="chart-header">
        <h3>Sector Performance - {selectedTimeframe.toUpperCase()}</h3>
        <div className="chart-controls">
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)}>
            <option value="performance">Sort by Performance</option>
            <option value="momentum">Sort by Momentum</option>
            <option value="alphabetical">Sort Alphabetically</option>
          </select>
        </div>
      </div>
      <div className="bars-container">
        {sortedData.map((sector) => {
          const performanceKey = `performance_${selectedTimeframe}` as keyof SectorPerformance;
          const performance = sector[performanceKey] as number;
          
          return (
            <div key={sector.sector} className="bar-item">
              <div className="bar-label">
                <span className="sector-name">{sector.sector}</span>
                <span 
                  className="performance-value"
                  style={{ color: getPerformanceColor(performance) }}
                >
                  {formatPerformance(performance)}
                </span>
              </div>
              <div className="bar-container">
                <div className="bar-background">
                  <div 
                    className="bar-fill"
                    style={{
                      width: `${getBarWidth(performance)}%`,
                      backgroundColor: getPerformanceColor(performance),
                      marginLeft: performance < 0 ? `${100 - getBarWidth(performance)}%` : '0'
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderHeatmap = () => (
    <div className="heatmap">
      <div className="chart-header">
        <h3>Sector Performance Heatmap</h3>
      </div>
      <div className="heatmap-grid">
        {sortedData.map((sector) => {
          const performance1m = sector.performance_1m;
          const performance3m = sector.performance_3m;
          const performance1y = sector.performance_1y;
          
          return (
            <div key={sector.sector} className="heatmap-row">
              <div className="heatmap-label">{sector.sector}</div>
              <div className="heatmap-cells">
                <div 
                  className="heatmap-cell"
                  style={{ backgroundColor: getPerformanceColor(performance1m) + '40' }}
                  title={`1M: ${formatPerformance(performance1m)}`}
                >
                  <span>{formatPerformance(performance1m)}</span>
                </div>
                <div 
                  className="heatmap-cell"
                  style={{ backgroundColor: getPerformanceColor(performance3m) + '40' }}
                  title={`3M: ${formatPerformance(performance3m)}`}
                >
                  <span>{formatPerformance(performance3m)}</span>
                </div>
                <div 
                  className="heatmap-cell"
                  style={{ backgroundColor: getPerformanceColor(performance1y) + '40' }}
                  title={`1Y: ${formatPerformance(performance1y)}`}
                >
                  <span>{formatPerformance(performance1y)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="heatmap-legend">
        <div className="legend-item">
          <span className="legend-label">1M</span>
        </div>
        <div className="legend-item">
          <span className="legend-label">3M</span>
        </div>
        <div className="legend-item">
          <span className="legend-label">1Y</span>
        </div>
      </div>
    </div>
  );

  const renderTable = () => (
    <div className="performance-table">
      <div className="chart-header">
        <h3>Sector Performance Table</h3>
      </div>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Sector</th>
              <th>1D</th>
              <th>1W</th>
              <th>1M</th>
              <th>3M</th>
              <th>1Y</th>
              <th>Momentum</th>
              <th>Trend</th>
              <th>P/E</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((sector) => (
              <tr key={sector.sector}>
                <td className="sector-name-cell">{sector.sector}</td>
                <td style={{ color: getPerformanceColor(sector.performance_1d) }}>
                  {formatPerformance(sector.performance_1d)}
                </td>
                <td style={{ color: getPerformanceColor(sector.performance_1w) }}>
                  {formatPerformance(sector.performance_1w)}
                </td>
                <td style={{ color: getPerformanceColor(sector.performance_1m) }}>
                  {formatPerformance(sector.performance_1m)}
                </td>
                <td style={{ color: getPerformanceColor(sector.performance_3m) }}>
                  {formatPerformance(sector.performance_3m)}
                </td>
                <td style={{ color: getPerformanceColor(sector.performance_1y) }}>
                  {formatPerformance(sector.performance_1y)}
                </td>
                <td>
                  <div className="momentum-bar">
                    <div 
                      className="momentum-fill"
                      style={{ 
                        width: `${sector.momentum_score}%`,
                        backgroundColor: sector.momentum_score > 60 ? '#22c55e' : 
                                       sector.momentum_score > 40 ? '#f59e0b' : '#ef4444'
                      }}
                    />
                    <span className="momentum-text">{sector.momentum_score}</span>
                  </div>
                </td>
                <td>
                  <span className={`trend-badge trend-${sector.trend_direction}`}>
                    {sector.trend_direction.replace('_', ' ')}
                  </span>
                </td>
                <td>{sector.pe_ratio ? sector.pe_ratio.toFixed(2) : 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div className={`sector-performance-chart ${className}`}>
      <div className="chart-type-selector">
        <button 
          className={chartType === 'bar' ? 'active' : ''}
          onClick={() => setChartType('bar')}
        >
          Bar Chart
        </button>
        <button 
          className={chartType === 'heatmap' ? 'active' : ''}
          onClick={() => setChartType('heatmap')}
        >
          Heatmap
        </button>
        <button 
          className={chartType === 'table' ? 'active' : ''}
          onClick={() => setChartType('table')}
        >
          Table
        </button>
      </div>

      <div className="chart-content">
        {chartType === 'bar' && renderBarChart()}
        {chartType === 'heatmap' && renderHeatmap()}
        {chartType === 'table' && renderTable()}
      </div>
    </div>
  );
};

export default SectorPerformanceChart;