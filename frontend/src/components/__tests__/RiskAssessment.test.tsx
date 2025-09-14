/**
 * Tests for RiskAssessment Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RiskAssessment from '../RiskAssessment';
import { riskAssessmentService } from '../../services/riskAssessment';

// Mock the risk assessment service
jest.mock('../../services/riskAssessment');
const mockedRiskService = riskAssessmentService as jest.Mocked<typeof riskAssessmentService>;

describe('RiskAssessment Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockStockAssessment = {
    symbol: 'AAPL',
    overall_risk_level: 'MODERATE' as const,
    risk_score: 65,
    risk_metrics: [
      {
        name: 'Volatility Risk',
        value: 0.25,
        risk_level: 'MODERATE' as const,
        description: 'Moderate volatility risk',
        impact: 'Medium' as const,
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
      market_data: '2024-01-15T15:25:00Z'
    }
  };

  const mockPortfolioAssessment = {
    total_value: 37000,
    overall_risk_level: 'MODERATE' as const,
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
        risk_level: 'MODERATE' as const,
        description: 'Portfolio concentration risk of 40.0%',
        impact: 'Medium' as const,
        mitigation: 'Reduce position sizes'
      }
    ],
    positions: [
      {
        symbol: 'AAPL',
        weight: 0.405,
        risk_assessment: mockStockAssessment
      }
    ],
    assessment_timestamp: '2024-01-15T15:30:00Z'
  };

  describe('Stock Risk Assessment Mode', () => {
    it('should render stock risk assessment interface', () => {
      render(<RiskAssessment />);

      expect(screen.getByText('Stock Risk')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/enter stock symbol/i)).toBeInTheDocument();
      expect(screen.getByText('Assess Risk')).toBeInTheDocument();
      expect(screen.getByText('Include Correlation Analysis')).toBeInTheDocument();
      expect(screen.getByText('Include Scenario Analysis')).toBeInTheDocument();
    });

    it('should perform stock risk assessment', async () => {
      const user = userEvent.setup();
      mockedRiskService.assessStockRisk.mockResolvedValue(mockStockAssessment);
      mockedRiskService.getRiskLevelIcon.mockReturnValue('🟡');

      render(<RiskAssessment />);

      // Enter symbol and click assess
      const symbolInput = screen.getByPlaceholderText(/enter stock symbol/i);
      const assessButton = screen.getByText('Assess Risk');

      await user.type(symbolInput, 'AAPL');
      await user.click(assessButton);

      await waitFor(() => {
        expect(mockedRiskService.assessStockRisk).toHaveBeenCalledWith('AAPL', true, true);
      });

      // Check if assessment results are displayed
      await waitFor(() => {
        expect(screen.getByText('Risk Assessment: AAPL')).toBeInTheDocument();
        expect(screen.getByText('MODERATE RISK')).toBeInTheDocument();
        expect(screen.getByText('65')).toBeInTheDocument(); // Risk score
      });
    });

    it('should handle assessment errors', async () => {
      const user = userEvent.setup();
      mockedRiskService.assessStockRisk.mockRejectedValue(new Error('Stock not found'));

      render(<RiskAssessment />);

      const symbolInput = screen.getByPlaceholderText(/enter stock symbol/i);
      const assessButton = screen.getByText('Assess Risk');

      await user.type(symbolInput, 'INVALID');
      await user.click(assessButton);

      await waitFor(() => {
        expect(screen.getByText(/stock not found/i)).toBeInTheDocument();
      });
    });

    it('should validate empty symbol input', async () => {
      const user = userEvent.setup();
      render(<RiskAssessment />);

      const assessButton = screen.getByText('Assess Risk');
      await user.click(assessButton);

      await waitFor(() => {
        expect(screen.getByText(/please enter a stock symbol/i)).toBeInTheDocument();
      });
    });

    it('should toggle correlation and scenario options', async () => {
      const user = userEvent.setup();
      render(<RiskAssessment />);

      const correlationCheckbox = screen.getByLabelText(/include correlation analysis/i);
      const scenarioCheckbox = screen.getByLabelText(/include scenario analysis/i);

      expect(correlationCheckbox).toBeChecked();
      expect(scenarioCheckbox).toBeChecked();

      await user.click(correlationCheckbox);
      await user.click(scenarioCheckbox);

      expect(correlationCheckbox).not.toBeChecked();
      expect(scenarioCheckbox).not.toBeChecked();
    });

    it('should display risk warnings and mitigation suggestions', async () => {
      const user = userEvent.setup();
      mockedRiskService.assessStockRisk.mockResolvedValue(mockStockAssessment);
      mockedRiskService.getRiskLevelIcon.mockReturnValue('🟡');

      render(<RiskAssessment />);

      const symbolInput = screen.getByPlaceholderText(/enter stock symbol/i);
      const assessButton = screen.getByText('Assess Risk');

      await user.type(symbolInput, 'AAPL');
      await user.click(assessButton);

      await waitFor(() => {
        expect(screen.getByText(/risk warnings/i)).toBeInTheDocument();
        expect(screen.getByText(/moderate risk/i)).toBeInTheDocument();
        expect(screen.getByText(/risk mitigation suggestions/i)).toBeInTheDocument();
        expect(screen.getByText(/consider diversification/i)).toBeInTheDocument();
      });
    });
  });

  describe('Portfolio Risk Assessment Mode', () => {
    it('should render portfolio risk assessment interface', async () => {
      const user = userEvent.setup();
      render(<RiskAssessment />);

      await user.click(screen.getByText('Portfolio Risk'));

      expect(screen.getByText('Portfolio Positions')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Symbol')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Quantity')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Value ($)')).toBeInTheDocument();
      expect(screen.getByText('Add')).toBeInTheDocument();
    });

    it('should add portfolio positions', async () => {
      const user = userEvent.setup();
      render(<RiskAssessment />);

      await user.click(screen.getByText('Portfolio Risk'));

      // Add a position
      await user.type(screen.getByPlaceholderText('Symbol'), 'AAPL');
      await user.type(screen.getByPlaceholderText('Quantity'), '100');
      await user.type(screen.getByPlaceholderText('Value ($)'), '15000');
      await user.type(screen.getByPlaceholderText('Sector (optional)'), 'Technology');

      await user.click(screen.getByText('Add'));

      // Check if position was added
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('100 shares')).toBeInTheDocument();
      expect(screen.getByText('$15,000')).toBeInTheDocument();
      expect(screen.getByText('Technology')).toBeInTheDocument();
    });

    it('should remove portfolio positions', async () => {
      const user = userEvent.setup();
      render(<RiskAssessment />);

      await user.click(screen.getByText('Portfolio Risk'));

      // Add a position
      await user.type(screen.getByPlaceholderText('Symbol'), 'AAPL');
      await user.type(screen.getByPlaceholderText('Quantity'), '100');
      await user.type(screen.getByPlaceholderText('Value ($)'), '15000');
      await user.click(screen.getByText('Add'));

      // Remove the position
      await user.click(screen.getByText('Remove'));

      expect(screen.queryByText('AAPL')).not.toBeInTheDocument();
    });

    it('should perform portfolio risk assessment', async () => {
      const user = userEvent.setup();
      mockedRiskService.assessPortfolioRisk.mockResolvedValue(mockPortfolioAssessment);
      mockedRiskService.getRiskLevelIcon.mockReturnValue('🟡');
      mockedRiskService.formatPercentage.mockImplementation((val) => `${(val * 100).toFixed(1)}%`);

      render(<RiskAssessment />);

      await user.click(screen.getByText('Portfolio Risk'));

      // Add positions
      await user.type(screen.getByPlaceholderText('Symbol'), 'AAPL');
      await user.type(screen.getByPlaceholderText('Quantity'), '100');
      await user.type(screen.getByPlaceholderText('Value ($)'), '15000');
      await user.click(screen.getByText('Add'));

      // Assess portfolio
      await user.click(screen.getByText('Assess Portfolio Risk'));

      await waitFor(() => {
        expect(mockedRiskService.assessPortfolioRisk).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(screen.getByText('Portfolio Risk Assessment')).toBeInTheDocument();
        expect(screen.getByText('$37,000')).toBeInTheDocument();
        expect(screen.getByText('65/100')).toBeInTheDocument(); // Diversification score
      });
    });

    it('should validate portfolio position inputs', async () => {
      const user = userEvent.setup();
      render(<RiskAssessment />);

      await user.click(screen.getByText('Portfolio Risk'));

      // Try to add position without required fields
      await user.click(screen.getByText('Add'));

      await waitFor(() => {
        expect(screen.getByText(/please fill in all position fields/i)).toBeInTheDocument();
      });
    });

    it('should prevent duplicate symbols', async () => {
      const user = userEvent.setup();
      render(<RiskAssessment />);

      await user.click(screen.getByText('Portfolio Risk'));

      // Add first position
      await user.type(screen.getByPlaceholderText('Symbol'), 'AAPL');
      await user.type(screen.getByPlaceholderText('Quantity'), '100');
      await user.type(screen.getByPlaceholderText('Value ($)'), '15000');
      await user.click(screen.getByText('Add'));

      // Try to add duplicate symbol
      await user.type(screen.getByPlaceholderText('Symbol'), 'AAPL');
      await user.type(screen.getByPlaceholderText('Quantity'), '50');
      await user.type(screen.getByPlaceholderText('Value ($)'), '7500');
      await user.click(screen.getByText('Add'));

      await waitFor(() => {
        expect(screen.getByText(/symbol already exists/i)).toBeInTheDocument();
      });
    });
  });

  describe('Scenario Analysis Mode', () => {
    it('should render scenario analysis interface', async () => {
      const user = userEvent.setup();
      render(<RiskAssessment />);

      await user.click(screen.getByText('Scenario Analysis'));

      expect(screen.getByText('Scenario Analysis')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/add symbol for analysis/i)).toBeInTheDocument();
      expect(screen.getByText('Add Symbol')).toBeInTheDocument();
      expect(screen.getByText('Run Scenario Analysis')).toBeInTheDocument();
    });

    it('should add and remove symbols for scenario analysis', async () => {
      const user = userEvent.setup();
      render(<RiskAssessment />);

      await user.click(screen.getByText('Scenario Analysis'));

      // Add symbols
      const symbolInput = screen.getByPlaceholderText(/add symbol for analysis/i);
      await user.type(symbolInput, 'AAPL');
      await user.click(screen.getByText('Add Symbol'));

      await user.type(symbolInput, 'GOOGL');
      await user.click(screen.getByText('Add Symbol'));

      // Check symbols are displayed
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('GOOGL')).toBeInTheDocument();

      // Remove a symbol
      const removeButtons = screen.getAllByText('×');
      await user.click(removeButtons[0]);

      expect(screen.queryByText('AAPL')).not.toBeInTheDocument();
      expect(screen.getByText('GOOGL')).toBeInTheDocument();
    });

    it('should perform scenario analysis', async () => {
      const user = userEvent.setup();
      const mockScenarioResults = {
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
            correlation_data: null,
            overall_risk_level: 'MODERATE'
          }
        },
        analysis_timestamp: '2024-01-15T15:30:00Z',
        scenarios_analyzed: ['bull_market', 'bear_market']
      };

      mockedRiskService.performScenarioAnalysis.mockResolvedValue(mockScenarioResults);
      mockedRiskService.formatPercentage.mockImplementation((val) => `${(val * 100).toFixed(1)}%`);

      render(<RiskAssessment />);

      await user.click(screen.getByText('Scenario Analysis'));

      // Add symbol
      const symbolInput = screen.getByPlaceholderText(/add symbol for analysis/i);
      await user.type(symbolInput, 'AAPL');
      await user.click(screen.getByText('Add Symbol'));

      // Run analysis
      await user.click(screen.getByText('Run Scenario Analysis'));

      await waitFor(() => {
        expect(mockedRiskService.performScenarioAnalysis).toHaveBeenCalledWith(['AAPL'], undefined);
      });

      await waitFor(() => {
        expect(screen.getByText('Scenario Analysis Results')).toBeInTheDocument();
        expect(screen.getByText('AAPL')).toBeInTheDocument();
        expect(screen.getByText(/bull market/i)).toBeInTheDocument();
      });
    });
  });

  describe('Mode Switching', () => {
    it('should switch between different modes', async () => {
      const user = userEvent.setup();
      render(<RiskAssessment />);

      // Start in stock mode
      expect(screen.getByText('Stock Risk')).toHaveClass('active');

      // Switch to portfolio mode
      await user.click(screen.getByText('Portfolio Risk'));
      expect(screen.getByText('Portfolio Risk')).toHaveClass('active');
      expect(screen.getByText('Portfolio Positions')).toBeInTheDocument();

      // Switch to scenario mode
      await user.click(screen.getByText('Scenario Analysis'));
      expect(screen.getByText('Scenario Analysis')).toHaveClass('active');
      expect(screen.getByPlaceholderText(/add symbol for analysis/i)).toBeInTheDocument();

      // Switch back to stock mode
      await user.click(screen.getByText('Stock Risk'));
      expect(screen.getByText('Stock Risk')).toHaveClass('active');
      expect(screen.getByPlaceholderText(/enter stock symbol/i)).toBeInTheDocument();
    });
  });

  describe('Props Handling', () => {
    it('should initialize with provided symbol', () => {
      render(<RiskAssessment symbol="AAPL" />);

      const symbolInput = screen.getByPlaceholderText(/enter stock symbol/i) as HTMLInputElement;
      expect(symbolInput.value).toBe('AAPL');
    });

    it('should initialize with provided portfolio', () => {
      const portfolio = [
        { symbol: 'AAPL', quantity: 100, value: 15000, sector: 'Technology' }
      ];

      render(<RiskAssessment portfolio={portfolio} />);

      // Should not automatically show portfolio in stock mode
      expect(screen.queryByText('AAPL')).not.toBeInTheDocument();
    });

    it('should call onRiskAssessed callback', async () => {
      const user = userEvent.setup();
      const onRiskAssessed = jest.fn();
      mockedRiskService.assessStockRisk.mockResolvedValue(mockStockAssessment);

      render(<RiskAssessment onRiskAssessed={onRiskAssessed} />);

      const symbolInput = screen.getByPlaceholderText(/enter stock symbol/i);
      const assessButton = screen.getByText('Assess Risk');

      await user.type(symbolInput, 'AAPL');
      await user.click(assessButton);

      await waitFor(() => {
        expect(onRiskAssessed).toHaveBeenCalledWith(mockStockAssessment);
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading state during assessment', async () => {
      const user = userEvent.setup();
      // Create a promise that we can control
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      mockedRiskService.assessStockRisk.mockReturnValue(promise);

      render(<RiskAssessment />);

      const symbolInput = screen.getByPlaceholderText(/enter stock symbol/i);
      const assessButton = screen.getByText('Assess Risk');

      await user.type(symbolInput, 'AAPL');
      await user.click(assessButton);

      // Should show loading state
      expect(screen.getByText('Assessing...')).toBeInTheDocument();
      expect(screen.getByText('Assessing...')).toBeDisabled();

      // Resolve the promise
      resolvePromise!(mockStockAssessment);

      await waitFor(() => {
        expect(screen.getByText('Assess Risk')).toBeInTheDocument();
        expect(screen.getByText('Assess Risk')).not.toBeDisabled();
      });
    });
  });
});