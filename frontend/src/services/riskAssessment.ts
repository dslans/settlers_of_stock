/**
 * Risk Assessment Service
 * 
 * Provides functions for comprehensive risk assessment including individual stock risk,
 * portfolio risk, correlation analysis, and scenario modeling.
 */

import { api } from './api';

export interface RiskMetric {
  name: string;
  value: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH';
  description: string;
  impact: 'Low' | 'Medium' | 'High';
  mitigation: string;
}

export interface CorrelationData {
  symbol: string;
  benchmark: string;
  correlation: number;
  beta: number;
  r_squared: number;
  period_days: number;
  last_updated: string;
}

export interface ScenarioResult {
  scenario: string;
  expected_return: number;
  worst_case_return: number;
  best_case_return: number;
  probability: number;
  description: string;
}

export interface StockRiskAssessment {
  symbol: string;
  overall_risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH';
  risk_score: number;
  risk_metrics: RiskMetric[];
  correlation_data?: CorrelationData;
  scenario_analysis?: ScenarioResult[];
  risk_warnings: string[];
  mitigation_suggestions: string[];
  assessment_timestamp: string;
  data_sources: {
    market_data?: string;
    fundamental_data?: string;
    technical_data?: string;
  };
}

export interface PortfolioPosition {
  symbol: string;
  quantity: number;
  value: number;
  sector?: string;
}

export interface PortfolioRiskAssessment {
  total_value: number;
  overall_risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH';
  diversification_score: number;
  concentration_risk: number;
  correlation_risk: number;
  sector_concentration: Record<string, number>;
  risk_metrics: RiskMetric[];
  positions: Array<{
    symbol: string;
    weight: number;
    risk_assessment: StockRiskAssessment;
  }>;
  assessment_timestamp: string;
}

export interface CorrelationAnalysis {
  symbol: string;
  benchmark: string;
  correlation: number;
  beta: number;
  r_squared: number;
  period_days: number;
  last_updated: string;
  interpretation: string;
  risk_implications: string[];
}

export interface ScenarioAnalysisResult {
  results: Record<string, {
    scenario_analysis: ScenarioResult[];
    correlation_data?: CorrelationData;
    overall_risk_level: string;
    error?: string;
  }>;
  analysis_timestamp: string;
  scenarios_analyzed: string[];
}

export interface RiskFactorDefinitions {
  risk_levels: Record<string, {
    description: string;
    characteristics: string[];
    suitable_for: string;
  }>;
  risk_categories: Record<string, string>;
  market_conditions: Record<string, {
    description: string;
    typical_duration: string;
    risk_characteristics: string[];
  }>;
}

class RiskAssessmentService {
  /**
   * Assess risk for an individual stock
   */
  async assessStockRisk(
    symbol: string,
    includeCorrelation: boolean = true,
    includeScenarios: boolean = true
  ): Promise<StockRiskAssessment> {
    try {
      const response = await api.post('/risk/stock', {
        symbol: symbol.toUpperCase(),
        include_correlation: includeCorrelation,
        include_scenarios: includeScenarios
      });
      return response.data;
    } catch (error: any) {
      console.error('Error assessing stock risk:', error);
      throw new Error(error.response?.data?.detail?.message || 'Failed to assess stock risk');
    }
  }

  /**
   * Assess risk for a portfolio
   */
  async assessPortfolioRisk(
    positions: PortfolioPosition[],
    includeCorrelationMatrix: boolean = true
  ): Promise<PortfolioRiskAssessment> {
    try {
      const response = await api.post('/risk/portfolio', {
        positions,
        include_correlation_matrix: includeCorrelationMatrix
      });
      return response.data;
    } catch (error: any) {
      console.error('Error assessing portfolio risk:', error);
      throw new Error(error.response?.data?.detail?.message || 'Failed to assess portfolio risk');
    }
  }

  /**
   * Perform scenario analysis for multiple stocks
   */
  async performScenarioAnalysis(
    symbols: string[],
    scenarios?: string[]
  ): Promise<ScenarioAnalysisResult> {
    try {
      const response = await api.post('/risk/scenario-analysis', {
        symbols: symbols.map(s => s.toUpperCase()),
        scenarios
      });
      return response.data;
    } catch (error: any) {
      console.error('Error performing scenario analysis:', error);
      throw new Error(error.response?.data?.detail?.message || 'Failed to perform scenario analysis');
    }
  }

