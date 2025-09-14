import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ChatMessage from '../ChatMessage';
import { ChatMessage as ChatMessageType } from '../../types';

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('ChatMessage', () => {
  const mockUserMessage: ChatMessageType = {
    id: 'test-1',
    type: 'user',
    content: 'What is the analysis for AAPL?',
    timestamp: new Date('2024-01-01T12:00:00Z'),
  };

  const mockAssistantMessage: ChatMessageType = {
    id: 'test-2',
    type: 'assistant',
    content: 'Apple (AAPL) is showing strong fundamentals...',
    timestamp: new Date('2024-01-01T12:01:00Z'),
    metadata: {
      stockSymbol: 'AAPL',
      analysisType: 'fundamental',
    },
  };

  const mockSystemMessage: ChatMessageType = {
    id: 'test-3',
    type: 'system',
    content: 'Connection established',
    timestamp: new Date('2024-01-01T12:00:00Z'),
  };

  it('renders user message correctly', () => {
    renderWithTheme(<ChatMessage message={mockUserMessage} />);
    
    expect(screen.getByText('What is the analysis for AAPL?')).toBeInTheDocument();
    expect(screen.getByText(/\d{2}:\d{2} [AP]M/)).toBeInTheDocument();
  });

  it('renders assistant message correctly', () => {
    renderWithTheme(<ChatMessage message={mockAssistantMessage} />);
    
    expect(screen.getByText('Apple (AAPL) is showing strong fundamentals...')).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument(); // Stock symbol chip
    expect(screen.getByText(/\d{2}:\d{2} [AP]M/)).toBeInTheDocument();
  });

  it('renders system message correctly', () => {
    renderWithTheme(<ChatMessage message={mockSystemMessage} />);
    
    expect(screen.getByText('Connection established')).toBeInTheDocument();
    expect(screen.getByText(/\d{2}:\d{2} [AP]M/)).toBeInTheDocument();
  });

  it('displays stock symbol chip when metadata is present', () => {
    renderWithTheme(<ChatMessage message={mockAssistantMessage} />);
    
    const stockChip = screen.getByText('AAPL');
    expect(stockChip).toBeInTheDocument();
  });

  it('does not display stock symbol chip when metadata is not present', () => {
    renderWithTheme(<ChatMessage message={mockUserMessage} />);
    
    expect(screen.queryByText('AAPL')).not.toBeInTheDocument();
  });
});