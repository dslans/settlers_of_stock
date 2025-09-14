import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChatInterface from '../ChatInterface';
import { ChatMessage } from '../../types';

// Mock the voice hook
jest.mock('../../hooks/useVoice', () => ({
  useVoice: jest.fn(() => ({
    isListening: false,
    isSupported: true,
    transcript: '',
    confidence: 0,
    error: null,
    startListening: jest.fn(),
    stopListening: jest.fn(),
    speak: jest.fn(),
    isSpeaking: false,
    stopSpeaking: jest.fn(),
    voices: [
      {
        name: 'Test Voice',
        lang: 'en-US',
        default: true,
        localService: true,
        voiceURI: 'test-voice',
      },
    ],
    selectedVoice: {
      name: 'Test Voice',
      lang: 'en-US',
      default: true,
      localService: true,
      voiceURI: 'test-voice',
    },
    setSelectedVoice: jest.fn(),
  })),
}));

// Mock voice commands
jest.mock('../../services/voiceCommands', () => ({
  voiceCommandProcessor: {
    processCommand: jest.fn(() => ({
      type: 'stock_query',
      intent: 'analyze_stock',
      parameters: { symbol: 'AAPL', action: 'analyze' },
      confidence: 1,
      originalText: 'analyze Apple',
    })),
    convertToMessage: jest.fn(() => 'Analyze AAPL'),
    getHelpText: jest.fn(() => 'Voice commands help text'),
  },
}));

const mockMessages: ChatMessage[] = [
  {
    id: '1',
    type: 'user',
    content: 'Hello',
    timestamp: new Date(),
  },
  {
    id: '2',
    type: 'assistant',
    content: 'Hello! How can I help you with stock analysis today?',
    timestamp: new Date(),
  },
];

const defaultProps = {
  messages: mockMessages,
  onSendMessage: jest.fn(),
  isLoading: false,
  voiceEnabled: true,
  currentStockData: null,
  connected: true,
  connecting: false,
  connectionError: null,
  onNavigate: jest.fn(),
};