  /**
   * Get correlation analysis for a stock
   */
  async getCorrelationAnalysis(
    symbol: string,
    benchmark: string = 'SPY',
    periodDays: number = 252
  ): Promise<CorrelationAnalysis> {
    try {
      const response = await api.get(`/risk/correlation/${symbol.toUpperCase()}`, {
        params: {
          benchmark: benchmark.toUpperCase(),
          period_days: periodDays
        }
      });
      return response.data;
    } catch (error: any) {
      console.error('Error getting correlation analysis:', error);
      throw new Error(error.response?.data?.detail?.message || 'Failed to get correlation analysis');
    }
  }

  /**
   * Get risk factor definitions and explanations
   */
  async getRiskFactorDefinitions(): Promise<RiskFactorDefinitions> {
    try {
      const response = await api.get('/risk/risk-factors');
      return response.data;
    } catch (error: any) {
      console.error('Error getting risk factor definitions:', error);
      throw new Error('Failed to get risk factor definitions');
    }
  }

  /**
   * Get risk level color for UI display
   */
  getRiskLevelColor(riskLevel: string): string {
    switch (riskLevel) {
      case 'LOW':
        return '#4CAF50'; // Green
      case 'MODERATE':
        return '#FF9800'; // Orange
      case 'HIGH':
        return '#F44336'; // Red
      case 'VERY_HIGH':
        return '#9C27B0'; // Purple
      default:
        return '#757575'; // Gray
    }
  }

  /**
   * Get risk level icon for UI display
   */
  getRiskLevelIcon(riskLevel: string): string {
    switch (riskLevel) {
      case 'LOW':
        return '🟢';
      case 'MODERATE':
        return '🟡';
      case 'HIGH':
        return '🔴';
      case 'VERY_HIGH':
        return '🟣';
      default:
        return '⚪';
    }
  }

  /**
   * Format risk score for display
   */
  formatRiskScore(score: number): string {
    if (score >= 80) return 'Very High Risk';
    if (score >= 60) return 'High Risk';
    if (score >= 40) return 'Moderate Risk';
    if (score >= 20) return 'Low Risk';
    return 'Very Low Risk';
  }

  /**
   * Format percentage for display
   */
  formatPercentage(value: number, decimals: number = 1): string {
    return `${(value * 100).toFixed(decimals)}%`;
  }

  /**
   * Format correlation value for display
   */
  formatCorrelation(correlation: number): string {
    const abs = Math.abs(correlation);
    let strength = '';
    
    if (abs >= 0.8) strength = 'Very Strong';
    else if (abs >= 0.6) strength = 'Strong';
    else if (abs >= 0.4) strength = 'Moderate';
    else if (abs >= 0.2) strength = 'Weak';
    else strength = 'Very Weak';
    
    const direction = correlation >= 0 ? 'Positive' : 'Negative';
    return `${strength} ${direction} (${correlation.toFixed(2)})`;
  }

  /**
   * Get diversification score description
   */
  getDiversificationDescription(score: number): string {
    if (score >= 80) return 'Excellent diversification';
    if (score >= 60) return 'Good diversification';
    if (score >= 40) return 'Moderate diversification';
    if (score >= 20) return 'Poor diversification';
    return 'Very poor diversification';
  }

  /**
   * Calculate portfolio value at risk (VaR) estimate
   */
  calculateVaR(
    portfolioValue: number,
    riskScore: number,
    confidenceLevel: number = 0.95
  ): number {
    // Simplified VaR calculation based on risk score
    // In practice, this would use more sophisticated models
    const volatility = riskScore / 100 * 0.4; // Convert risk score to volatility estimate
    const zScore = confidenceLevel === 0.95 ? 1.645 : 2.326; // 95% or 99% confidence
    
    return portfolioValue * volatility * zScore;
  }

  /**
   * Get risk mitigation priority
   */
  getMitigationPriority(riskMetric: RiskMetric): 'High' | 'Medium' | 'Low' {
    if (riskMetric.risk_level === 'VERY_HIGH') return 'High';
    if (riskMetric.risk_level === 'HIGH') return 'High';
    if (riskMetric.risk_level === 'MODERATE' && riskMetric.impact === 'High') return 'Medium';
    return 'Low';
  }
}

export const riskAssessmentService = new RiskAssessmentService();