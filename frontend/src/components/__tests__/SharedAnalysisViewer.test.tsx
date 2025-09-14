import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import SharedAnalysisViewer from '../SharedAnalysisViewer';
import * as exportService from '../../services/export';

// Mock the export service
jest.mock('../../services/export');

const mockExportService = exportService as jest.Mocked<typeof exportService>;

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('SharedAnalysisViewer', () => {
  const mockSharedData = {
    analysis: {
      symbol: 'AAPL',
      analysis_type: 'combined',
      recommendation: 'BUY',
      confidence: 78,
      overall_score: 75,
      fundamental_score: 80,
      technical_score: 70,
      strengths: [
        'Strong financial position with low debt',
        'Consistent revenue growth',
        'Technical indicators showing bullish momentum'
      ],
      weaknesses: [
        'High valuation compared to peers',
        'Dependence on iPhone sales'
      ],
      risks: [
        'Market volatility',
        'Regulatory challenges',
        'Supply chain disruptions'
      ],
      opportunities: [
        'Services revenue growth',
        'Expansion in emerging markets',
        'New product categories'
      ],
      price_targets: [
        {
          target: 165.00,
          timeframe: '3M',
          confidence: 75,
          rationale: 'Based on P/E expansion and earnings growth'
        },
        {
          target: 180.00,
          timeframe: '1Y',
          confidence: 65,
          rationale: 'Long-term growth trajectory and market expansion'
        }
      ],
      risk_level: 'MODERATE',
      risk_factors: {
        volatility: 0.25,
        beta: 1.2,
        debt_ratio: 0.3
      },
      analysis_timestamp: '2024-01-15T15:30:00Z'
    },
    sentiment: {
      symbol: 'AAPL',
      sentiment_data: {
        overall_sentiment: 0.6,
        news_sentiment: 0.5,
        social_sentiment: 0.7,
        trend_direction: 'IMPROVING',
        trend_strength: 0.8,
        confidence_score: 0.75,
        data_freshness: '2024-01-15T15:30:00Z',
        news_articles_count: 25,
        social_posts_count: 150,
        volatility: 0.25
      },
      sentiment_alerts: [],
      recent_news: [],
      analysis_timestamp: '2024-01-15T15:30:00Z'
    },
    created_at: '2024-01-15T15:30:00Z',
    view_count: 5,
    expires_at: '2024-01-16T15:30:00Z'
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    mockExportService.getSharedAnalysis.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders shared analysis data correctly', async () => {
    mockExportService.getSharedAnalysis.mockResolvedValue(mockSharedData);
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    await waitFor(() => {
      expect(screen.getByText('AAPL Stock Analysis')).toBeInTheDocument();
    });
    
    // Check header information
    expect(screen.getByText(/Shared analysis report generated on/)).toBeInTheDocument();
    expect(screen.getByText('5 views')).toBeInTheDocument();
    expect(screen.getByText(/Expires:/)).toBeInTheDocument();
    
    // Check executive summary
    expect(screen.getByText('Executive Summary')).toBeInTheDocument();
    expect(screen.getByText('BUY')).toBeInTheDocument();
    expect(screen.getByText('78%')).toBeInTheDocument();
    expect(screen.getByText('75/100')).toBeInTheDocument();
    expect(screen.getByText('MODERATE')).toBeInTheDocument();
  });

  it('renders price targets', async () => {
    mockExportService.getSharedAnalysis.mockResolvedValue(mockSharedData);
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    await waitFor(() => {
      expect(screen.getByText('Price Targets')).toBeInTheDocument();
    });
    
    expect(screen.getByText('3M')).toBeInTheDocument();
    expect(screen.getByText('$165')).toBeInTheDocument();
    expect(screen.getByText('1Y')).toBeInTheDocument();
    expect(screen.getByText('$180')).toBeInTheDocument();
  });

  it('renders analysis details', async () => {
    mockExportService.getSharedAnalysis.mockResolvedValue(mockSharedData);
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    await waitFor(() => {
      expect(screen.getByText('Key Strengths')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Strong financial position with low debt')).toBeInTheDocument();
    expect(screen.getByText('Key Weaknesses')).toBeInTheDocument();
    expect(screen.getByText('High valuation compared to peers')).toBeInTheDocument();
    expect(screen.getByText('Risk Factors')).toBeInTheDocument();
    expect(screen.getByText('Market volatility')).toBeInTheDocument();
    expect(screen.getByText('Opportunities')).toBeInTheDocument();
    expect(screen.getByText('Services revenue growth')).toBeInTheDocument();
  });

  it('renders sentiment analysis', async () => {
    mockExportService.getSharedAnalysis.mockResolvedValue(mockSharedData);
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    await waitFor(() => {
      expect(screen.getByText('Sentiment Analysis')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Overall Sentiment')).toBeInTheDocument();
    expect(screen.getByText('Positive')).toBeInTheDocument(); // 0.6 should be "Positive"
    expect(screen.getByText('News Sentiment')).toBeInTheDocument();
    expect(screen.getByText('Social Sentiment')).toBeInTheDocument();
  });

  it('renders disclaimers', async () => {
    mockExportService.getSharedAnalysis.mockResolvedValue(mockSharedData);
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    await waitFor(() => {
      expect(screen.getByText('Important Disclaimers')).toBeInTheDocument();
    });
    
    expect(screen.getByText(/Investment Disclaimer:/)).toBeInTheDocument();
    expect(screen.getByText(/Data Sources:/)).toBeInTheDocument();
    expect(screen.getByText(/Risk Warning:/)).toBeInTheDocument();
  });

  it('handles analysis without sentiment data', async () => {
    const dataWithoutSentiment = {
      ...mockSharedData,
      sentiment: null
    };
    
    mockExportService.getSharedAnalysis.mockResolvedValue(dataWithoutSentiment);
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    await waitFor(() => {
      expect(screen.getByText('AAPL Stock Analysis')).toBeInTheDocument();
    });
    
    // Sentiment section should not be present
    expect(screen.queryByText('Sentiment Analysis')).not.toBeInTheDocument();
  });

  it('handles analysis without price targets', async () => {
    const dataWithoutTargets = {
      ...mockSharedData,
      analysis: {
        ...mockSharedData.analysis,
        price_targets: []
      }
    };
    
    mockExportService.getSharedAnalysis.mockResolvedValue(dataWithoutTargets);
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    await waitFor(() => {
      expect(screen.getByText('AAPL Stock Analysis')).toBeInTheDocument();
    });
    
    // Price targets section should not be present
    expect(screen.queryByText('Price Targets')).not.toBeInTheDocument();
  });

  it('displays error when shared analysis not found', async () => {
    mockExportService.getSharedAnalysis.mockRejectedValue(new Error('Shared link not found or expired'));
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    await waitFor(() => {
      expect(screen.getByText('Unable to Load Shared Analysis')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Shared link not found or expired')).toBeInTheDocument();
  });

  it('displays warning when no analysis data returned', async () => {
    mockExportService.getSharedAnalysis.mockResolvedValue(null);
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    await waitFor(() => {
      expect(screen.getByText('No Analysis Found')).toBeInTheDocument();
    });
    
    expect(screen.getByText('The shared analysis could not be found or may have expired.')).toBeInTheDocument();
  });

  it('calls getSharedAnalysis with correct link ID', async () => {
    mockExportService.getSharedAnalysis.mockResolvedValue(mockSharedData);
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    await waitFor(() => {
      expect(mockExportService.getSharedAnalysis).toHaveBeenCalledWith('test-link-id');
    });
  });

  it('formats sentiment scores correctly', async () => {
    const dataWithDifferentSentiments = {
      ...mockSharedData,
      sentiment: {
        ...mockSharedData.sentiment,
        sentiment_data: {
          ...mockSharedData.sentiment.sentiment_data,
          overall_sentiment: 0.8,  // Should be "Very Positive"
          news_sentiment: -0.3,    // Should be "Negative"
          social_sentiment: 0.1    // Should be "Neutral"
        }
      }
    };
    
    mockExportService.getSharedAnalysis.mockResolvedValue(dataWithDifferentSentiments);
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    await waitFor(() => {
      expect(screen.getByText('Very Positive')).toBeInTheDocument();
      expect(screen.getByText('Negative')).toBeInTheDocument();
      expect(screen.getByText('Neutral')).toBeInTheDocument();
    });
  });

  it('handles different recommendation types', async () => {
    const dataWithSellRecommendation = {
      ...mockSharedData,
      analysis: {
        ...mockSharedData.analysis,
        recommendation: 'STRONG_SELL',
        risk_level: 'HIGH'
      }
    };
    
    mockExportService.getSharedAnalysis.mockResolvedValue(dataWithSellRecommendation);
    
    renderWithTheme(<SharedAnalysisViewer linkId="test-link-id" />);
    
    await waitFor(() => {
      expect(screen.getByText('STRONG SELL')).toBeInTheDocument();
      expect(screen.getByText('HIGH')).toBeInTheDocument();
    });
  });
});