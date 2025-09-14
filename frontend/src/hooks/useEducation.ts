/**
 * Hook for managing educational features and progress
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  educationService, 
  EducationalConcept, 
  LearningProgress, 
  LearningPathSuggestion,
  EducationalConceptSummary 
} from '../services/education';

interface UseEducationReturn {
  // Concepts
  concepts: EducationalConcept[];
  searchConcepts: (query?: string, type?: string, level?: string) => Promise<void>;
  isLoadingConcepts: boolean;
  conceptsError: string | null;

  // Progress
  progress: LearningProgress[];
  refreshProgress: () => Promise<void>;
  markCompleted: (conceptId: number, rating?: number) => Promise<void>;
  isLoadingProgress: boolean;
  progressError: string | null;

  // Learning Path
  suggestions: LearningPathSuggestion | null;
  refreshSuggestions: (userLevel?: 'beginner' | 'intermediate' | 'advanced') => Promise<void>;
  isLoadingSuggestions: boolean;
  suggestionsError: string | null;

  // Contextual Learning
  getContextualSuggestions: (chatContent: string, stockSymbol?: string) => Promise<EducationalConceptSummary[]>;

  // Statistics
  getProgressStats: () => {
    totalConcepts: number;
    completedConcepts: number;
    progressPercentage: number;
    recentCompletions: LearningProgress[];
  };
}

export const useEducation = (): UseEducationReturn => {
  // Concepts state
  const [concepts, setConcepts] = useState<EducationalConcept[]>([]);
  const [isLoadingConcepts, setIsLoadingConcepts] = useState(false);
  const [conceptsError, setConceptsError] = useState<string | null>(null);

  // Progress state
  const [progress, setProgress] = useState<LearningProgress[]>([]);
  const [isLoadingProgress, setIsLoadingProgress] = useState(false);
  const [progressError, setProgressError] = useState<string | null>(null);

  // Suggestions state
  const [suggestions, setSuggestions] = useState<LearningPathSuggestion | null>(null);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [suggestionsError, setSuggestionsError] = useState<string | null>(null);

  // Search concepts
  const searchConcepts = useCallback(async (
    query?: string,
    type?: string,
    level?: string
  ) => {
    setIsLoadingConcepts(true);
    setConceptsError(null);

    try {
      const results = await educationService.searchConcepts(query, type, level);
      setConcepts(results);
    } catch (error) {
      setConceptsError(error instanceof Error ? error.message : 'Failed to search concepts');
    } finally {
      setIsLoadingConcepts(false);
    }
  }, []);

  // Refresh progress
  const refreshProgress = useCallback(async () => {
    setIsLoadingProgress(true);
    setProgressError(null);

    try {
      const progressData = await educationService.getLearningProgress();
      setProgress(progressData);
    } catch (error) {
      setProgressError(error instanceof Error ? error.message : 'Failed to load progress');
    } finally {
      setIsLoadingProgress(false);
    }
  }, []);

  // Mark concept as completed
  const markCompleted = useCallback(async (conceptId: number, rating?: number) => {
    try {
      await educationService.markConceptCompleted(conceptId, rating);
      await refreshProgress(); // Refresh progress after marking complete
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Failed to mark concept as completed');
    }
  }, [refreshProgress]);

  // Refresh suggestions
  const refreshSuggestions = useCallback(async (
    userLevel: 'beginner' | 'intermediate' | 'advanced' = 'beginner'
  ) => {
    setIsLoadingSuggestions(true);
    setSuggestionsError(null);

    try {
      const suggestionsData = await educationService.getLearningPathSuggestions(userLevel);
      setSuggestions(suggestionsData);
    } catch (error) {
      setSuggestionsError(error instanceof Error ? error.message : 'Failed to load suggestions');
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, []);

  // Get contextual suggestions
  const getContextualSuggestions = useCallback(async (
    chatContent: string,
    stockSymbol?: string
  ): Promise<EducationalConceptSummary[]> => {
    try {
      return await educationService.getContextualSuggestions(chatContent, stockSymbol);
    } catch (error) {
      console.warn('Failed to get contextual suggestions:', error);
      return [];
    }
  }, []);

  // Calculate progress statistics
  const getProgressStats = useCallback(() => {
    const totalConcepts = progress.length;
    const completedConcepts = progress.filter(p => p.is_completed).length;
    const progressPercentage = totalConcepts > 0 ? Math.round((completedConcepts / totalConcepts) * 100) : 0;
    
    // Get recent completions (last 7 days)
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    
    const recentCompletions = progress.filter(p => 
      p.is_completed && 
      p.completion_date && 
      new Date(p.completion_date) >= sevenDaysAgo
    ).sort((a, b) => 
      new Date(b.completion_date!).getTime() - new Date(a.completion_date!).getTime()
    );

    return {
      totalConcepts,
      completedConcepts,
      progressPercentage,
      recentCompletions
    };
  }, [progress]);

  // Load initial data
  useEffect(() => {
    searchConcepts();
    refreshProgress();
    refreshSuggestions();
  }, [searchConcepts, refreshProgress, refreshSuggestions]);

  return {
    // Concepts
    concepts,
    searchConcepts,
    isLoadingConcepts,
    conceptsError,

    // Progress
    progress,
    refreshProgress,
    markCompleted,
    isLoadingProgress,
    progressError,

    // Learning Path
    suggestions,
    refreshSuggestions,
    isLoadingSuggestions,
    suggestionsError,

    // Contextual Learning
    getContextualSuggestions,

    // Statistics
    getProgressStats
  };
};