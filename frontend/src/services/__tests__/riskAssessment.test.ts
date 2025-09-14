/**
 * Tests for Risk Assessment Service
 */

import { riskAssessmentService, RiskMetric, StockRiskAssessment, PortfolioPosition } from '../riskAssessment';
import { api } from '../api';

// Mock the API
jest.mock('../api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('RiskAssessmentService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('assessStockRisk', () => {
    const mockStockAssessment: StockRiskAssessment = {
      symbol: 'AAPL',
      overall_risk_level: 'MODERATE',
      risk_score: 65,
      risk_metrics: [
        {
          name: 'Volatility Risk',
          value: 0.25,
          risk_level: 'MODERATE',
          description: 'Moderate volatility risk',
          impact: 'Medium',
          mitigation: 'Consider position sizing'
        }
      ],
      correlation_data: {
        symbol: 'AAPL',
        benchmark: 'SPY',
        correlation: 0.75,
        beta: 1.2,
        r_squared: 0.56,
        period_days: 252,
        last_updated: '2024-01-15T10:00:00Z'
      },
      scenario_analysis: [
        {
          scenario: 'bull_market',
          expected_return: 0.20,
          worst_case_return: -0.10,
          best_case_return: 0.50,
          probability: 0.35,
          description: 'Bull market scenario'
        }
      ],
      risk_warnings: ['⚠️ MODERATE RISK: This investment carries typical market risks'],
      mitigation_suggestions: ['Consider diversification across sectors'],
      assessment_timestamp: '2024-01-15T15:30:00Z',
      data_sources: {
        market_data: '2024-01-15T15:25:00Z',
        fundamental_data: '2024-01-15T10:00:00Z',
        technical_data: '2024-01-15T15:20:00Z'
      }
    };

    it('should assess stock risk successfully', async () => {
      mockedApi.post.mockResolvedValue({ data: mockStockAssessment });

      const result = await riskAssessmentService.assessStockRisk('AAPL', true, true);

      expect(mockedApi.post).toHaveBeenCalledWith('/risk/stock', {
        symbol: 'AAPL',
        include_correlation: true,
        include_scenarios: true
      });
      expect(result).toEqual(mockStockAssessment);
    });

    it('should convert symbol to uppercase', async () => {
      mockedApi.post.mockResolvedValue({ data: mockStockAssessment });

      await riskAssessmentService.assessStockRisk('aapl');

      expect(mockedApi.post).toHaveBeenCalledWith('/risk/stock', {
        symbol: 'AAPL',
        include_correlation: true,
        include_scenarios: true
      });
    });

    it('should handle API errors', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: {
              message: 'Stock not found'
            }
          }
        }
      };
      mockedApi.post.mockRejectedValue(errorResponse);

      await expect(riskAssessmentService.assessStockRisk('INVALID')).rejects.toThrow('Stock not found');
    });

    it('should handle generic errors', async () => {
      mockedApi.post.mockRejectedValue(new Error('Network error'));

      await expect(riskAssessmentService.assessStockRisk('AAPL')).rejects.toThrow('Failed to assess stock risk');
    });
  });

  describe('assessPortfolioRisk', () => {
    const mockPositions: PortfolioPosition[] = [
      { symbol: 'AAPL', quantity: 100, value: 15000, sector: 'Technology' },
      { symbol: 'GOOGL', quantity: 50, value: 12000, sector: 'Technology' },
      { symbol: 'JNJ', quantity: 75, value: 10000, sector: 'Healthcare' }
    ];

    const mockPortfolioAssessment = {
      total_value: 37000,
      overall_risk_level: 'MODERATE',
      diversification_score: 65,
      concentration_risk: 0.4,
      correlation_risk: 0.6,
      sector_concentration: {
        'Technology': 0.73,
        'Healthcare': 0.27
      },
      risk_metrics: [
        {
          name: 'Concentration Risk',
          value: 0.4,
          risk_level: 'MODERATE',
          description: 'Portfolio concentration risk of 40.0%',
          impact: 'Medium',
          mitigation: 'Reduce position sizes and increase number of holdings'
        }
      ],
      positions: [
        {
          symbol: 'AAPL',
          weight: 0.405,
          risk_assessment: {
            symbol: 'AAPL',
            overall_risk_level: 'MODERATE',
            risk_score: 65,
            risk_metrics: [],
            risk_warnings: [],
            mitigation_suggestions: [],
            assessment_timestamp: '2024-01-15T15:30:00Z',
            data_sources: {}
          }
        }
      ],
      assessment_timestamp: '2024-01-15T15:30:00Z'
    };

    it('should assess portfolio risk successfully', async () => {
      mockedApi.post.mockResolvedValue({ data: mockPortfolioAssessment });

      const result = await riskAssessmentService.assessPortfolioRisk(mockPositions, true);

      expect(mockedApi.post).toHaveBeenCalledWith('/risk/portfolio', {
        positions: mockPositions,
        include_correlation_matrix: true
      });
      expect(result).toEqual(mockPortfolioAssessment);
    });

    it('should handle portfolio assessment errors', async () => {
      mockedApi.post.mockRejectedValue(new Error('Portfolio error'));

      await expect(riskAssessmentService.assessPortfolioRisk(mockPositions)).rejects.toThrow('Failed to assess portfolio risk');
    });
  });

  describe('performScenarioAnalysis', () => {
    const mockScenarioResult = {
      results: {
        'AAPL': {
          scenario_analysis: [
            {
              scenario: 'bull_market',
              expected_return: 0.20,
              worst_case_return: -0.10,
              best_case_return: 0.50,
              probability: 0.35,
              description: 'Bull market scenario'
            }
          ],
          correlation_data: {
            symbol: 'AAPL',
            benchmark: 'SPY',
            correlation: 0.75,
            beta: 1.2,
            r_squared: 0.56,
            period_days: 252,
            last_updated: '2024-01-15T10:00:00Z'
          },
          overall_risk_level: 'MODERATE'
        }
      },
      analysis_timestamp: '2024-01-15T15:30:00Z',
      scenarios_analyzed: ['bull_market', 'bear_market', 'sideways_market']
    };

    it('should perform scenario analysis successfully', async () => {
      mockedApi.post.mockResolvedValue({ data: mockScenarioResult });

      const result = await riskAssessmentService.performScenarioAnalysis(['AAPL', 'GOOGL']);

      expect(mockedApi.post).toHaveBeenCalledWith('/risk/scenario-analysis', {
        symbols: ['AAPL', 'GOOGL'],
        scenarios: undefined
      });
      expect(result).toEqual(mockScenarioResult);
    });

    it('should convert symbols to uppercase', async () => {
      mockedApi.post.mockResolvedValue({ data: mockScenarioResult });

      await riskAssessmentService.performScenarioAnalysis(['aapl', 'googl']);

      expect(mockedApi.post).toHaveBeenCalledWith('/risk/scenario-analysis', {
        symbols: ['AAPL', 'GOOGL'],
        scenarios: undefined
      });
    });
  });

  describe('getCorrelationAnalysis', () => {
    const mockCorrelationAnalysis = {
      symbol: 'AAPL',
      benchmark: 'SPY',
      correlation: 0.75,
      beta: 1.2,
      r_squared: 0.56,
      period_days: 252,
      last_updated: '2024-01-15T10:00:00Z',
      interpretation: 'Stock shows high positive correlation with market and is more volatile than market (β=1.20)',
      risk_implications: [
        'High correlation means stock will likely move with market trends',
        'High beta indicates amplified market movements - higher risk and potential reward'
      ]
    };

    it('should get correlation analysis successfully', async () => {
      mockedApi.get.mockResolvedValue({ data: mockCorrelationAnalysis });

      const result = await riskAssessmentService.getCorrelationAnalysis('AAPL', 'SPY', 252);

      expect(mockedApi.get).toHaveBeenCalledWith('/risk/correlation/AAPL', {
        params: {
          benchmark: 'SPY',
          period_days: 252
        }
      });
      expect(result).toEqual(mockCorrelationAnalysis);
    });

    it('should use default parameters', async () => {
      mockedApi.get.mockResolvedValue({ data: mockCorrelationAnalysis });

      await riskAssessmentService.getCorrelationAnalysis('AAPL');

      expect(mockedApi.get).toHaveBeenCalledWith('/risk/correlation/AAPL', {
        params: {
          benchmark: 'SPY',
          period_days: 252
        }
      });
    });
  });

  describe('getRiskFactorDefinitions', () => {
    const mockDefinitions = {
      risk_levels: {
        'LOW': {
          description: 'Low risk with stable fundamentals and low volatility',
          characteristics: ['Low volatility', 'Strong fundamentals', 'High liquidity'],
          suitable_for: 'Conservative investors seeking capital preservation'
        }
      },
      risk_categories: {
        'MARKET_RISK': 'Risk from overall market movements and economic conditions'
      },
      market_conditions: {
        'bull_market': {
          description: 'Rising market with strong investor confidence',
          typical_duration: '1-3 years',
          risk_characteristics: ['Low downside risk', 'High opportunity cost']
        }
      }
    };

    it('should get risk factor definitions successfully', async () => {
      mockedApi.get.mockResolvedValue({ data: mockDefinitions });

      const result = await riskAssessmentService.getRiskFactorDefinitions();

      expect(mockedApi.get).toHaveBeenCalledWith('/risk/risk-factors');
      expect(result).toEqual(mockDefinitions);
    });
  });

  describe('utility methods', () => {
    describe('getRiskLevelColor', () => {
      it('should return correct colors for risk levels', () => {
        expect(riskAssessmentService.getRiskLevelColor('LOW')).toBe('#4CAF50');
        expect(riskAssessmentService.getRiskLevelColor('MODERATE')).toBe('#FF9800');
        expect(riskAssessmentService.getRiskLevelColor('HIGH')).toBe('#F44336');
        expect(riskAssessmentService.getRiskLevelColor('VERY_HIGH')).toBe('#9C27B0');
        expect(riskAssessmentService.getRiskLevelColor('UNKNOWN')).toBe('#757575');
      });
    });

    describe('getRiskLevelIcon', () => {
      it('should return correct icons for risk levels', () => {
        expect(riskAssessmentService.getRiskLevelIcon('LOW')).toBe('🟢');
        expect(riskAssessmentService.getRiskLevelIcon('MODERATE')).toBe('🟡');
        expect(riskAssessmentService.getRiskLevelIcon('HIGH')).toBe('🔴');
        expect(riskAssessmentService.getRiskLevelIcon('VERY_HIGH')).toBe('🟣');
        expect(riskAssessmentService.getRiskLevelIcon('UNKNOWN')).toBe('⚪');
      });
    });

    describe('formatRiskScore', () => {
      it('should format risk scores correctly', () => {
        expect(riskAssessmentService.formatRiskScore(90)).toBe('Very High Risk');
        expect(riskAssessmentService.formatRiskScore(70)).toBe('High Risk');
        expect(riskAssessmentService.formatRiskScore(50)).toBe('Moderate Risk');
        expect(riskAssessmentService.formatRiskScore(30)).toBe('Low Risk');
        expect(riskAssessmentService.formatRiskScore(10)).toBe('Very Low Risk');
      });
    });

    describe('formatPercentage', () => {
      it('should format percentages correctly', () => {
        expect(riskAssessmentService.formatPercentage(0.1234)).toBe('12.3%');
        expect(riskAssessmentService.formatPercentage(0.1234, 2)).toBe('12.34%');
        expect(riskAssessmentService.formatPercentage(-0.05)).toBe('-5.0%');
      });
    });

    describe('formatCorrelation', () => {
      it('should format correlation values correctly', () => {
        expect(riskAssessmentService.formatCorrelation(0.85)).toBe('Very Strong Positive (0.85)');
        expect(riskAssessmentService.formatCorrelation(0.65)).toBe('Strong Positive (0.65)');
        expect(riskAssessmentService.formatCorrelation(0.45)).toBe('Moderate Positive (0.45)');
        expect(riskAssessmentService.formatCorrelation(0.25)).toBe('Weak Positive (0.25)');
        expect(riskAssessmentService.formatCorrelation(0.05)).toBe('Very Weak Positive (0.05)');
        expect(riskAssessmentService.formatCorrelation(-0.65)).toBe('Strong Negative (-0.65)');
      });
    });

    describe('getDiversificationDescription', () => {
      it('should provide correct diversification descriptions', () => {
        expect(riskAssessmentService.getDiversificationDescription(85)).toBe('Excellent diversification');
        expect(riskAssessmentService.getDiversificationDescription(65)).toBe('Good diversification');
        expect(riskAssessmentService.getDiversificationDescription(45)).toBe('Moderate diversification');
        expect(riskAssessmentService.getDiversificationDescription(25)).toBe('Poor diversification');
        expect(riskAssessmentService.getDiversificationDescription(15)).toBe('Very poor diversification');
      });
    });

    describe('calculateVaR', () => {
      it('should calculate Value at Risk correctly', () => {
        const portfolioValue = 100000;
        const riskScore = 60; // Moderate risk
        const var95 = riskAssessmentService.calculateVaR(portfolioValue, riskScore, 0.95);
        const var99 = riskAssessmentService.calculateVaR(portfolioValue, riskScore, 0.99);

        expect(var95).toBeGreaterThan(0);
        expect(var99).toBeGreaterThan(var95); // 99% VaR should be higher than 95% VaR
        expect(var95).toBeLessThan(portfolioValue); // VaR should be less than total value
      });
    });

    describe('getMitigationPriority', () => {
      it('should determine correct mitigation priorities', () => {
        const highRiskMetric: RiskMetric = {
          name: 'Test',
          value: 0.8,
          risk_level: 'VERY_HIGH',
          description: 'Test',
          impact: 'High',
          mitigation: 'Test'
        };

        const moderateRiskMetric: RiskMetric = {
          name: 'Test',
          value: 0.5,
          risk_level: 'MODERATE',
          description: 'Test',
          impact: 'High',
          mitigation: 'Test'
        };

        const lowRiskMetric: RiskMetric = {
          name: 'Test',
          value: 0.2,
          risk_level: 'LOW',
          description: 'Test',
          impact: 'Low',
          mitigation: 'Test'
        };

        expect(riskAssessmentService.getMitigationPriority(highRiskMetric)).toBe('High');
        expect(riskAssessmentService.getMitigationPriority(moderateRiskMetric)).toBe('Medium');
        expect(riskAssessmentService.getMitigationPriority(lowRiskMetric)).toBe('Low');
      });
    });
  });
});