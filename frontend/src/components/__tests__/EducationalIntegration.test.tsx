/**
 * Integration tests for educational features
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import EducationalDashboard from '../EducationalDashboard';
import EducationalTooltip from '../EducationalTooltip';
import { educationService } from '../../services/education';

// Mock the education service
jest.mock('../../services/education');
const mockEducationService = educationService as jest.Mocked<typeof educationService>;

// Mock the useEducation hook
jest.mock('../../hooks/useEducation', () => ({
  useEducation: () => ({
    concepts: [
      {
        id: 1,
        name: 'P/E Ratio',
        concept_type: 'fundamental_ratio',
        difficulty_level: 'beginner',
        short_description: 'Price-to-Earnings ratio measures stock valuation',
        detailed_explanation: 'The P/E ratio compares a company\'s current share price to its per-share earnings.',
        practical_example: 'If a stock trades at $50 and has earnings of $5 per share, the P/E ratio is 10.',
        formula: 'P/E = Stock Price / Earnings Per Share',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
    ],
    searchConcepts: jest.fn(),
    isLoadingConcepts: false,
    conceptsError: null,
    progress: [
      {
        id: 1,
        user_id: 1,
        concept_id: 1,
        concept: {
          id: 1,
          name: 'P/E Ratio',
          concept_type: 'fundamental_ratio',
          difficulty_level: 'beginner',
          short_description: 'Price-to-Earnings ratio measures stock valuation'
        },
        is_completed: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
    ],
    refreshProgress: jest.fn(),
    markCompleted: jest.fn(),
    isLoadingProgress: false,
    progressError: null,
    suggestions: {
      suggestions: [
        'Start with basic financial ratios like P/E and P/B',
        'Learn about technical indicators like RSI and MACD',
        'Understand market concepts like bull and bear markets'
      ],
      recommended_concepts: [],
      estimated_duration_minutes: 60
    },
    refreshSuggestions: jest.fn(),
    isLoadingSuggestions: false,
    suggestionsError: null,
    getContextualSuggestions: jest.fn(),
    getProgressStats: () => ({
      totalConcepts: 1,
      completedConcepts: 0,
      progressPercentage: 0,
      recentCompletions: []
    })
  })
}));

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('Educational Dashboard Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should display educational dashboard with concepts', async () => {
    renderWithTheme(<EducationalDashboard />);
    
    expect(screen.getByText('Financial Education Center')).toBeInTheDocument();
    expect(screen.getByText('Learn financial concepts to improve your investment knowledge')).toBeInTheDocument();
    expect(screen.getByText('P/E Ratio')).toBeInTheDocument();
    expect(screen.getByText('Price-to-Earnings ratio measures stock valuation')).toBeInTheDocument();
  });

  test('should show progress statistics', async () => {
    renderWithTheme(<EducationalDashboard />);
    
    // Click on progress tab
    const progressTab = screen.getByText('My Progress');
    fireEvent.click(progressTab);
    
    await waitFor(() => {
      expect(screen.getByText('Concepts Learned')).toBeInTheDocument();
      expect(screen.getByText('Progress')).toBeInTheDocument();
      expect(screen.getByText('Total Concepts')).toBeInTheDocument();
    });
  });

  test('should show learning path suggestions', async () => {
    renderWithTheme(<EducationalDashboard />);
    
    // Click on learning path tab
    const learningPathTab = screen.getByText('Learning Path');
    fireEvent.click(learningPathTab);
    
    await waitFor(() => {
      expect(screen.getByText('Recommended Learning Path')).toBeInTheDocument();
      expect(screen.getByText('Start with basic financial ratios like P/E and P/B')).toBeInTheDocument();
    });
  });

  test('should search concepts with filters', async () => {
    renderWithTheme(<EducationalDashboard />);
    
    const searchInput = screen.getByPlaceholderText('Search concepts...');
    fireEvent.change(searchInput, { target: { value: 'P/E' } });
    
    // The search should be triggered by the useEffect in the component
    expect(screen.getByDisplayValue('P/E')).toBeInTheDocument();
  });
});

describe('Educational Tooltips Integration', () => {
  beforeEach(() => {
    mockEducationService.explainConcept.mockResolvedValue({
      concept: {
        id: 1,
        name: 'P/E Ratio',
        concept_type: 'fundamental_ratio',
        difficulty_level: 'beginner',
        short_description: 'Price-to-Earnings ratio measures stock valuation',
        detailed_explanation: 'The P/E ratio compares a company\'s current share price to its per-share earnings.',
        practical_example: 'If a stock trades at $50 and has earnings of $5 per share, the P/E ratio is 10.',
        formula: 'P/E = Stock Price / Earnings Per Share',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      },
      contextual_explanation: 'In the context of stock analysis, P/E ratio helps determine if a stock is overvalued or undervalued.',
      related_suggestions: [],
      next_learning_steps: ['Learn about P/B ratio', 'Understand ROE']
    });
  });

  test('should render educational tooltip component', () => {
    renderWithTheme(
      <EducationalTooltip concept="P/E Ratio">
        <span>P/E Ratio</span>
      </EducationalTooltip>
    );
    
    expect(screen.getByText('P/E Ratio')).toBeInTheDocument();
    expect(screen.getByText('?')).toBeInTheDocument();
  });

  test('should show tooltip content on hover', async () => {
    renderWithTheme(
      <EducationalTooltip concept="P/E Ratio">
        <span>P/E Ratio</span>
      </EducationalTooltip>
    );
    
    const trigger = screen.getByText('P/E Ratio');
    fireEvent.mouseEnter(trigger);
    
    await waitFor(() => {
      expect(screen.getByText('Loading explanation...')).toBeInTheDocument();
    });
  });
});