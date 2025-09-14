/**
 * Disclaimer Modal Component
 * 
 * Modal component for displaying disclaimers, terms of use, and privacy policy
 * with user acknowledgment functionality.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Checkbox,
  FormControlLabel,
  Box,
  Tabs,
  Tab,
  Alert,
  Divider,
  IconButton
} from '@mui/material';
import {
  Close as CloseIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { disclaimerService, DisclaimerConfig, DisclaimerContext } from '../services/disclaimer';

interface DisclaimerModalProps {
  open: boolean;
  onClose: () => void;
  context?: DisclaimerContext;
  userId?: string;
  required?: boolean;
  onAcknowledge?: () => void;
  showTermsAndPrivacy?: boolean;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`disclaimer-tabpanel-${index}`}
      aria-labelledby={`disclaimer-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const DisclaimerModal: React.FC<DisclaimerModalProps> = ({
  open,
  onClose,
  context,
  userId,
  required = false,
  onAcknowledge,
  showTermsAndPrivacy = false
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [acknowledgments, setAcknowledgments] = useState<{ [key: string]: boolean }>({});
  const [allAcknowledged, setAllAcknowledged] = useState(false);

  const disclaimers = context 
    ? disclaimerService.getDisclaimersForContext(context)
    : disclaimerService.getAllDisclaimers();

  const requiredDisclaimers = disclaimers.filter(d => d.required);

  useEffect(() => {
    // Load existing acknowledgments if userId is provided
    if (userId) {
      disclaimerService.loadUserAcknowledgments(userId);
      
      // Check which disclaimers are already acknowledged
      const initialAcknowledgments: { [key: string]: boolean } = {};
      disclaimers.forEach(disclaimer => {
        const isAcknowledged = disclaimerService.hasUserAcknowledgedContext(userId, context || 'app_startup');
        initialAcknowledgments[disclaimer.id] = isAcknowledged;
      });
      setAcknowledgments(initialAcknowledgments);
    }
  }, [userId, context, disclaimers]);

  useEffect(() => {
    // Check if all required disclaimers are acknowledged
    const allRequired = requiredDisclaimers.every(disclaimer => 
      acknowledgments[disclaimer.id] === true
    );
    setAllAcknowledged(allRequired);
  }, [acknowledgments, requiredDisclaimers]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleAcknowledgmentChange = (disclaimerId: string, checked: boolean) => {
    setAcknowledgments(prev => ({
      ...prev,
      [disclaimerId]: checked
    }));
  };

  const handleAccept = () => {
    if (userId) {
      // Record acknowledgments
      Object.entries(acknowledgments).forEach(([disclaimerId, acknowledged]) => {
        if (acknowledged) {
          disclaimerService.acknowledgeDisclaimer(userId, disclaimerId);
        }
      });
    }

    if (onAcknowledge) {
      onAcknowledge();
    }

    onClose();
  };

  const handleClose = () => {
    if (required && !allAcknowledged) {
      // Don't allow closing if required disclaimers aren't acknowledged
      return;
    }
    onClose();
  };

  const getSeverityIcon = (severity: 'info' | 'warning' | 'error') => {
    switch (severity) {
      case 'error':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'info':
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getSeverityColor = (severity: 'info' | 'warning' | 'error') => {
    switch (severity) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
      default:
        return 'info';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '60vh', maxHeight: '90vh' }
      }}
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">
          {required ? 'Important Legal Notices' : 'Disclaimers and Legal Information'}
        </Typography>
        {!required && (
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        )}
      </DialogTitle>

      <DialogContent dividers>
        {showTermsAndPrivacy ? (
          <>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="disclaimer tabs">
              <Tab label="Disclaimers" />
              <Tab label="Terms of Use" />
              <Tab label="Privacy Policy" />
            </Tabs>

            <TabPanel value={tabValue} index={0}>
              {disclaimers.map((disclaimer, index) => (
                <Box key={disclaimer.id} sx={{ mb: 3 }}>
                  <Alert 
                    severity={getSeverityColor(disclaimer.severity)}
                    icon={getSeverityIcon(disclaimer.severity)}
                    sx={{ mb: 2 }}
                  >
                    <Typography variant="h6" gutterBottom>
                      {disclaimer.title}
                    </Typography>
                    <Typography variant="body2">
                      {disclaimer.content}
                    </Typography>
                  </Alert>

                  {userId && (
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={acknowledgments[disclaimer.id] || false}
                          onChange={(e) => handleAcknowledgmentChange(disclaimer.id, e.target.checked)}
                          color="primary"
                        />
                      }
                      label={
                        disclaimer.required 
                          ? `I acknowledge and understand this ${disclaimer.title.toLowerCase()} (Required)`
                          : `I acknowledge this ${disclaimer.title.toLowerCase()}`
                      }
                      sx={{ 
                        mt: 1,
                        '& .MuiFormControlLabel-label': {
                          fontSize: '0.875rem',
                          fontWeight: disclaimer.required ? 'bold' : 'normal'
                        }
                      }}
                    />
                  )}

                  {index < disclaimers.length - 1 && <Divider sx={{ mt: 2 }} />}
                </Box>
              ))}
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <Typography variant="body2" component="div" sx={{ whiteSpace: 'pre-line' }}>
                {disclaimerService.getTermsOfUse()}
              </Typography>
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <Typography variant="body2" component="div" sx={{ whiteSpace: 'pre-line' }}>
                {disclaimerService.getPrivacyPolicy()}
              </Typography>
            </TabPanel>
          </>
        ) : (
          <Box>
            {disclaimers.map((disclaimer, index) => (
              <Box key={disclaimer.id} sx={{ mb: 3 }}>
                <Alert 
                  severity={getSeverityColor(disclaimer.severity)}
                  icon={getSeverityIcon(disclaimer.severity)}
                  sx={{ mb: 2 }}
                >
                  <Typography variant="h6" gutterBottom>
                    {disclaimer.title}
                  </Typography>
                  <Typography variant="body2">
                    {disclaimer.content}
                  </Typography>
                </Alert>

                {userId && (
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={acknowledgments[disclaimer.id] || false}
                        onChange={(e) => handleAcknowledgmentChange(disclaimer.id, e.target.checked)}
                        color="primary"
                      />
                    }
                    label={
                      disclaimer.required 
                        ? `I acknowledge and understand this ${disclaimer.title.toLowerCase()} (Required)`
                        : `I acknowledge this ${disclaimer.title.toLowerCase()}`
                    }
                    sx={{ 
                      mt: 1,
                      '& .MuiFormControlLabel-label': {
                        fontSize: '0.875rem',
                        fontWeight: disclaimer.required ? 'bold' : 'normal'
                      }
                    }}
                  />
                )}

                {index < disclaimers.length - 1 && <Divider sx={{ mt: 2 }} />}
              </Box>
            ))}
          </Box>
        )}

        {required && !allAcknowledged && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body2">
              You must acknowledge all required disclaimers before continuing.
            </Typography>
          </Alert>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        {!required && (
          <Button onClick={handleClose} color="secondary">
            Close
          </Button>
        )}
        <Button
          onClick={handleAccept}
          variant="contained"
          color="primary"
          disabled={required && !allAcknowledged}
        >
          {required ? 'Accept and Continue' : 'Acknowledge'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DisclaimerModal;