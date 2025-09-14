/**
 * Risk Assessment Component
 * 
 * Comprehensive risk assessment interface with individual stock analysis,
 * portfolio risk assessment, and scenario modeling.
 */

import React, { useState, useEffect } from 'react';
import {
  riskAssessmentService,
  StockRiskAssessment,
  PortfolioRiskAssessment,
  PortfolioPosition,
  ScenarioAnalysisResult,
  RiskMetric
} from '../services/riskAssessment';
import './RiskAssessment.css';

interface RiskAssessmentProps {
  symbol?: string;
  portfolio?: PortfolioPosition[];
  onRiskAssessed?: (assessment: StockRiskAssessment | PortfolioRiskAssessment) => void;
}

type AssessmentMode = 'stock' | 'portfolio' | 'scenario';

const RiskAssessment: React.FC<RiskAssessmentProps> = ({
  symbol: initialSymbol,
  portfolio: initialPortfolio,
  onRiskAssessed
}) => {
  const [mode, setMode] = useState<AssessmentMode>('stock');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Stock assessment state
  const [symbol, setSymbol] = useState(initialSymbol || '');
  const [stockAssessment, setStockAssessment] = useState<StockRiskAssessment | null>(null);
  const [includeCorrelation, setIncludeCorrelation] = useState(true);
  const [includeScenarios, setIncludeScenarios] = useState(true);
  
  // Portfolio assessment state
  const [portfolio, setPortfolio] = useState<PortfolioPosition[]>(initialPortfolio || []);
  const [portfolioAssessment, setPortfolioAssessment] = useState<PortfolioRiskAssessment | null>(null);
  const [newPosition, setNewPosition] = useState<PortfolioPosition>({
    symbol: '',
    quantity: 0,
    value: 0,
    sector: ''
  });
  
  // Scenario analysis state
  const [scenarioSymbols, setScenarioSymbols] = useState<string[]>([]);
  const [scenarioResults, setScenarioResults] = useState<ScenarioAnalysisResult | null>(null);
  const [newScenarioSymbol, setNewScenarioSymbol] = useState('');

  useEffect(() => {
    if (initialSymbol && mode === 'stock') {
      handleStockAssessment();
    }
  }, [initialSymbol]);

  useEffect(() => {
    if (initialPortfolio && initialPortfolio.length > 0 && mode === 'portfolio') {
      handlePortfolioAssessment();
    }
  }, [initialPortfolio]);

  const handleStockAssessment = async () => {
    if (!symbol.trim()) {
      setError('Please enter a stock symbol');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const assessment = await riskAssessmentService.assessStockRisk(
        symbol,
        includeCorrelation,
        includeScenarios
      );
      
      setStockAssessment(assessment);
      onRiskAssessed?.(assessment);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePortfolioAssessment = async () => {
    if (portfolio.length === 0) {
      setError('Please add at least one position to the portfolio');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const assessment = await riskAssessmentService.assessPortfolioRisk(portfolio, true);
      setPortfolioAssessment(assessment);
      onRiskAssessed?.(assessment);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleScenarioAnalysis = async () => {
    if (scenarioSymbols.length === 0) {
      setError('Please add at least one symbol for scenario analysis');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const results = await riskAssessmentService.performScenarioAnalysis(scenarioSymbols);
      setScenarioResults(results);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const addPortfolioPosition = () => {
    if (!newPosition.symbol || newPosition.quantity <= 0 || newPosition.value <= 0) {
      setError('Please fill in all position fields with valid values');
      return;
    }

    if (portfolio.some(p => p.symbol.toUpperCase() === newPosition.symbol.toUpperCase())) {
      setError('Symbol already exists in portfolio');
      return;
    }

    setPortfolio([...portfolio, { ...newPosition, symbol: newPosition.symbol.toUpperCase() }]);
    setNewPosition({ symbol: '', quantity: 0, value: 0, sector: '' });
    setError(null);
  };

  const removePortfolioPosition = (index: number) => {
    setPortfolio(portfolio.filter((_, i) => i !== index));
  };

  const addScenarioSymbol = () => {
    if (!newScenarioSymbol.trim()) return;
    
    const upperSymbol = newScenarioSymbol.toUpperCase();
    if (!scenarioSymbols.includes(upperSymbol)) {
      setScenarioSymbols([...scenarioSymbols, upperSymbol]);
      setNewScenarioSymbol('');
    }
  };

  const removeScenarioSymbol = (symbol: string) => {
    setScenarioSymbols(scenarioSymbols.filter(s => s !== symbol));
  };

  const renderRiskMetric = (metric: RiskMetric) => (
    <div key={metric.name} className={`risk-metric risk-${metric.risk_level.toLowerCase()}`}>
      <div className="risk-metric-header">
        <span className="risk-metric-name">{metric.name}</span>
        <span className="risk-level-badge">
          {riskAssessmentService.getRiskLevelIcon(metric.risk_level)} {metric.risk_level}
        </span>
      </div>
      <div className="risk-metric-description">{metric.description}</div>
      <div className="risk-metric-impact">Impact: {metric.impact}</div>
      <div className="risk-metric-mitigation">
        <strong>Mitigation:</strong> {metric.mitigation}
      </div>
    </div>
  );

  const renderStockAssessment = () => {
    if (!stockAssessment) return null;

    return (
      <div className="stock-assessment">
        <div className="assessment-header">
          <h3>Risk Assessment: {stockAssessment.symbol}</h3>
          <div className={`overall-risk risk-${stockAssessment.overall_risk_level.toLowerCase()}`}>
            {riskAssessmentService.getRiskLevelIcon(stockAssessment.overall_risk_level)}
            {stockAssessment.overall_risk_level} RISK
          </div>
        </div>

        <div className="risk-score">
          <div className="score-circle">
            <span className="score-value">{stockAssessment.risk_score}</span>
            <span className="score-label">Risk Score</span>
          </div>
          <div className="score-description">
            {riskAssessmentService.formatRiskScore(stockAssessment.risk_score)}
          </div>
        </div>

        {stockAssessment.risk_warnings.length > 0 && (
          <div className="risk-warnings">
            <h4>⚠️ Risk Warnings</h4>
            <ul>
              {stockAssessment.risk_warnings.map((warning, index) => (
                <li key={index} className="warning-item">{warning}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="risk-metrics">
          <h4>Risk Metrics</h4>
          {stockAssessment.risk_metrics.map(renderRiskMetric)}
        </div>

        {stockAssessment.correlation_data && (
          <div className="correlation-analysis">
            <h4>Correlation Analysis</h4>
            <div className="correlation-data">
              <div className="correlation-item">
                <span>Correlation with {stockAssessment.correlation_data.benchmark}:</span>
                <span>{riskAssessmentService.formatCorrelation(stockAssessment.correlation_data.correlation)}</span>
              </div>
              <div className="correlation-item">
                <span>Beta:</span>
                <span>{stockAssessment.correlation_data.beta.toFixed(2)}</span>
              </div>
              <div className="correlation-item">
                <span>R-Squared:</span>
                <span>{riskAssessmentService.formatPercentage(stockAssessment.correlation_data.r_squared)}</span>
              </div>
            </div>
          </div>
        )}

        {stockAssessment.scenario_analysis && stockAssessment.scenario_analysis.length > 0 && (
          <div className="scenario-analysis">
            <h4>Scenario Analysis</h4>
            <div className="scenarios">
              {stockAssessment.scenario_analysis.map((scenario, index) => (
                <div key={index} className="scenario-item">
                  <div className="scenario-header">
                    <span className="scenario-name">{scenario.scenario.replace('_', ' ')}</span>
                    <span className="scenario-probability">
                      {riskAssessmentService.formatPercentage(scenario.probability)}
                    </span>
                  </div>
                  <div className="scenario-returns">
                    <div className="return-item">
                      <span>Expected:</span>
                      <span className={scenario.expected_return >= 0 ? 'positive' : 'negative'}>
                        {riskAssessmentService.formatPercentage(scenario.expected_return)}
                      </span>
                    </div>
                    <div className="return-item">
                      <span>Best Case:</span>
                      <span className="positive">
                        {riskAssessmentService.formatPercentage(scenario.best_case_return)}
                      </span>
                    </div>
                    <div className="return-item">
                      <span>Worst Case:</span>
                      <span className="negative">
                        {riskAssessmentService.formatPercentage(scenario.worst_case_return)}
                      </span>
                    </div>
                  </div>
                  <div className="scenario-description">{scenario.description}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {stockAssessment.mitigation_suggestions.length > 0 && (
          <div className="mitigation-suggestions">
            <h4>💡 Risk Mitigation Suggestions</h4>
            <ul>
              {stockAssessment.mitigation_suggestions.map((suggestion, index) => (
                <li key={index} className="suggestion-item">{suggestion}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderPortfolioAssessment = () => {
    if (!portfolioAssessment) return null;

    return (
      <div className="portfolio-assessment">
        <div className="assessment-header">
          <h3>Portfolio Risk Assessment</h3>
          <div className={`overall-risk risk-${portfolioAssessment.overall_risk_level.toLowerCase()}`}>
            {riskAssessmentService.getRiskLevelIcon(portfolioAssessment.overall_risk_level)}
            {portfolioAssessment.overall_risk_level} RISK
          </div>
        </div>

        <div className="portfolio-summary">
          <div className="summary-item">
            <span>Total Value:</span>
            <span>${portfolioAssessment.total_value.toLocaleString()}</span>
          </div>
          <div className="summary-item">
            <span>Positions:</span>
            <span>{portfolioAssessment.positions.length}</span>
          </div>
          <div className="summary-item">
            <span>Diversification Score:</span>
            <span>{portfolioAssessment.diversification_score}/100</span>
          </div>
        </div>

        <div className="risk-breakdown">
          <div className="risk-item">
            <span>Concentration Risk:</span>
            <span className={portfolioAssessment.concentration_risk > 0.6 ? 'high-risk' : 'low-risk'}>
              {riskAssessmentService.formatPercentage(portfolioAssessment.concentration_risk)}
            </span>
          </div>
          <div className="risk-item">
            <span>Correlation Risk:</span>
            <span className={portfolioAssessment.correlation_risk > 0.7 ? 'high-risk' : 'low-risk'}>
              {riskAssessmentService.formatPercentage(portfolioAssessment.correlation_risk)}
            </span>
          </div>
        </div>

        <div className="sector-concentration">
          <h4>Sector Concentration</h4>
          <div className="sector-chart">
            {Object.entries(portfolioAssessment.sector_concentration).map(([sector, weight]) => (
              <div key={sector} className="sector-item">
                <span className="sector-name">{sector}</span>
                <div className="sector-bar">
                  <div 
                    className="sector-fill" 
                    style={{ width: `${weight * 100}%` }}
                  ></div>
                </div>
                <span className="sector-weight">
                  {riskAssessmentService.formatPercentage(weight)}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="portfolio-risk-metrics">
          <h4>Portfolio Risk Metrics</h4>
          {portfolioAssessment.risk_metrics.map(renderRiskMetric)}
        </div>

        <div className="position-risks">
          <h4>Individual Position Risks</h4>
          <div className="positions-table">
            {portfolioAssessment.positions.map((position, index) => (
              <div key={index} className="position-row">
                <div className="position-symbol">{position.symbol}</div>
                <div className="position-weight">
                  {riskAssessmentService.formatPercentage(position.weight)}
                </div>
                <div className={`position-risk risk-${position.risk_assessment.overall_risk_level.toLowerCase()}`}>
                  {riskAssessmentService.getRiskLevelIcon(position.risk_assessment.overall_risk_level)}
                  {position.risk_assessment.overall_risk_level}
                </div>
                <div className="position-score">
                  {position.risk_assessment.risk_score}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="risk-assessment-container">
      <div className="mode-selector">
        <button 
          className={mode === 'stock' ? 'active' : ''}
          onClick={() => setMode('stock')}
        >
          Stock Risk
        </button>
        <button 
          className={mode === 'portfolio' ? 'active' : ''}
          onClick={() => setMode('portfolio')}
        >
          Portfolio Risk
        </button>
        <button 
          className={mode === 'scenario' ? 'active' : ''}
          onClick={() => setMode('scenario')}
        >
          Scenario Analysis
        </button>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {mode === 'stock' && (
        <div className="stock-mode">
          <div className="input-section">
            <div className="input-group">
              <input
                type="text"
                placeholder="Enter stock symbol (e.g., AAPL)"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                onKeyPress={(e) => e.key === 'Enter' && handleStockAssessment()}
              />
              <button 
                onClick={handleStockAssessment}
                disabled={loading || !symbol.trim()}
                className="assess-button"
              >
                {loading ? 'Assessing...' : 'Assess Risk'}
              </button>
            </div>
            
            <div className="options">
              <label>
                <input
                  type="checkbox"
                  checked={includeCorrelation}
                  onChange={(e) => setIncludeCorrelation(e.target.checked)}
                />
                Include Correlation Analysis
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={includeScenarios}
                  onChange={(e) => setIncludeScenarios(e.target.checked)}
                />
                Include Scenario Analysis
              </label>
            </div>
          </div>

          {renderStockAssessment()}
        </div>
      )}

      {mode === 'portfolio' && (
        <div className="portfolio-mode">
          <div className="portfolio-builder">
            <h4>Portfolio Positions</h4>
            
            <div className="add-position">
              <input
                type="text"
                placeholder="Symbol"
                value={newPosition.symbol}
                onChange={(e) => setNewPosition({...newPosition, symbol: e.target.value.toUpperCase()})}
              />
              <input
                type="number"
                placeholder="Quantity"
                value={newPosition.quantity || ''}
                onChange={(e) => setNewPosition({...newPosition, quantity: parseFloat(e.target.value) || 0})}
              />
              <input
                type="number"
                placeholder="Value ($)"
                value={newPosition.value || ''}
                onChange={(e) => setNewPosition({...newPosition, value: parseFloat(e.target.value) || 0})}
              />
              <input
                type="text"
                placeholder="Sector (optional)"
                value={newPosition.sector}
                onChange={(e) => setNewPosition({...newPosition, sector: e.target.value})}
              />
              <button onClick={addPortfolioPosition}>Add</button>
            </div>

            <div className="positions-list">
              {portfolio.map((position, index) => (
                <div key={index} className="position-item">
                  <span>{position.symbol}</span>
                  <span>{position.quantity} shares</span>
                  <span>${position.value.toLocaleString()}</span>
                  <span>{position.sector || 'N/A'}</span>
                  <button onClick={() => removePortfolioPosition(index)}>Remove</button>
                </div>
              ))}
            </div>

            <button 
              onClick={handlePortfolioAssessment}
              disabled={loading || portfolio.length === 0}
              className="assess-button"
            >
              {loading ? 'Assessing...' : 'Assess Portfolio Risk'}
            </button>
          </div>

          {renderPortfolioAssessment()}
        </div>
      )}

      {mode === 'scenario' && (
        <div className="scenario-mode">
          <div className="scenario-builder">
            <h4>Scenario Analysis</h4>
            
            <div className="add-symbol">
              <input
                type="text"
                placeholder="Add symbol for analysis"
                value={newScenarioSymbol}
                onChange={(e) => setNewScenarioSymbol(e.target.value.toUpperCase())}
                onKeyPress={(e) => e.key === 'Enter' && addScenarioSymbol()}
              />
              <button onClick={addScenarioSymbol}>Add Symbol</button>
            </div>

            <div className="symbols-list">
              {scenarioSymbols.map((symbol, index) => (
                <div key={index} className="symbol-tag">
                  {symbol}
                  <button onClick={() => removeScenarioSymbol(symbol)}>×</button>
                </div>
              ))}
            </div>

            <button 
              onClick={handleScenarioAnalysis}
              disabled={loading || scenarioSymbols.length === 0}
              className="assess-button"
            >
              {loading ? 'Analyzing...' : 'Run Scenario Analysis'}
            </button>
          </div>

          {scenarioResults && (
            <div className="scenario-results">
              <h4>Scenario Analysis Results</h4>
              {Object.entries(scenarioResults.results).map(([symbol, result]) => (
                <div key={symbol} className="symbol-scenarios">
                  <h5>{symbol}</h5>
                  {result.error ? (
                    <div className="error">Error: {result.error}</div>
                  ) : (
                    <div className="scenarios">
                      {result.scenario_analysis.map((scenario, index) => (
                        <div key={index} className="scenario-item">
                          <div className="scenario-name">{scenario.scenario.replace('_', ' ')}</div>
                          <div className="scenario-returns">
                            <span>Expected: {riskAssessmentService.formatPercentage(scenario.expected_return)}</span>
                            <span>Best: {riskAssessmentService.formatPercentage(scenario.best_case_return)}</span>
                            <span>Worst: {riskAssessmentService.formatPercentage(scenario.worst_case_return)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RiskAssessment;