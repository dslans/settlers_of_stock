/**
 * Tests for useDisclaimer Hook
 */

import { renderHook, act } from '@testing-library/react';
import { useDisclaimer } from '../useDisclaimer';

// Mock the disclaimer service
jest.mock('../../services/disclaimer', () => ({
  disclaimerService: {
    loadUserAcknowledgments: jest.fn(),
    hasUserAcknowledgedContext: jest.fn(),
    acknowledgeDisclaimer: jest.fn(),
    getRequiredDisclaimersForContext: jest.fn(),
  }
}));

import { disclaimerService } from '../../services/disclaimer';

const mockDisclaimerService = disclaimerService as jest.Mocked<typeof disclaimerService>;

describe('useDisclaimer', () => {
  const userId = 'test-user';

  beforeEach(() => {
    jest.clearAllMocks();
    mockDisclaimerService.getRequiredDisclaimersForContext.mockReturnValue([
      { id: 'investment_advice', title: 'Investment Disclaimer', content: 'Test', severity: 'warning', required: true, contexts: ['app_startup'] }
    ]);
  });

  it('should initialize with default values', () => {
    mockDisclaimerService.hasUserAcknowledgedContext.mockReturnValue(true);

    const { result } = renderHook(() => useDisclaimer({ userId }));

    expect(result.current.showStartupDisclaimer).toBe(false);
    expect(result.current.showDisclaimerModal).toBe(false);
  });

  it('should show startup disclaimer when user has not acknowledged', () => {
    mockDisclaimerService.hasUserAcknowledgedContext.mockReturnValue(false);

    const { result } = renderHook(() => useDisclaimer({ userId }));

    expect(result.current.showStartupDisclaimer).toBe(true);
  });

  it('should not show startup disclaimer when user has acknowledged', () => {
    mockDisclaimerService.hasUserAcknowledgedContext.mockReturnValue(true);

    const { result } = renderHook(() => useDisclaimer({ userId }));

    expect(result.current.showStartupDisclaimer).toBe(false);
  });

  it('should load user acknowledgments on mount when autoLoad is true', () => {
    mockDisclaimerService.hasUserAcknowledgedContext.mockReturnValue(true);

    renderHook(() => useDisclaimer({ userId, autoLoad: true }));

    expect(mockDisclaimerService.loadUserAcknowledgments).toHaveBeenCalledWith(userId);
  });

  it('should not load user acknowledgments when autoLoad is false', () => {
    mockDisclaimerService.hasUserAcknowledgedContext.mockReturnValue(true);

    renderHook(() => useDisclaimer({ userId, autoLoad: false }));

    expect(mockDisclaimerService.loadUserAcknowledgments).not.toHaveBeenCalled();
  });

  it('should not load user acknowledgments when userId is not provided', () => {
    renderHook(() => useDisclaimer({}));

    expect(mockDisclaimerService.loadUserAcknowledgments).not.toHaveBeenCalled();
  });

  it('should handle hasAcknowledgedContext correctly', () => {
    // Set up mock to return false for app_startup (initial load) and false for chat_response
    mockDisclaimerService.hasUserAcknowledgedContext.mockImplementation((userId, context) => {
      if (context === 'app_startup') return false;
      if (context === 'chat_response') return false;
      return true; // Default for other contexts
    });

    const { result } = renderHook(() => useDisclaimer({ userId }));

    const hasAcknowledged = result.current.hasAcknowledgedContext('chat_response');
    expect(hasAcknowledged).toBe(false);
    expect(mockDisclaimerService.hasUserAcknowledgedContext).toHaveBeenCalledWith(userId, 'chat_response');
  });

  it('should return false for hasAcknowledgedContext when no userId', () => {
    const { result } = renderHook(() => useDisclaimer({}));

    const hasAcknowledged = result.current.hasAcknowledgedContext('chat_response');
    expect(hasAcknowledged).toBe(false);
  });

  it('should acknowledge disclaimer correctly', () => {
    mockDisclaimerService.hasUserAcknowledgedContext.mockReturnValue(true);

    const { result } = renderHook(() => useDisclaimer({ userId }));

    act(() => {
      result.current.acknowledgeDisclaimer('investment_advice');
    });

    expect(mockDisclaimerService.acknowledgeDisclaimer).toHaveBeenCalledWith(userId, 'investment_advice');
  });

  it('should not acknowledge disclaimer when no userId', () => {
    const { result } = renderHook(() => useDisclaimer({}));

    act(() => {
      result.current.acknowledgeDisclaimer('investment_advice');
    });

    expect(mockDisclaimerService.acknowledgeDisclaimer).not.toHaveBeenCalled();
  });

  it('should open and close disclaimer modal', () => {
    mockDisclaimerService.hasUserAcknowledgedContext.mockReturnValue(true);

    const { result } = renderHook(() => useDisclaimer({ userId }));

    // Initially closed
    expect(result.current.showDisclaimerModal).toBe(false);

    // Open modal
    act(() => {
      result.current.openDisclaimerModal();
    });
    expect(result.current.showDisclaimerModal).toBe(true);

    // Close modal
    act(() => {
      result.current.closeDisclaimerModal();
    });
    expect(result.current.showDisclaimerModal).toBe(false);
  });

  it('should handle startup accept correctly', () => {
    mockDisclaimerService.hasUserAcknowledgedContext.mockReturnValue(false);

    const { result } = renderHook(() => useDisclaimer({ userId }));

    // Initially showing startup disclaimer
    expect(result.current.showStartupDisclaimer).toBe(true);

    act(() => {
      result.current.handleStartupAccept();
    });

    // Should hide startup disclaimer
    expect(result.current.showStartupDisclaimer).toBe(false);
    
    // Should acknowledge required disclaimers
    expect(mockDisclaimerService.acknowledgeDisclaimer).toHaveBeenCalledWith(userId, 'investment_advice');
  });

  it('should handle startup accept without userId', () => {
    const { result } = renderHook(() => useDisclaimer({}));

    act(() => {
      result.current.handleStartupAccept();
    });

    // Should not crash and should not call acknowledge
    expect(mockDisclaimerService.acknowledgeDisclaimer).not.toHaveBeenCalled();
  });

  it('should check if context needs acknowledgment', () => {
    mockDisclaimerService.hasUserAcknowledgedContext
      .mockReturnValueOnce(true) // For initial load
      .mockReturnValueOnce(false); // For needsAcknowledgment call

    const { result } = renderHook(() => useDisclaimer({ userId }));

    const needsAck = result.current.needsAcknowledgment('recommendation');
    expect(needsAck).toBe(true);
    expect(mockDisclaimerService.hasUserAcknowledgedContext).toHaveBeenCalledWith(userId, 'recommendation');
  });

  it('should return false for needsAcknowledgment when no userId', () => {
    const { result } = renderHook(() => useDisclaimer({}));

    const needsAck = result.current.needsAcknowledgment('recommendation');
    expect(needsAck).toBe(false);
  });

  it('should update acknowledgment status when acknowledging disclaimers', () => {
    mockDisclaimerService.hasUserAcknowledgedContext.mockReturnValue(false);

    const { result } = renderHook(() => useDisclaimer({ userId }));

    // Initially needs acknowledgment
    expect(result.current.needsAcknowledgment('app_startup')).toBe(true);

    // Acknowledge disclaimer
    act(() => {
      result.current.acknowledgeDisclaimer('investment_advice');
    });

    // Status should be updated locally
    expect(mockDisclaimerService.acknowledgeDisclaimer).toHaveBeenCalledWith(userId, 'investment_advice');
  });

  it('should handle multiple contexts correctly', () => {
    mockDisclaimerService.hasUserAcknowledgedContext.mockImplementation((userId, context) => {
      const contextMap: { [key: string]: boolean } = {
        'app_startup': true,
        'chat_response': false,
        'analysis_result': true,
        'recommendation': false,
        'backtest': true,
        'export': false,
        'shared_analysis': true
      };
      return contextMap[context] || false;
    });

    const { result } = renderHook(() => useDisclaimer({ userId }));

    // Check various contexts
    expect(result.current.hasAcknowledgedContext('chat_response')).toBe(false);
    expect(result.current.hasAcknowledgedContext('analysis_result')).toBe(true);
    expect(result.current.needsAcknowledgment('recommendation')).toBe(true);
    expect(result.current.needsAcknowledgment('backtest')).toBe(false);
  });
});