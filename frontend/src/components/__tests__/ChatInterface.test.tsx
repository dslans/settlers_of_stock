import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ChatInterface from '../ChatInterface';
import { ChatMessage } from '../../types';

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('ChatInterface', () => {
  const mockMessages: ChatMessage[] = [
    {
      id: 'test-1',
      type: 'user',
      content: 'Hello',
      timestamp: new Date('2024-01-01T12:00:00Z'),
    },
    {
      id: 'test-2',
      type: 'assistant',
      content: 'Hi there! How can I help you with stock analysis today?',
      timestamp: new Date('2024-01-01T12:01:00Z'),
    },
  ];

  const defaultProps = {
    messages: [],
    onSendMessage: jest.fn(),
    isLoading: false,
    voiceEnabled: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders empty state correctly', () => {
    renderWithTheme(<ChatInterface {...defaultProps} />);
    
    expect(screen.getByText('Welcome to Settlers of Stock!')).toBeInTheDocument();
    expect(screen.getByText(/Start by asking about a stock/)).toBeInTheDocument();
  });

  it('renders messages when provided', () => {
    renderWithTheme(<ChatInterface {...defaultProps} messages={mockMessages} />);
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there! How can I help you with stock analysis today?')).toBeInTheDocument();
  });

  it('calls onSendMessage when send button is clicked', async () => {
    const user = userEvent.setup();
    const mockOnSendMessage = jest.fn();
    
    renderWithTheme(
      <ChatInterface {...defaultProps} onSendMessage={mockOnSendMessage} />
    );
    
    const input = screen.getByPlaceholderText(/Ask about a stock/);
    const sendButton = screen.getByTestId('SendIcon').closest('button');
    
    await user.type(input, 'Test message');
    if (sendButton) {
      await user.click(sendButton);
    }
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message');
  });

  it('calls onSendMessage when Enter key is pressed', async () => {
    const user = userEvent.setup();
    const mockOnSendMessage = jest.fn();
    
    renderWithTheme(
      <ChatInterface {...defaultProps} onSendMessage={mockOnSendMessage} />
    );
    
    const input = screen.getByPlaceholderText(/Ask about a stock/);
    
    await user.type(input, 'Test message{enter}');
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message');
  });

  it('does not send empty messages', async () => {
    const mockOnSendMessage = jest.fn();
    
    renderWithTheme(
      <ChatInterface {...defaultProps} onSendMessage={mockOnSendMessage} />
    );
    
    const sendButton = screen.getByTestId('SendIcon').closest('button');
    
    // Button should be disabled when input is empty
    expect(sendButton).toBeDisabled();
    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  it('disables input and send button when loading', () => {
    renderWithTheme(<ChatInterface {...defaultProps} isLoading={true} />);
    
    const input = screen.getByPlaceholderText(/Processing your request/);
    const sendButton = screen.getByTestId('SendIcon').closest('button');
    
    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('shows loading indicator when isLoading is true', () => {
    renderWithTheme(
      <ChatInterface {...defaultProps} messages={mockMessages} isLoading={true} />
    );
    
    expect(screen.getByText('Analyzing market data...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('clears input after sending message', async () => {
    const user = userEvent.setup();
    const mockOnSendMessage = jest.fn();
    
    renderWithTheme(
      <ChatInterface {...defaultProps} onSendMessage={mockOnSendMessage} />
    );
    
    const input = screen.getByPlaceholderText(/Ask about a stock/) as HTMLInputElement;
    
    await user.type(input, 'Test message');
    expect(input.value).toBe('Test message');
    
    await user.keyboard('{enter}');
    
    await waitFor(() => {
      expect(input.value).toBe('');
    });
  });

  it('shows voice button when voice is enabled', () => {
    renderWithTheme(<ChatInterface {...defaultProps} voiceEnabled={true} />);
    
    expect(screen.getByTestId('MicIcon')).toBeInTheDocument();
  });

  it('does not show voice button when voice is disabled', () => {
    renderWithTheme(<ChatInterface {...defaultProps} voiceEnabled={false} />);
    
    expect(screen.queryByTestId('MicIcon')).not.toBeInTheDocument();
  });
});