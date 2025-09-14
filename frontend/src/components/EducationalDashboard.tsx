/**
 * Educational dashboard component for learning financial concepts
 */

import React, { useState } from 'react';
import { useEducation } from '../hooks/useEducation';
import './EducationalDashboard.css';

const EducationalDashboard: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedLevel, setSelectedLevel] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'explore' | 'progress' | 'suggestions'>('explore');

  const {
    concepts,
    searchConcepts,
    isLoadingConcepts,
    progress,
    markCompleted,
    suggestions,
    getProgressStats
  } = useEducation();

  const conceptTypes = [
    { value: '', label: 'All Types' },
    { value: 'technical_indicator', label: 'Technical Indicators' },
    { value: 'fundamental_ratio', label: 'Fundamental Ratios' },
    { value: 'market_concept', label: 'Market Concepts' },
    { value: 'trading_strategy', label: 'Trading Strategies' },
    { value: 'risk_management', label: 'Risk Management' }
  ];

  const difficultyLevels = [
    { value: '', label: 'All Levels' },
    { value: 'beginner', label: 'Beginner' },
    { value: 'intermediate', label: 'Intermediate' },
    { value: 'advanced', label: 'Advanced' }
  ];

  // Handle search when filters change
  React.useEffect(() => {
    searchConcepts(searchQuery || undefined, selectedType || undefined, selectedLevel || undefined);
  }, [searchQuery, selectedType, selectedLevel, searchConcepts]);

  const handleMarkCompleted = async (conceptId: number) => {
    try {
      await markCompleted(conceptId);
    } catch (error) {
      console.error('Failed to mark as completed:', error);
    }
  };

  const progressStats = getProgressStats();

  const getDifficultyColor = (level: string) => {
    switch (level) {
      case 'beginner': return '#28a745';
      case 'intermediate': return '#ffc107';
      case 'advanced': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'technical_indicator': return '📈';
      case 'fundamental_ratio': return '📊';
      case 'market_concept': return '🏦';
      case 'trading_strategy': return '🎯';
      case 'risk_management': return '🛡️';
      default: return '📚';
    }
  };

  return (
    <div className="educational-dashboard">
      <div className="dashboard-header">
        <h2>Financial Education Center</h2>
        <p>Learn financial concepts to improve your investment knowledge</p>
      </div>

      <div className="dashboard-tabs">
        <button 
          className={`tab ${activeTab === 'explore' ? 'active' : ''}`}
          onClick={() => setActiveTab('explore')}
        >
          Explore Concepts
        </button>
        <button 
          className={`tab ${activeTab === 'progress' ? 'active' : ''}`}
          onClick={() => setActiveTab('progress')}
        >
          My Progress
        </button>
        <button 
          className={`tab ${activeTab === 'suggestions' ? 'active' : ''}`}
          onClick={() => setActiveTab('suggestions')}
        >
          Learning Path
        </button>
      </div>

      {activeTab === 'explore' && (
        <div className="explore-section">
          <div className="search-filters">
            <div className="search-bar">
              <input
                type="text"
                placeholder="Search concepts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>
            
            <div className="filters">
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="filter-select"
              >
                {conceptTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
              
              <select
                value={selectedLevel}
                onChange={(e) => setSelectedLevel(e.target.value)}
                className="filter-select"
              >
                {difficultyLevels.map(level => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {isLoadingConcepts ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <span>Loading concepts...</span>
            </div>
          ) : (
            <div className="concepts-grid">
              {concepts.map(concept => (
                <div key={concept.id} className="concept-card">
                  <div className="concept-header">
                    <span className="concept-icon">
                      {getTypeIcon(concept.concept_type)}
                    </span>
                    <h3>{concept.name}</h3>
                    <span 
                      className="difficulty-badge"
                      style={{ backgroundColor: getDifficultyColor(concept.difficulty_level) }}
                    >
                      {concept.difficulty_level}
                    </span>
                  </div>
                  
                  <p className="concept-description">
                    {concept.short_description}
                  </p>
                  
                  {concept.formula && (
                    <div className="concept-formula">
                      <strong>Formula:</strong>
                      <code>{concept.formula}</code>
                    </div>
                  )}
                  
                  <div className="concept-actions">
                    <button 
                      className="learn-button"
                      onClick={() => handleMarkCompleted(concept.id)}
                    >
                      Mark as Learned
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'progress' && (
        <div className="progress-section">
          <div className="progress-overview">
            <div className="progress-stats">
              <div className="stat-card">
                <h3>{progressStats.completedConcepts}</h3>
                <p>Concepts Learned</p>
              </div>
              <div className="stat-card">
                <h3>{progressStats.progressPercentage}%</h3>
                <p>Progress</p>
              </div>
              <div className="stat-card">
                <h3>{progressStats.totalConcepts}</h3>
                <p>Total Concepts</p>
              </div>
            </div>
            
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${progressStats.progressPercentage}%` }}
              ></div>
            </div>
          </div>

          <div className="progress-list">
            <h3>Learning History</h3>
            {progress.map(item => (
              <div key={item.id} className="progress-item">
                <div className="progress-concept">
                  <span className={`status-icon ${item.is_completed ? 'completed' : 'pending'}`}>
                    {item.is_completed ? '✓' : '○'}
                  </span>
                  <div className="concept-info">
                    <h4>{item.concept.name}</h4>
                    <p>{item.concept.short_description}</p>
                  </div>
                </div>
                
                {item.is_completed && item.completion_date && (
                  <div className="completion-info">
                    <span className="completion-date">
                      Completed: {new Date(item.completion_date).toLocaleDateString()}
                    </span>
                    {item.difficulty_rating && (
                      <div className="difficulty-rating">
                        Rating: {'★'.repeat(item.difficulty_rating)}{'☆'.repeat(5 - item.difficulty_rating)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'suggestions' && (
        <div className="suggestions-section">
          <h3>Recommended Learning Path</h3>
          <p>Based on your current level, here's what we recommend learning next:</p>
          
          <div className="suggestions-list">
            {suggestions?.suggestions.map((suggestion, index) => (
              <div key={index} className="suggestion-item">
                <div className="suggestion-number">{index + 1}</div>
                <div className="suggestion-content">
                  <p>{suggestion}</p>
                </div>
              </div>
            )) || (
              <div className="no-suggestions">
                <p>No learning path suggestions available at the moment.</p>
              </div>
            )}
          </div>
          
          {suggestions?.recommended_concepts && suggestions.recommended_concepts.length > 0 && (
            <div className="recommended-concepts">
              <h4>Recommended Concepts</h4>
              <div className="concepts-grid">
                {suggestions.recommended_concepts.map(concept => (
                  <div key={concept.id} className="concept-card">
                    <div className="concept-header">
                      <span className="concept-icon">
                        {getTypeIcon(concept.concept_type)}
                      </span>
                      <h3>{concept.name}</h3>
                      <span 
                        className="difficulty-badge"
                        style={{ backgroundColor: getDifficultyColor(concept.difficulty_level) }}
                      >
                        {concept.difficulty_level}
                      </span>
                    </div>
                    
                    <p className="concept-description">
                      {concept.short_description}
                    </p>
                    
                    <div className="concept-actions">
                      <button 
                        className="learn-button"
                        onClick={() => handleMarkCompleted(concept.id)}
                      >
                        Start Learning
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EducationalDashboard;