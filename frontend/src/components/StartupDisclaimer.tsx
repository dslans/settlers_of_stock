/**
 * Startup Disclaimer Component
 * 
 * Component that displays important disclaimers when users first access the application
 * or when required disclaimers haven't been acknowledged.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Alert,
  Checkbox,
  FormControlLabel,
  Divider,
  Paper
} from '@mui/material';
import {
  Warning as WarningIcon,
  Security as SecurityIcon,
  Gavel as GavelIcon
} from '@mui/icons-material';
import { disclaimerService } from '../services/disclaimer';

interface StartupDisclaimerProps {
  open: boolean;
  onAccept: () => void;
  userId?: string;
}

const StartupDisclaimer: React.FC<StartupDisclaimerProps> = ({
  open,
  onAccept,
  userId
}) => {
  const [acknowledgments, setAcknowledgments] = useState({
    investment_advice: false,
    risk_warning: false,
    ai_limitations: false,
    regulatory_compliance: false
  });
  const [allAcknowledged, setAllAcknowledged] = useState(false);

  useEffect(() => {
    const allChecked = Object.values(acknowledgments).every(Boolean);
    setAllAcknowledged(allChecked);
  }, [acknowledgments]);

  const handleAcknowledgmentChange = (key: string, checked: boolean) => {
    setAcknowledgments(prev => ({
      ...prev,
      [key]: checked
    }));
  };

  const handleAccept = () => {
    if (userId) {
      // Record all acknowledgments
      Object.entries(acknowledgments).forEach(([disclaimerId, acknowledged]) => {
        if (acknowledged) {
          disclaimerService.acknowledgeDisclaimer(userId, disclaimerId);
        }
      });
    }
    onAccept();
  };

  return (
    <Dialog
      open={open}
      maxWidth="md"
      fullWidth
      disableEscapeKeyDown
      PaperProps={{
        sx: { minHeight: '70vh' }
      }}
    >
      <DialogTitle sx={{ textAlign: 'center', pb: 1 }}>
        <SecurityIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
        <Typography variant="h5" component="div" gutterBottom>
          Welcome to Settlers of Stock
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Important Legal Notices and Disclaimers
        </Typography>
      </DialogTitle>

      <DialogContent dividers sx={{ px: 3 }}>
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            Before using this application, you must read and acknowledge the following important disclaimers.
            These notices are legally required and essential for your protection.
          </Typography>
        </Alert>

        <Box sx={{ mb: 3 }}>
          <Paper elevation={1} sx={{ p: 2, mb: 2, bgcolor: 'error.light' }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <WarningIcon sx={{ color: 'error.dark', mr: 1, mt: 0.5 }} />
              <Box>
                <Typography variant="h6" sx={{ color: 'error.dark', mb: 1 }}>
                  Investment Disclaimer
                </Typography>
                <Typography variant="body2" sx={{ color: 'error.dark' }}>
                  This application provides information and analysis for educational purposes only and does not 
                  constitute investment advice, financial advice, trading advice, or any other sort of advice. 
                  The information provided should not be relied upon as a substitute for extensive independent 
                  market research before making your investment decisions. All investments carry risk of loss, 
                  and you may lose some or all of your investment. Past performance does not guarantee future results.
                </Typography>
              </Box>
            </Box>
            <FormControlLabel
              control={
                <Checkbox
                  checked={acknowledgments.investment_advice}
                  onChange={(e) => handleAcknowledgmentChange('investment_advice', e.target.checked)}
                  color="error"
                />
              }
              label={
                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                  I understand this is not investment advice and I am responsible for my own investment decisions
                </Typography>
              }
            />
          </Paper>

          <Paper elevation={1} sx={{ p: 2, mb: 2, bgcolor: 'warning.light' }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <WarningIcon sx={{ color: 'warning.dark', mr: 1, mt: 0.5 }} />
              <Box>
                <Typography variant="h6" sx={{ color: 'warning.dark', mb: 1 }}>
                  Risk Warning
                </Typography>
                <Typography variant="body2" sx={{ color: 'warning.dark' }}>
                  Trading and investing in stocks, securities, and financial instruments involves substantial 
                  risk of loss and is not suitable for all investors. Stock prices can be extremely volatile 
                  and unpredictable. You should carefully consider your investment objectives, level of experience, 
                  and risk appetite before making any investment decisions. Never invest money you cannot afford to lose.
                </Typography>
              </Box>
            </Box>
            <FormControlLabel
              control={
                <Checkbox
                  checked={acknowledgments.risk_warning}
                  onChange={(e) => handleAcknowledgmentChange('risk_warning', e.target.checked)}
                  color="warning"
                />
              }
              label={
                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                  I understand the risks involved in stock trading and investing
                </Typography>
              }
            />
          </Paper>

          <Paper elevation={1} sx={{ p: 2, mb: 2, bgcolor: 'info.light' }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <SecurityIcon sx={{ color: 'info.dark', mr: 1, mt: 0.5 }} />
              <Box>
                <Typography variant="h6" sx={{ color: 'info.dark', mb: 1 }}>
                  AI Analysis Limitations
                </Typography>
                <Typography variant="body2" sx={{ color: 'info.dark' }}>
                  This application uses artificial intelligence and automated analysis tools. AI-generated 
                  content may contain errors, biases, or inaccuracies. The analysis is based on historical 
                  data and patterns, which may not predict future market behavior. Always conduct your own 
                  research and consult with qualified financial professionals before making investment decisions.
                </Typography>
              </Box>
            </Box>
            <FormControlLabel
              control={
                <Checkbox
                  checked={acknowledgments.ai_limitations}
                  onChange={(e) => handleAcknowledgmentChange('ai_limitations', e.target.checked)}
                  color="info"
                />
              }
              label={
                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                  I understand the limitations of AI-generated analysis and will verify information independently
                </Typography>
              }
            />
          </Paper>

          <Paper elevation={1} sx={{ p: 2, mb: 2, bgcolor: 'grey.100' }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
              <GavelIcon sx={{ color: 'text.primary', mr: 1, mt: 0.5 }} />
              <Box>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  Regulatory Notice
                </Typography>
                <Typography variant="body2">
                  This application is not registered as an investment advisor or broker-dealer. The information 
                  provided is not personalized investment advice. Users are responsible for complying with all 
                  applicable laws and regulations in their jurisdiction regarding investment activities. We do not 
                  act as a fiduciary and no fiduciary relationship is created by using this service.
                </Typography>
              </Box>
            </Box>
            <FormControlLabel
              control={
                <Checkbox
                  checked={acknowledgments.regulatory_compliance}
                  onChange={(e) => handleAcknowledgmentChange('regulatory_compliance', e.target.checked)}
                  color="primary"
                />
              }
              label={
                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                  I understand the regulatory limitations and my responsibilities
                </Typography>
              }
            />
          </Paper>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            By continuing, you also agree to our Terms of Use and Privacy Policy
          </Typography>
          <Typography variant="caption" color="text.secondary">
            You can review these documents at any time in the application settings
          </Typography>
        </Box>

        {!allAcknowledged && (
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              Please acknowledge all disclaimers above to continue using the application.
            </Typography>
          </Alert>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 3, justifyContent: 'center' }}>
        <Button
          onClick={handleAccept}
          variant="contained"
          size="large"
          disabled={!allAcknowledged}
          sx={{ minWidth: 200 }}
        >
          I Acknowledge and Accept
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default StartupDisclaimer;