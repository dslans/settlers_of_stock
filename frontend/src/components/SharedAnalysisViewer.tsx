import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Alert,
  CircularProgress,
  Chip,
  Divider,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  LinearProgress,
  useTheme,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Visibility as VisibilityIcon,
  Schedule as ScheduleIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import DisclaimerBanner from './DisclaimerBanner';
import { getSharedAnalysis, SharedAnalysis } from '../services/export';

interface SharedAnalysisViewerProps {
  linkId: string;
}

const SharedAnalysisViewer: React.FC<SharedAnalysisViewerProps> = ({ linkId }) => {
  const theme = useTheme();
  const [sharedData, setSharedData] = useState<SharedAnalysis | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSharedAnalysis = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getSharedAnalysis(linkId);
        setSharedData(data);
      } catch (error: any) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    if (linkId) {
      loadSharedAnalysis();
    }
  }, [linkId]);

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation?.toUpperCase()) {
      case 'STRONG_BUY':
      case 'BUY':
        return theme.palette.success.main;
      case 'HOLD':
        return theme.palette.warning.main;
      case 'SELL':
      case 'STRONG_SELL':
        return theme.palette.error.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  const getRecommendationIcon = (recommendation: string) => {
    switch (recommendation?.toUpperCase()) {
      case 'STRONG_BUY':
      case 'BUY':
        return <TrendingUpIcon />;
      case 'HOLD':
        return <TrendingFlatIcon />;
      case 'SELL':
      case 'STRONG_SELL':
        return <TrendingDownIcon />;
      default:
        return <AssessmentIcon />;
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel?.toUpperCase()) {
      case 'LOW':
        return theme.palette.success.main;
      case 'MODERATE':
        return theme.palette.warning.main;
      case 'HIGH':
      case 'VERY_HIGH':
        return theme.palette.error.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  const formatSentimentScore = (score: number): string => {
    if (score >= 0.5) return 'Very Positive';
    if (score >= 0.2) return 'Positive';
    if (score >= -0.2) return 'Neutral';
    if (score >= -0.5) return 'Negative';
    return 'Very Negative';
  };

  const getSentimentColor = (score: number) => {
    if (score >= 0.2) return theme.palette.success.main;
    if (score >= -0.2) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          <Typography variant="h6" gutterBottom>
            Unable to Load Shared Analysis
          </Typography>
          <Typography variant="body2">
            {error}
          </Typography>
        </Alert>
      </Box>
    );
  }

  if (!sharedData) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">
          <Typography variant="h6" gutterBottom>
            No Analysis Found
          </Typography>
          <Typography variant="body2">
            The shared analysis could not be found or may have expired.
          </Typography>
        </Alert>
      </Box>
    );
  }

  const { analysis, sentiment } = sharedData;

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: theme.palette.primary.main, color: 'white' }}>
        <Typography variant="h4" gutterBottom>
          {analysis.symbol} Stock Analysis
        </Typography>
        <Typography variant="body1" sx={{ opacity: 0.9 }}>
          Shared analysis report generated on {new Date(analysis.analysis_timestamp).toLocaleString()}
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
          <Chip
            icon={<VisibilityIcon />}
            label={`${sharedData.view_count} views`}
            variant="outlined"
            sx={{ color: 'white', borderColor: 'white' }}
          />
          <Chip
            icon={<ScheduleIcon />}
            label={`Expires: ${new Date(sharedData.expires_at).toLocaleDateString()}`}
            variant="outlined"
            sx={{ color: 'white', borderColor: 'white' }}
          />
        </Box>
      </Paper>

      {/* Executive Summary */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Executive Summary
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {getRecommendationIcon(analysis.recommendation)}
                  <Typography variant="h6" sx={{ ml: 1, color: getRecommendationColor(analysis.recommendation) }}>
                    {analysis.recommendation?.replace('_', ' ')}
                  </Typography>
                </Box>
                
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Confidence Level
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={analysis.confidence}
                    sx={{ flexGrow: 1, mr: 2, height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="body2" fontWeight="bold">
                    {analysis.confidence}%
                  </Typography>
                </Box>
                
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Overall Score
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <LinearProgress
                    variant="determinate"
                    value={analysis.overall_score}
                    sx={{ flexGrow: 1, mr: 2, height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="body2" fontWeight="bold">
                    {analysis.overall_score}/100
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Assessment
                </Typography>
                
                <Chip
                  label={analysis.risk_level?.replace('_', ' ')}
                  sx={{
                    bgcolor: getRiskLevelColor(analysis.risk_level),
                    color: 'white',
                    mb: 2
                  }}
                />
                
                {analysis.fundamental_score && (
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Fundamental Score: {analysis.fundamental_score}/100
                    </Typography>
                  </Box>
                )}
                
                {analysis.technical_score && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Technical Score: {analysis.technical_score}/100
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Price Targets */}
      {analysis.price_targets && analysis.price_targets.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Price Targets
          </Typography>
          
          <Grid container spacing={2}>
            {analysis.price_targets.map((target: any, index: number) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" color="primary" gutterBottom>
                      {target.timeframe}
                    </Typography>
                    <Typography variant="h4" gutterBottom>
                      ${target.target}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Confidence: {target.confidence}%
                    </Typography>
                    <Typography variant="body2">
                      {target.rationale}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Analysis Details */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Strengths */}
        {analysis.strengths && analysis.strengths.length > 0 && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom color="success.main">
                Key Strengths
              </Typography>
              <List dense>
                {analysis.strengths.map((strength: string, index: number) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <CheckCircleIcon color="success" />
                    </ListItemIcon>
                    <ListItemText primary={strength} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        )}

        {/* Weaknesses */}
        {analysis.weaknesses && analysis.weaknesses.length > 0 && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom color="warning.main">
                Key Weaknesses
              </Typography>
              <List dense>
                {analysis.weaknesses.map((weakness: string, index: number) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <WarningIcon color="warning" />
                    </ListItemIcon>
                    <ListItemText primary={weakness} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        )}

        {/* Risks */}
        {analysis.risks && analysis.risks.length > 0 && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom color="error.main">
                Risk Factors
              </Typography>
              <List dense>
                {analysis.risks.map((risk: string, index: number) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <ErrorIcon color="error" />
                    </ListItemIcon>
                    <ListItemText primary={risk} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        )}

        {/* Opportunities */}
        {analysis.opportunities && analysis.opportunities.length > 0 && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom color="info.main">
                Opportunities
              </Typography>
              <List dense>
                {analysis.opportunities.map((opportunity: string, index: number) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <TrendingUpIcon color="info" />
                    </ListItemIcon>
                    <ListItemText primary={opportunity} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        )}
      </Grid>

      {/* Sentiment Analysis */}
      {sentiment && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Sentiment Analysis
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h6" gutterBottom>
                    Overall Sentiment
                  </Typography>
                  <Typography
                    variant="h4"
                    sx={{ color: getSentimentColor(sentiment.sentiment_data.overall_sentiment) }}
                    gutterBottom
                  >
                    {formatSentimentScore(sentiment.sentiment_data.overall_sentiment)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Score: {sentiment.sentiment_data.overall_sentiment?.toFixed(2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h6" gutterBottom>
                    News Sentiment
                  </Typography>
                  <Typography
                    variant="h4"
                    sx={{ color: getSentimentColor(sentiment.sentiment_data.news_sentiment) }}
                    gutterBottom
                  >
                    {formatSentimentScore(sentiment.sentiment_data.news_sentiment)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Score: {sentiment.sentiment_data.news_sentiment?.toFixed(2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h6" gutterBottom>
                    Social Sentiment
                  </Typography>
                  <Typography
                    variant="h4"
                    sx={{ color: getSentimentColor(sentiment.sentiment_data.social_sentiment) }}
                    gutterBottom
                  >
                    {formatSentimentScore(sentiment.sentiment_data.social_sentiment)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Score: {sentiment.sentiment_data.social_sentiment?.toFixed(2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Disclaimer */}
      <DisclaimerBanner
        context="shared_analysis"
        compact={false}
        symbol={sharedData?.symbol}
      />
    </Box>
  );
};

export default SharedAnalysisViewer;