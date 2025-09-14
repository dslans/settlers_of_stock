/**
 * useDisclaimer Hook
 * 
 * React hook for managing disclaimer acknowledgments and display logic
 */

import { useState, useEffect, useCallback } from 'react';
import { disclaimerService, DisclaimerContext } from '../services/disclaimer';

interface UseDisclaimerOptions {
  userId?: string;
  context?: DisclaimerContext;
  autoLoad?: boolean;
}

interface UseDisclaimerReturn {
  showStartupDisclaimer: boolean;
  showDisclaimerModal: boolean;
  hasAcknowledgedContext: (context: DisclaimerContext) => boolean;
  acknowledgeDisclaimer: (disclaimerId: string) => void;
  openDisclaimerModal: () => void;
  closeDisclaimerModal: () => void;
  handleStartupAccept: () => void;
  needsAcknowledgment: (context: DisclaimerContext) => boolean;
}

export const useDisclaimer = (options: UseDisclaimerOptions = {}): UseDisclaimerReturn => {
  const { userId, context, autoLoad = true } = options;
  
  const [showStartupDisclaimer, setShowStartupDisclaimer] = useState(false);
  const [showDisclaimerModal, setShowDisclaimerModal] = useState(false);
  const [acknowledgmentStatus, setAcknowledgmentStatus] = useState<{ [key: string]: boolean }>({});

  // Load user acknowledgments on mount
  useEffect(() => {
    if (userId && autoLoad) {
      disclaimerService.loadUserAcknowledgments(userId);
      
      // Check if startup disclaimers need to be shown
      const needsStartup = !disclaimerService.hasUserAcknowledgedContext(userId, 'app_startup');
      setShowStartupDisclaimer(needsStartup);
      
      // Update acknowledgment status
      const contexts: DisclaimerContext[] = [
        'app_startup',
        'chat_response',
        'analysis_result',
        'recommendation',
        'backtest',
        'export',
        'shared_analysis'
      ];
      
      const status: { [key: string]: boolean } = {};
      contexts.forEach(ctx => {
        status[ctx] = disclaimerService.hasUserAcknowledgedContext(userId, ctx);
      });
      setAcknowledgmentStatus(status);
    }
  }, [userId, autoLoad]);

  const hasAcknowledgedContext = useCallback((context: DisclaimerContext): boolean => {
    if (!userId) return false;
    return disclaimerService.hasUserAcknowledgedContext(userId, context);
  }, [userId]);

  const acknowledgeDisclaimer = useCallback((disclaimerId: string) => {
    if (!userId) return;
    disclaimerService.acknowledgeDisclaimer(userId, disclaimerId);
    
    // Update local state
    setAcknowledgmentStatus(prev => ({
      ...prev,
      [disclaimerId]: true
    }));
  }, [userId]);

  const openDisclaimerModal = useCallback(() => {
    setShowDisclaimerModal(true);
  }, []);

  const closeDisclaimerModal = useCallback(() => {
    setShowDisclaimerModal(false);
  }, []);

  const handleStartupAccept = useCallback(() => {
    setShowStartupDisclaimer(false);
    
    // Mark startup context as acknowledged
    if (userId) {
      const startupDisclaimers = disclaimerService.getRequiredDisclaimersForContext('app_startup');
      startupDisclaimers.forEach(disclaimer => {
        disclaimerService.acknowledgeDisclaimer(userId, disclaimer.id);
      });
      
      setAcknowledgmentStatus(prev => ({
        ...prev,
        app_startup: true
      }));
    }
  }, [userId]);

  const needsAcknowledgment = useCallback((context: DisclaimerContext): boolean => {
    if (!userId) return false;
    return !disclaimerService.hasUserAcknowledgedContext(userId, context);
  }, [userId]);

  return {
    showStartupDisclaimer,
    showDisclaimerModal,
    hasAcknowledgedContext,
    acknowledgeDisclaimer,
    openDisclaimerModal,
    closeDisclaimerModal,
    handleStartupAccept,
    needsAcknowledgment
  };
};