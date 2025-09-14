/**
 * Tests for Disclaimer Service
 */

import { disclaimerService, DisclaimerContext } from '../disclaimer';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('DisclaimerService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('getDisclaimersForContext', () => {
    it('should return disclaimers for chat_response context', () => {
      const disclaimers = disclaimerService.getDisclaimersForContext('chat_response');
      expect(disclaimers.length).toBeGreaterThan(0);
      expect(disclaimers.some(d => d.id === 'investment_advice')).toBe(true);
    });

    it('should return disclaimers for recommendation context', () => {
      const disclaimers = disclaimerService.getDisclaimersForContext('recommendation');
      expect(disclaimers.length).toBeGreaterThan(0);
      expect(disclaimers.some(d => d.id === 'investment_advice')).toBe(true);
      expect(disclaimers.some(d => d.id === 'market_volatility')).toBe(true);
    });

    it('should return disclaimers for backtest context', () => {
      const disclaimers = disclaimerService.getDisclaimersForContext('backtest');
      expect(disclaimers.length).toBeGreaterThan(0);
      expect(disclaimers.some(d => d.id === 'backtesting_limitations')).toBe(true);
    });

    it('should return empty array for unknown context', () => {
      const disclaimers = disclaimerService.getDisclaimersForContext('unknown' as DisclaimerContext);
      expect(disclaimers).toEqual([]);
    });
  });

  describe('getRequiredDisclaimersForContext', () => {
    it('should return only required disclaimers', () => {
      const disclaimers = disclaimerService.getRequiredDisclaimersForContext('recommendation');
      expect(disclaimers.every(d => d.required)).toBe(true);
    });

    it('should filter out non-required disclaimers', () => {
      const allDisclaimers = disclaimerService.getDisclaimersForContext('recommendation');
      const requiredDisclaimers = disclaimerService.getRequiredDisclaimersForContext('recommendation');
      expect(requiredDisclaimers.length).toBeLessThanOrEqual(allDisclaimers.length);
    });
  });

  describe('acknowledgeDisclaimer', () => {
    const userId = 'test-user';
    const disclaimerId = 'investment_advice';

    it('should record disclaimer acknowledgment', () => {
      disclaimerService.acknowledgeDisclaimer(userId, disclaimerId);
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        `disclaimers_${userId}`,
        expect.stringContaining(disclaimerId)
      );
    });

    it('should replace existing acknowledgment for same disclaimer', () => {
      // Acknowledge twice
      disclaimerService.acknowledgeDisclaimer(userId, disclaimerId);
      disclaimerService.acknowledgeDisclaimer(userId, disclaimerId);
      
      // Should only have one acknowledgment
      const calls = localStorageMock.setItem.mock.calls;
      const lastCall = calls[calls.length - 1];
      const storedData = JSON.parse(lastCall[1]);
      const acknowledgments = storedData.filter((ack: any) => ack.disclaimerId === disclaimerId);
      expect(acknowledgments).toHaveLength(1);
    });
  });

  describe('hasUserAcknowledgedContext', () => {
    const userId = 'test-user';

    it('should return false when no acknowledgments exist', () => {
      const hasAcknowledged = disclaimerService.hasUserAcknowledgedContext(userId, 'chat_response');
      expect(hasAcknowledged).toBe(false);
    });

    it('should return true when all required disclaimers are acknowledged', () => {
      // Mock existing acknowledgments
      const mockAcknowledgments = [
        {
          userId,
          disclaimerId: 'investment_advice',
          acknowledgedAt: new Date().toISOString(),
          version: '1.0'
        },
        {
          userId,
          disclaimerId: 'ai_limitations',
          acknowledgedAt: new Date().toISOString(),
          version: '1.0'
        }
      ];
      
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockAcknowledgments));
      disclaimerService.loadUserAcknowledgments(userId);
      
      const hasAcknowledged = disclaimerService.hasUserAcknowledgedContext(userId, 'chat_response');
      expect(hasAcknowledged).toBe(true);
    });

    it('should return false when some required disclaimers are missing', () => {
      // Mock partial acknowledgments
      const mockAcknowledgments = [
        {
          userId,
          disclaimerId: 'investment_advice',
          acknowledgedAt: new Date().toISOString(),
          version: '1.0'
        }
        // Missing other required disclaimers
      ];
      
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockAcknowledgments));
      disclaimerService.loadUserAcknowledgments(userId);
      
      const hasAcknowledged = disclaimerService.hasUserAcknowledgedContext(userId, 'recommendation');
      expect(hasAcknowledged).toBe(false);
    });
  });

  describe('generateDisclaimerText', () => {
    it('should generate compact disclaimer text', () => {
      const text = disclaimerService.generateDisclaimerText('chat_response', true);
      expect(text).toContain('⚠️ Important');
      expect(text).toContain('informational purposes only');
      expect(text).toContain('not investment advice');
    });

    it('should generate full disclaimer text', () => {
      const text = disclaimerService.generateDisclaimerText('recommendation', false);
      expect(text).toContain('IMPORTANT DISCLAIMERS');
      expect(text).toContain('Investment Disclaimer');
      expect(text).toContain('Risk Warning');
    });

    it('should return empty string for contexts with no disclaimers', () => {
      const text = disclaimerService.generateDisclaimerText('unknown' as DisclaimerContext);
      expect(text).toBe('');
    });
  });

  describe('shouldShowHighRiskDisclaimer', () => {
    it('should return true for HIGH risk level', () => {
      const shouldShow = disclaimerService.shouldShowHighRiskDisclaimer('HIGH');
      expect(shouldShow).toBe(true);
    });

    it('should return true for VERY_HIGH risk level', () => {
      const shouldShow = disclaimerService.shouldShowHighRiskDisclaimer('VERY_HIGH');
      expect(shouldShow).toBe(true);
    });

    it('should return false for LOW risk level', () => {
      const shouldShow = disclaimerService.shouldShowHighRiskDisclaimer('LOW');
      expect(shouldShow).toBe(false);
    });

    it('should return true for high volatility', () => {
      const shouldShow = disclaimerService.shouldShowHighRiskDisclaimer(undefined, 0.4);
      expect(shouldShow).toBe(true);
    });

    it('should return false for low volatility', () => {
      const shouldShow = disclaimerService.shouldShowHighRiskDisclaimer(undefined, 0.1);
      expect(shouldShow).toBe(false);
    });
  });

  describe('getTermsOfUse', () => {
    it('should return terms of use text', () => {
      const terms = disclaimerService.getTermsOfUse();
      expect(terms).toContain('Terms of Use');
      expect(terms).toContain('Acceptance of Terms');
      expect(terms).toContain('Investment Disclaimer');
      expect(terms).toContain('Risk Acknowledgment');
    });
  });

  describe('getPrivacyPolicy', () => {
    it('should return privacy policy text', () => {
      const policy = disclaimerService.getPrivacyPolicy();
      expect(policy).toContain('Privacy Policy');
      expect(policy).toContain('Information We Collect');
      expect(policy).toContain('How We Use Information');
      expect(policy).toContain('Data Storage and Security');
    });
  });

  describe('loadUserAcknowledgments', () => {
    const userId = 'test-user';

    it('should load acknowledgments from localStorage', () => {
      const mockAcknowledgments = [
        {
          userId,
          disclaimerId: 'investment_advice',
          acknowledgedAt: new Date().toISOString(),
          version: '1.0'
        }
      ];
      
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockAcknowledgments));
      
      disclaimerService.loadUserAcknowledgments(userId);
      
      expect(localStorageMock.getItem).toHaveBeenCalledWith(`disclaimers_${userId}`);
    });

    it('should handle missing localStorage data gracefully', () => {
      localStorageMock.getItem.mockReturnValue(null);
      
      expect(() => {
        disclaimerService.loadUserAcknowledgments(userId);
      }).not.toThrow();
    });

    it('should handle corrupted localStorage data gracefully', () => {
      localStorageMock.getItem.mockReturnValue('invalid-json');
      
      expect(() => {
        disclaimerService.loadUserAcknowledgments(userId);
      }).not.toThrow();
    });
  });

  describe('getDisclaimer', () => {
    it('should return disclaimer by ID', () => {
      const disclaimer = disclaimerService.getDisclaimer('investment_advice');
      expect(disclaimer).toBeDefined();
      expect(disclaimer?.id).toBe('investment_advice');
      expect(disclaimer?.title).toBe('Investment Disclaimer');
    });

    it('should return undefined for unknown ID', () => {
      const disclaimer = disclaimerService.getDisclaimer('unknown-id');
      expect(disclaimer).toBeUndefined();
    });
  });

  describe('getAllDisclaimers', () => {
    it('should return all disclaimers', () => {
      const disclaimers = disclaimerService.getAllDisclaimers();
      expect(disclaimers.length).toBeGreaterThan(0);
      expect(disclaimers.some(d => d.id === 'investment_advice')).toBe(true);
      expect(disclaimers.some(d => d.id === 'risk_warning')).toBe(true);
      expect(disclaimers.some(d => d.id === 'ai_limitations')).toBe(true);
    });
  });
});