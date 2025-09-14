/**
 * Educational tooltip component that provides explanations for financial concepts
 */

import React, { useState, useEffect } from 'react';
import { educationService, ConceptExplanationResponse } from '../services/education';
import './EducationalTooltip.css';



interface EducationalTooltipProps {
  concept: string;
  context?: string;
  children: React.ReactNode;
  userLevel?: 'beginner' | 'intermediate' | 'advanced';
}

const EducationalTooltip: React.FC<EducationalTooltipProps> = ({
  concept,
  context,
  children,
  userLevel = 'beginner'
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [explanation, setExplanation] = useState<ConceptExplanationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchExplanation = async () => {
    if (explanation || loading) return;

    setLoading(true);
    setError(null);

    try {
      const data = await educationService.explainConcept({
        concept_name: concept,
        context: context,
        user_level: userLevel
      });
      
      setExplanation(data);
      
      // Track the tooltip interaction
      await educationService.trackConceptInteraction(
        concept,
        'tooltip_view',
        context
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleMouseEnter = () => {
    setIsVisible(true);
    fetchExplanation();
  };

  const handleMouseLeave = () => {
    setIsVisible(false);
  };

  return (
    <div className="educational-tooltip-container">
      <span
        className="educational-tooltip-trigger"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {children}
        <span className="educational-indicator">?</span>
      </span>

      {isVisible && (
        <div className="educational-tooltip-content">
          {loading && (
            <div className="educational-tooltip-loading">
              <div className="spinner"></div>
              <span>Loading explanation...</span>
            </div>
          )}

          {error && (
            <div className="educational-tooltip-error">
              <span>Failed to load explanation: {error}</span>
            </div>
          )}

          {explanation && (
            <div className="educational-tooltip-explanation">
              <div className="concept-header">
                <h4>{explanation.concept.name}</h4>
                <span className={`difficulty-badge ${explanation.concept.difficulty_level}`}>
                  {explanation.concept.difficulty_level}
                </span>
              </div>

              <div className="concept-description">
                <p>{explanation.contextual_explanation}</p>
              </div>

              {explanation.concept.formula && (
                <div className="concept-formula">
                  <strong>Formula:</strong>
                  <code>{explanation.concept.formula}</code>
                </div>
              )}

              {explanation.concept.practical_example && (
                <div className="concept-example">
                  <strong>Example:</strong>
                  <p>{explanation.concept.practical_example}</p>
                </div>
              )}

              {explanation.next_learning_steps.length > 0 && (
                <div className="learning-steps">
                  <strong>Next Steps:</strong>
                  <ul>
                    {explanation.next_learning_steps.slice(0, 2).map((step, index) => (
                      <li key={index}>{step}</li>
                    ))}
                  </ul>
                </div>
              )}

              {explanation.related_suggestions.length > 0 && (
                <div className="related-concepts">
                  <strong>Related:</strong>
                  <div className="related-tags">
                    {explanation.related_suggestions.slice(0, 3).map((related) => (
                      <span key={related.id} className="related-tag">
                        {related.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EducationalTooltip;