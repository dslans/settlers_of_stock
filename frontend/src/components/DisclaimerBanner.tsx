/**
 * Disclaimer Banner Component
 * 
 * Compact banner component for displaying disclaimers inline with content
 * such as chat responses, analysis results, and recommendations.
 */

import React, { useState } from 'react';
import {
  Alert,
  AlertTitle,
  Collapse,
  IconButton,
  Typography,
  Box,
  Chip
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { disclaimerService, DisclaimerContext } from '../services/disclaimer';

interface DisclaimerBannerProps {
  context: DisclaimerContext;
  compact?: boolean;
  severity?: 'info' | 'warning' | 'error';
  riskLevel?: string;
  volatility?: number;
  symbol?: string;
  className?: string;
}

const DisclaimerBanner: React.FC<DisclaimerBannerProps> = ({
  context,
  compact = true,
  severity,
  riskLevel,
  volatility,
  symbol,
  className
}) => {
  const [expanded, setExpanded] = useState(false);

  const disclaimers = disclaimerService.getDisclaimersForContext(context);
  const shouldShowHighRisk = disclaimerService.shouldShowHighRiskDisclaimer(riskLevel, volatility);

  if (disclaimers.length === 0) {
    return null;
  }

  // Determine the most severe disclaimer level
  const maxSeverity = severity || disclaimers.reduce((max, disclaimer) => {
    const severityOrder = { info: 1, warning: 2, error: 3 };
    const currentLevel = severityOrder[disclaimer.severity];
    const maxLevel = severityOrder[max];
    return currentLevel > maxLevel ? disclaimer.severity : max;
  }, 'info' as 'info' | 'warning' | 'error');

  const getSeverityIcon = (sev: 'info' | 'warning' | 'error') => {
    switch (sev) {
      case 'error':
        return <ErrorIcon fontSize="small" />;
      case 'warning':
        return <WarningIcon fontSize="small" />;
      case 'info':
      default:
        return <InfoIcon fontSize="small" />;
    }
  };

  const getCompactText = () => {
    if (shouldShowHighRisk) {
      return `⚠️ High Risk ${symbol ? `(${symbol})` : ''}: This analysis is for informational purposes only and not investment advice. All investments carry risk of loss.`;
    }

    switch (context) {
      case 'recommendation':
        return '⚠️ Investment Disclaimer: This recommendation is for informational purposes only and not investment advice.';
      case 'backtest':
        return '⚠️ Backtesting Disclaimer: Past performance does not guarantee future results. Results are hypothetical.';
      case 'analysis_result':
        return '⚠️ Analysis Disclaimer: This analysis is for educational purposes only and not investment advice.';
      case 'chat_response':
        return '⚠️ Important: This information is for educational purposes only and not investment advice.';
      default:
        return '⚠️ Disclaimer: This information is for educational purposes only and not investment advice.';
    }
  };

  const getExpandedContent = () => {
    return disclaimers.map(disclaimer => (
      <Box key={disclaimer.id} sx={{ mb: 1 }}>
        <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
          {disclaimer.title}:
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {disclaimer.content}
        </Typography>
      </Box>
    ));
  };

  if (compact) {
    return (
      <Alert
        severity={maxSeverity}
        icon={getSeverityIcon(maxSeverity)}
        className={className}
        sx={{
          mt: 1,
          mb: 1,
          '& .MuiAlert-message': {
            width: '100%'
          }
        }}
        action={
          <IconButton
            aria-label="expand disclaimer"
            color="inherit"
            size="small"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        }
      >
        <Typography variant="body2">
          {getCompactText()}
        </Typography>
        
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
            {getExpandedContent()}
            
            {shouldShowHighRisk && (
              <Box sx={{ mt: 2 }}>
                <Chip
                  label="High Risk Investment"
                  color="error"
                  size="small"
                  icon={<WarningIcon />}
                />
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  This investment has been identified as high risk. Please exercise extreme caution
                  and consider consulting with a qualified financial advisor.
                </Typography>
              </Box>
            )}
          </Box>
        </Collapse>
      </Alert>
    );
  }

  // Full disclaimer display
  return (
    <Box className={className} sx={{ mt: 2, mb: 2 }}>
      <Alert severity={maxSeverity} icon={getSeverityIcon(maxSeverity)}>
        <AlertTitle>Important Disclaimers</AlertTitle>
        {getExpandedContent()}
        
        {shouldShowHighRisk && (
          <Box sx={{ mt: 2, p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'error.dark' }}>
              ⚠️ High Risk Warning {symbol && `(${symbol})`}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1, color: 'error.dark' }}>
              This investment has been identified as high risk due to high volatility or other risk factors.
              You may lose some or all of your investment. Only invest what you can afford to lose.
            </Typography>
          </Box>
        )}
      </Alert>
    </Box>
  );
};

export default DisclaimerBanner;