describe('ChatInterface Voice Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should show voice controls when voice is enabled', () => {
    render(<ChatInterface {...defaultProps} />);
    
    // Should show microphone button
    expect(screen.getByRole('button', { name: /start voice input/i })).toBeInTheDocument();
    
    // Should show voice settings button
    expect(screen.getByRole('button', { name: /voice settings/i })).toBeInTheDocument();
    
    // Should show speak button
    expect(screen.getByRole('button', { name: /speak last response/i })).toBeInTheDocument();
  });

  it('should not show voice controls when voice is disabled', () => {
    render(<ChatInterface {...defaultProps} voiceEnabled={false} />);
    
    expect(screen.queryByRole('button', { name: /start voice input/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /voice settings/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /speak last response/i })).not.toBeInTheDocument();
  });

  it('should show appropriate placeholder text when voice is enabled', () => {
    render(<ChatInterface {...defaultProps} />);
    
    const input = screen.getByPlaceholderText(/Ask about a stock or use voice input/);
    expect(input).toBeInTheDocument();
  });

  it('should call startListening when microphone button is clicked', async () => {
    const { useVoice } = require('../../hooks/useVoice');
    const mockStartListening = jest.fn();
    
    useVoice.mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      confidence: 0,
      error: null,
      startListening: mockStartListening,
      stopListening: jest.fn(),
      speak: jest.fn(),
      isSpeaking: false,
      stopSpeaking: jest.fn(),
      voices: [],
      selectedVoice: null,
      setSelectedVoice: jest.fn(),
    });

    const user = userEvent.setup();
    render(<ChatInterface {...defaultProps} />);
    
    const micButton = screen.getByRole('button', { name: /start voice input/i });
    await user.click(micButton);
    
    expect(mockStartListening).toHaveBeenCalled();
  });

  it('should call stopListening when microphone button is clicked while listening', async () => {
    const { useVoice } = require('../../hooks/useVoice');
    const mockStopListening = jest.fn();
    
    useVoice.mockReturnValue({
      isListening: true,
      isSupported: true,
      transcript: 'test transcript',
      confidence: 0.9,
      error: null,
      startListening: jest.fn(),
      stopListening: mockStopListening,
      speak: jest.fn(),
      isSpeaking: false,
      stopSpeaking: jest.fn(),
      voices: [],
      selectedVoice: null,
      setSelectedVoice: jest.fn(),
    });

    const user = userEvent.setup();
    render(<ChatInterface {...defaultProps} />);
    
    const micButton = screen.getByRole('button', { name: /stop listening/i });
    await user.click(micButton);
    
    expect(mockStopListening).toHaveBeenCalled();
  });

  it('should show listening state in placeholder text', () => {
    const { useVoice } = require('../../hooks/useVoice');
    
    useVoice.mockReturnValue({
      isListening: true,
      isSupported: true,
      transcript: 'analyze Apple',
      confidence: 0.9,
      error: null,
      startListening: jest.fn(),
      stopListening: jest.fn(),
      speak: jest.fn(),
      isSpeaking: false,
      stopSpeaking: jest.fn(),
      voices: [],
      selectedVoice: null,
      setSelectedVoice: jest.fn(),
    });

    render(<ChatInterface {...defaultProps} />);
    
    expect(screen.getByPlaceholderText(/Listening... "analyze Apple"/)).toBeInTheDocument();
  });

  it('should show pulse animation when listening', () => {
    const { useVoice } = require('../../hooks/useVoice');
    
    useVoice.mockReturnValue({
      isListening: true,
      isSupported: true,
      transcript: '',
      confidence: 0,
      error: null,
      startListening: jest.fn(),
      stopListening: jest.fn(),
      speak: jest.fn(),
      isSpeaking: false,
      stopSpeaking: jest.fn(),
      voices: [],
      selectedVoice: null,
      setSelectedVoice: jest.fn(),
    });

    render(<ChatInterface {...defaultProps} />);
    
    const micButton = screen.getByRole('button', { name: /stop listening/i });
    
    // Check if the button has animation styles (this is a simplified check)
    expect(micButton).toHaveStyle({ animation: expect.stringContaining('pulse') });
  });

  it('should open voice settings dialog when settings button is clicked', async () => {
    const user = userEvent.setup();
    render(<ChatInterface {...defaultProps} />);
    
    const settingsButton = screen.getByRole('button', { name: /voice settings/i });
    await user.click(settingsButton);
    
    expect(screen.getByText('Voice Settings')).toBeInTheDocument();
  });

  it('should call speak when speak button is clicked', async () => {
    const { useVoice } = require('../../hooks/useVoice');
    const mockSpeak = jest.fn();
    
    useVoice.mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      confidence: 0,
      error: null,
      startListening: jest.fn(),
      stopListening: jest.fn(),
      speak: mockSpeak,
      isSpeaking: false,
      stopSpeaking: jest.fn(),
      voices: [],
      selectedVoice: null,
      setSelectedVoice: jest.fn(),
    });

    const user = userEvent.setup();
    render(<ChatInterface {...defaultProps} />);
    
    const speakButton = screen.getByRole('button', { name: /speak last response/i });
    await user.click(speakButton);
    
    expect(mockSpeak).toHaveBeenCalled();
  });

  it('should call stopSpeaking when speak button is clicked while speaking', async () => {
    const { useVoice } = require('../../hooks/useVoice');
    const mockStopSpeaking = jest.fn();
    
    useVoice.mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      confidence: 0,
      error: null,
      startListening: jest.fn(),
      stopListening: jest.fn(),
      speak: jest.fn(),
      isSpeaking: true,
      stopSpeaking: mockStopSpeaking,
      voices: [],
      selectedVoice: null,
      setSelectedVoice: jest.fn(),
    });

    const user = userEvent.setup();
    render(<ChatInterface {...defaultProps} />);
    
    const speakButton = screen.getByRole('button', { name: /stop speaking/i });
    await user.click(speakButton);
    
    expect(mockStopSpeaking).toHaveBeenCalled();
  });

  it('should show voice error in snackbar', async () => {
    const { useVoice } = require('../../hooks/useVoice');
    
    useVoice.mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      confidence: 0,
      error: 'Microphone access denied',
      startListening: jest.fn(),
      stopListening: jest.fn(),
      speak: jest.fn(),
      isSpeaking: false,
      stopSpeaking: jest.fn(),
      voices: [],
      selectedVoice: null,
      setSelectedVoice: jest.fn(),
    });

    render(<ChatInterface {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Microphone access denied')).toBeInTheDocument();
    });
  });

  it('should show voice not supported warning when voice is not supported', () => {
    const { useVoice } = require('../../hooks/useVoice');
    
    useVoice.mockReturnValue({
      isListening: false,
      isSupported: false,
      transcript: '',
      confidence: 0,
      error: null,
      startListening: jest.fn(),
      stopListening: jest.fn(),
      speak: jest.fn(),
      isSpeaking: false,
      stopSpeaking: jest.fn(),
      voices: [],
      selectedVoice: null,
      setSelectedVoice: jest.fn(),
    });

    render(<ChatInterface {...defaultProps} />);
    
    expect(screen.getByText(/Voice input is not supported in your browser/)).toBeInTheDocument();
  });

  it('should disable voice button when not supported', () => {
    const { useVoice } = require('../../hooks/useVoice');
    
    useVoice.mockReturnValue({
      isListening: false,
      isSupported: false,
      transcript: '',
      confidence: 0,
      error: null,
      startListening: jest.fn(),
      stopListening: jest.fn(),
      speak: jest.fn(),
      isSpeaking: false,
      stopSpeaking: jest.fn(),
      voices: [],
      selectedVoice: null,
      setSelectedVoice: jest.fn(),
    });

    render(<ChatInterface {...defaultProps} voiceEnabled={false} />);
    
    // Voice button should not be present when not supported and not enabled
    expect(screen.queryByRole('button', { name: /start voice input/i })).not.toBeInTheDocument();
  });

  it('should handle navigation commands', async () => {
    const { voiceCommandProcessor } = require('../../services/voiceCommands');
    
    voiceCommandProcessor.processCommand.mockReturnValue({
      type: 'navigation',
      intent: 'navigate',
      parameters: { destination: 'alerts' },
      confidence: 1,
      originalText: 'go to alerts',
    });

    const user = userEvent.setup();
    render(<ChatInterface {...defaultProps} />);
    
    // Simulate voice result that triggers navigation
    const { useVoice } = require('../../hooks/useVoice');
    const mockOnResult = useVoice.mock.calls[0][0].onResult;
    
    // Simulate final voice result
    mockOnResult({
      transcript: 'go to alerts',
      confidence: 0.9,
      isFinal: true,
    });

    expect(defaultProps.onNavigate).toHaveBeenCalledWith('alerts');
  });

  it('should auto-speak new assistant messages when enabled', async () => {
    const { useVoice } = require('../../hooks/useVoice');
    const mockSpeak = jest.fn();
    
    useVoice.mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      confidence: 0,
      error: null,
      startListening: jest.fn(),
      stopListening: jest.fn(),
      speak: mockSpeak,
      isSpeaking: false,
      stopSpeaking: jest.fn(),
      voices: [],
      selectedVoice: null,
      setSelectedVoice: jest.fn(),
    });

    const { rerender } = render(<ChatInterface {...defaultProps} />);
    
    // Add a new assistant message
    const newMessages = [
      ...mockMessages,
      {
        id: '3',
        type: 'assistant' as const,
        content: 'Here is the analysis for AAPL.',
        timestamp: new Date(),
      },
    ];

    rerender(<ChatInterface {...defaultProps} messages={newMessages} />);

    await waitFor(() => {
      expect(mockSpeak).toHaveBeenCalledWith(
        'Here is the analysis for AAPL.',
        expect.any(Object)
      );
    });
  });
});