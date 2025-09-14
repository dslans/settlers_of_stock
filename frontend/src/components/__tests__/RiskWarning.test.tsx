/**
 * Tests for RiskWarning Component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RiskWarning from '../RiskWarning';
import { RiskMetric } from '../../services/riskAssessment';

describe('RiskWarning Component', () => {
  const mockRiskMetrics: RiskMetric[] = [
    {
      name: 'Volatility Risk',
      value: 0.35,
      risk_level: 'HIGH',
      description: 'High volatility risk detected',
      impact: 'High',
      mitigation: 'Consider position sizing and stop-losses'
    },
    {
      name: 'Liquidity Risk',
      value: 50000,
      risk_level: 'MODERATE',
      description: 'Moderate liquidity risk',
      impact: 'Medium',
      mitigation: 'Use limit orders for better execution'
    },
    {
      name: 'Debt Risk',
      value: 0.8,
      risk_level: 'LOW',
      description: 'Low debt levels',
      impact: 'Low',
      mitigation: 'Continue monitoring debt levels'
    }
  ];

  const mockWarnings = [
    '⚠️ HIGH RISK: This investment carries significant risk',
    '⚠️ Volatility Risk: High volatility risk detected',
    '⚠️ Market conditions are uncertain'
  ];

  const mockMitigations = [
    'Consider reducing position size to limit exposure',
    'Use stop-loss orders to limit downside risk',
    'Diversify across multiple positions and sectors'
  ];

  describe('Compact Mode', () => {
    it('should render compact risk warning', () => {
      render(
        <RiskWarning
          riskLevel="HIGH"
          riskScore={75}
          compact={true}
        />
      );

      expect(screen.getByText('🔴')).toBeInTheDocument();
      expect(screen.getByText('High Risk')).toBeInTheDocument();
      expect(screen.getByText('(75)')).toBeInTheDocument();
    });

    it('should show expand indicator when warnings or metrics exist', () => {
      render(
        <RiskWarning
          riskLevel="HIGH"
          warnings={mockWarnings}
          compact={true}
        />
      );

      expect(screen.getByText('▶')).toBeInTheDocument();
    });

    it('should expand to show details on click', async () => {
      const user = userEvent.setup();
      render(
        <RiskWarning
          riskLevel="HIGH"
          warnings={mockWarnings.slice(0, 2)}
          riskMetrics={mockRiskMetrics.slice(0, 1)}
          compact={true}
        />
      );

      const compactWarning = screen.getByText('High Risk').closest('.risk-warning-compact');
      expect(compactWarning).toBeInTheDocument();

      await user.click(compactWarning!);

      expect(screen.getByText('▼')).toBeInTheDocument();
      expect(screen.getByText(/high risk.*significant risk/i)).toBeInTheDocument();
      expect(screen.getByText(/volatility risk.*high volatility/i)).toBeInTheDocument();
    });

    it('should display correct risk level colors and icons', () => {
      const { rerender } = render(
        <RiskWarning riskLevel="LOW" compact={true} />
      );
      expect(screen.getByText('🟢')).toBeInTheDocument();
      expect(screen.getByText('Low Risk')).toBeInTheDocument();

      rerender(<RiskWarning riskLevel="MODERATE" compact={true} />);
      expect(screen.getByText('🟡')).toBeInTheDocument();
      expect(screen.getByText('Moderate Risk')).toBeInTheDocument();

      rerender(<RiskWarning riskLevel="HIGH" compact={true} />);
      expect(screen.getByText('🔴')).toBeInTheDocument();
      expect(screen.getByText('High Risk')).toBeInTheDocument();

      rerender(<RiskWarning riskLevel="VERY_HIGH" compact={true} />);
      expect(screen.getByText('🟣')).toBeInTheDocument();
      expect(screen.getByText('Very High Risk')).toBeInTheDocument();
    });
  });

  describe('Full Mode', () => {
    it('should render full risk warning with all sections', () => {
      render(
        <RiskWarning
          riskLevel="HIGH"
          riskScore={80}
          riskMetrics={mockRiskMetrics}
          warnings={mockWarnings}
          mitigations={mockMitigations}
          symbol="AAPL"
        />
      );

      expect(screen.getByText('🔴')).toBeInTheDocument();
      expect(screen.getByText('High Risk')).toBeInTheDocument();
      expect(screen.getByText('(AAPL)')).toBeInTheDocument();
      expect(screen.getByText('Risk Score: 80/100')).toBeInTheDocument();
      expect(screen.getByText(/⚠️ Risk Warnings/)).toBeInTheDocument();
      expect(screen.getByText(/📊 Key Risk Factors/)).toBeInTheDocument();
      expect(screen.getByText(/💡 Risk Mitigation/)).toBeInTheDocument();
    });

    it('should display risk warnings section', () => {
      render(
        <RiskWarning
          riskLevel="HIGH"
          warnings={mockWarnings}
        />
      );

      expect(screen.getByText(/⚠️ Risk Warnings/)).toBeInTheDocument();
      mockWarnings.forEach(warning => {
        expect(screen.getByText(warning)).toBeInTheDocument();
      });
    });

    it('should display risk metrics with correct styling', () => {
      render(
        <RiskWarning
          riskLevel="HIGH"
          riskMetrics={mockRiskMetrics}
        />
      );

      expect(screen.getByText(/📊 Key Risk Factors/)).toBeInTheDocument();
      
      // Should show high-priority metrics (HIGH and VERY_HIGH)
      expect(screen.getByText('Volatility Risk')).toBeInTheDocument();
      expect(screen.getByText('High volatility risk detected')).toBeInTheDocument();
      
      // Should not show low-priority metrics initially
      expect(screen.queryByText('Debt Risk')).not.toBeInTheDocument();
    });

    it('should display mitigation suggestions', () => {
      render(
        <RiskWarning
          riskLevel="HIGH"
          mitigations={mockMitigations}
        />
      );

      expect(screen.getByText(/💡 Risk Mitigation/)).toBeInTheDocument();
      mockMitigations.slice(0, 3).forEach(mitigation => {
        expect(screen.getByText(mitigation)).toBeInTheDocument();
      });
    });

    it('should show expand/collapse functionality for long lists', async () => {
      const user = userEvent.setup();
      const longWarnings = Array.from({ length: 5 }, (_, i) => `Warning ${i + 1}`);
      
      render(
        <RiskWarning
          riskLevel="HIGH"
          warnings={longWarnings}
        />
      );

      // Should show first 3 warnings and "more" indicator
      expect(screen.getByText('Warning 1')).toBeInTheDocument();
      expect(screen.getByText('Warning 2')).toBeInTheDocument();
      expect(screen.getByText('Warning 3')).toBeInTheDocument();
      expect(screen.getByText('+2 more warnings')).toBeInTheDocument();
      expect(screen.queryByText('Warning 4')).not.toBeInTheDocument();

      // Click to expand
      await user.click(screen.getByText('Show All'));

      expect(screen.getByText('Warning 4')).toBeInTheDocument();
      expect(screen.getByText('Warning 5')).toBeInTheDocument();
      expect(screen.getByText('Show Less')).toBeInTheDocument();

      // Click to collapse
      await user.click(screen.getByText('Show Less'));

      expect(screen.queryByText('Warning 4')).not.toBeInTheDocument();
      expect(screen.queryByText('Warning 5')).not.toBeInTheDocument();
    });

    it('should show disclaimer for high-risk investments', () => {
      render(
        <RiskWarning riskLevel="HIGH" />
      );

      expect(screen.getByText(/⚠️ Important:/)).toBeInTheDocument();
      expect(screen.getByText(/high-risk investments can result in significant losses/i)).toBeInTheDocument();
    });

    it('should show disclaimer for very high-risk investments', () => {
      render(
        <RiskWarning riskLevel="VERY_HIGH" />
      );

      expect(screen.getByText(/⚠️ Important:/)).toBeInTheDocument();
      expect(screen.getByText(/high-risk investments can result in significant losses/i)).toBeInTheDocument();
    });

    it('should not show disclaimer for low and moderate risk', () => {
      const { rerender } = render(
        <RiskWarning riskLevel="LOW" />
      );

      expect(screen.queryByText(/⚠️ Important:/)).not.toBeInTheDocument();

      rerender(<RiskWarning riskLevel="MODERATE" />);
      expect(screen.queryByText(/⚠️ Important:/)).not.toBeInTheDocument();
    });

    it('should handle empty data gracefully', () => {
      render(
        <RiskWarning
          riskLevel="MODERATE"
          riskMetrics={[]}
          warnings={[]}
          mitigations={[]}
        />
      );

      expect(screen.getByText('Moderate Risk')).toBeInTheDocument();
      expect(screen.queryByText(/⚠️ Risk Warnings/)).not.toBeInTheDocument();
      expect(screen.queryByText(/📊 Key Risk Factors/)).not.toBeInTheDocument();
      expect(screen.queryByText(/💡 Risk Mitigation/)).not.toBeInTheDocument();
    });

    it('should expand all metrics when show all button is clicked', async () => {
      const user = userEvent.setup();
      const manyMetrics = Array.from({ length: 5 }, (_, i) => ({
        name: `Risk ${i + 1}`,
        value: 0.5,
        risk_level: i < 2 ? 'HIGH' : 'LOW' as const,
        description: `Description ${i + 1}`,
        impact: 'Medium' as const,
        mitigation: `Mitigation ${i + 1}`
      }));

      render(
        <RiskWarning
          riskLevel="HIGH"
          riskMetrics={manyMetrics}
        />
      );

      // Should show high-priority metrics first
      expect(screen.getByText('Risk 1')).toBeInTheDocument();
      expect(screen.getByText('Risk 2')).toBeInTheDocument();
      expect(screen.queryByText('Risk 3')).not.toBeInTheDocument();

      // Click to show all
      await user.click(screen.getByText(/Show All.*Risk Factors/));

      expect(screen.getByText('Risk 3')).toBeInTheDocument();
      expect(screen.getByText('Risk 4')).toBeInTheDocument();
      expect(screen.getByText('Risk 5')).toBeInTheDocument();
    });
  });

  describe('Risk Level Descriptions', () => {
    it('should show correct descriptions for each risk level', () => {
      const { rerender } = render(<RiskWarning riskLevel="LOW" />);
      expect(screen.getByText(/low risk characteristics/i)).toBeInTheDocument();

      rerender(<RiskWarning riskLevel="MODERATE" />);
      expect(screen.getByText(/moderate risk/i)).toBeInTheDocument();

      rerender(<RiskWarning riskLevel="HIGH" />);
      expect(screen.getByText(/high risk.*careful consideration/i)).toBeInTheDocument();

      rerender(<RiskWarning riskLevel="VERY_HIGH" />);
      expect(screen.getByText(/very high risk.*risk-tolerant investors/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(
        <RiskWarning
          riskLevel="HIGH"
          warnings={mockWarnings}
          compact={true}
        />
      );

      const compactWarning = screen.getByText('High Risk').closest('.risk-warning-compact');
      expect(compactWarning).toHaveAttribute('title');
    });

    it('should be keyboard accessible', async () => {
      const user = userEvent.setup();
      render(
        <RiskWarning
          riskLevel="HIGH"
          warnings={mockWarnings}
          compact={true}
        />
      );

      const compactWarning = screen.getByText('High Risk').closest('.risk-warning-compact');
      
      // Should be focusable
      compactWarning?.focus();
      expect(compactWarning).toHaveFocus();

      // Should expand on Enter key
      await user.keyboard('{Enter}');
      expect(screen.getByText('▼')).toBeInTheDocument();
    });
  });

  describe('Props Validation', () => {
    it('should handle showDetails prop', () => {
      render(
        <RiskWarning
          riskLevel="HIGH"
          warnings={mockWarnings}
          showDetails={true}
        />
      );

      // Should start expanded
      expect(screen.getByText(mockWarnings[0])).toBeInTheDocument();
    });

    it('should handle missing optional props', () => {
      render(<RiskWarning riskLevel="MODERATE" />);

      expect(screen.getByText('Moderate Risk')).toBeInTheDocument();
      expect(screen.getByText(/moderate risk/i)).toBeInTheDocument();
    });
  });
});