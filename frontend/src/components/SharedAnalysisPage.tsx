import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Home as HomeIcon,
} from '@mui/icons-material';
import SharedAnalysisViewer from './SharedAnalysisViewer';

const SharedAnalysisPage: React.FC = () => {
  const { linkId } = useParams<{ linkId: string }>();
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/');
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  if (!linkId) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Typography variant="h4" gutterBottom>
          Invalid Share Link
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          The shared analysis link is invalid or malformed.
        </Typography>
        <Button variant="contained" onClick={handleGoHome} startIcon={<HomeIcon />}>
          Go to Home
        </Button>
      </Container>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={handleGoBack}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Shared Stock Analysis
          </Typography>
          
          <Button
            color="inherit"
            onClick={handleGoHome}
            startIcon={<HomeIcon />}
          >
            Home
          </Button>
        </Toolbar>
      </AppBar>

      {/* Content */}
      <Container maxWidth="lg" sx={{ py: 0 }}>
        <SharedAnalysisViewer linkId={linkId} />
      </Container>
    </Box>
  );
};

export default SharedAnalysisPage;