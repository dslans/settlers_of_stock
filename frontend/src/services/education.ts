/**
 * Educational service for managing learning content and progress
 */

export interface EducationalConcept {
  id: number;
  name: string;
  concept_type: string;
  difficulty_level: string;
  short_description: string;
  detailed_explanation: string;
  practical_example?: string;
  formula?: string;
  interpretation_guide?: string;
  common_mistakes?: string;
  keywords?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  related_concepts?: EducationalConceptSummary[];
}

export interface EducationalConceptSummary {
  id: number;
  name: string;
  concept_type: string;
  difficulty_level: string;
  short_description: string;
}

export interface ConceptExplanationRequest {
  concept_name: string;
  context?: string;
  user_level?: 'beginner' | 'intermediate' | 'advanced';
}

export interface ConceptExplanationResponse {
  concept: EducationalConcept;
  contextual_explanation: string;
  related_suggestions: EducationalConceptSummary[];
  next_learning_steps: string[];
}

export interface LearningProgress {
  id: number;
  user_id: number;
  concept_id: number;
  concept: EducationalConceptSummary;
  is_completed: boolean;
  completion_date?: string;
  difficulty_rating?: number;
  created_at: string;
  updated_at: string;
}

export interface LearningPathSuggestion {
  suggestions: string[];
  recommended_concepts: EducationalConceptSummary[];
  estimated_duration_minutes: number;
}

class EducationService {
  private baseUrl = '/api/v1/education';

  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  /**
   * Search for educational concepts
   */
  async searchConcepts(
    query?: string,
    conceptType?: string,
    difficultyLevel?: string,
    limit: number = 20
  ): Promise<EducationalConcept[]> {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (conceptType) params.append('concept_type', conceptType);
    if (difficultyLevel) params.append('difficulty_level', difficultyLevel);
    params.append('limit', limit.toString());

    const response = await fetch(`${this.baseUrl}/concepts/search?${params}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to search concepts: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get explanation for a specific concept
   */
  async explainConcept(request: ConceptExplanationRequest): Promise<ConceptExplanationResponse> {
    const response = await fetch(`${this.baseUrl}/explain`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Failed to get concept explanation: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get user's learning progress
   */
  async getLearningProgress(): Promise<LearningProgress[]> {
    const response = await fetch(`${this.baseUrl}/progress`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to get learning progress: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Mark a concept as completed
   */
  async markConceptCompleted(
    conceptId: number,
    difficultyRating?: number
  ): Promise<LearningProgress> {
    const response = await fetch(`${this.baseUrl}/progress/${conceptId}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        completed: true,
        difficulty_rating: difficultyRating
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to mark concept as completed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get learning path suggestions
   */
  async getLearningPathSuggestions(
    userLevel: 'beginner' | 'intermediate' | 'advanced' = 'beginner'
  ): Promise<LearningPathSuggestion> {
    const response = await fetch(`${this.baseUrl}/learning-paths/suggestions?user_level=${userLevel}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to get learning path suggestions: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get contextual learning suggestions based on chat content
   */
  async getContextualSuggestions(
    chatContent: string,
    stockSymbol?: string
  ): Promise<EducationalConceptSummary[]> {
    const response = await fetch(`${this.baseUrl}/contextual-suggestions`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        content: chatContent,
        stock_symbol: stockSymbol
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to get contextual suggestions: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Track concept interaction (for analytics)
   */
  async trackConceptInteraction(
    conceptName: string,
    interactionType: 'tooltip_view' | 'explanation_request' | 'completion',
    context?: string
  ): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/track-interaction`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          concept_name: conceptName,
          interaction_type: interactionType,
          context: context
        })
      });
    } catch (error) {
      // Don't throw errors for tracking - it's not critical
      console.warn('Failed to track concept interaction:', error);
    }
  }
}

export const educationService = new EducationService();