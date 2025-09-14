import React, { useState } from 'react';
import { Container, Typography, Box, Paper, Tabs, Tab } from '@mui/material';
import { ChatInterface } from './components';
import { AlertManager } from './components/AlertManager';
import EducationalDashboard from './components/EducationalDashboard';
import StartupDisclaimer from './components/StartupDisclaimer';
import { useChat } from './hooks/useChat';
import { useDisclaimer } from './hooks/useDisclaimer';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState(0);
  const { 
    messages, 
    isLoading, 
    sendMessage, 
    currentStockData,
    connected,
    connecting,
    connectionError
  } = useChat();
  
  // For demo purposes, using a mock user ID. In production, this would come from authentication
  const mockUserId = 'demo-user-123';
  const { 
    showStartupDisclaimer, 
    handleStartupAccept 
  } = useDisclaimer({ userId: mockUserId });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleNavigate = (destination: string) => {
    const tabMap: Record<string, number> = {
      'chat': 0,
      'alerts': 1,
      'education': 2,
      'watchlist': 1, // Map to alerts for now since we don't have a separate watchlist tab
    };
    
    const tabIndex = tabMap[destination];
    if (tabIndex !== undefined) {
      setActiveTab(tabIndex);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Settlers of Stock
        </Typography>
        <Typography variant="subtitle1" component="h2" gutterBottom align="center" color="text.secondary">
          Conversational Stock Research Application
        </Typography>
      </Box>
      
      <Paper elevation={3} sx={{ borderRadius: 3, overflow: 'hidden' }}>
        <Tabs value={activeTab} onChange={handleTabChange} centered>
          <Tab label="Chat" />
          <Tab label="Alerts" />
          <Tab label="Education" />
        </Tabs>
        
        <Box sx={{ p: 0 }}>
          {activeTab === 0 && (
            <ChatInterface
              messages={messages}
              onSendMessage={sendMessage}
              isLoading={isLoading}
              voiceEnabled={true} // Now enabled with full voice functionality
              currentStockData={currentStockData}
              connected={connected}
              connecting={connecting}
              connectionError={connectionError}
              onNavigate={handleNavigate}
            />
          )}
          
          {activeTab === 1 && (
            <AlertManager />
          )}
          
          {activeTab === 2 && (
            <EducationalDashboard />
          )}
        </Box>
      </Paper>
      
      {/* Startup Disclaimer Modal */}
      <StartupDisclaimer
        open={showStartupDisclaimer}
        onAccept={handleStartupAccept}
        userId={mockUserId}
      />
    </Container>
  );
}

export default App;