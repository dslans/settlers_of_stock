import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Paper,
  Typography,
  CircularProgress,
  Fade,
  useTheme,
  Tooltip,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Send as SendIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Sync as SyncIcon,
  Settings as SettingsIcon,
  VolumeUp as VolumeUpIcon,
  VolumeOff as VolumeOffIcon,
} from '@mui/icons-material';
import ChatMessage from './ChatMessage';
import VoiceSettings from './VoiceSettings';
import { ChatMessage as ChatMessageType } from '../types';
import { StockLookupResponse } from '../services/api';
import { useVoice } from '../hooks/useVoice';
import { voiceCommandProcessor, VoiceCommand } from '../services/voiceCommands';

interface ChatInterfaceProps {
  messages: ChatMessageType[];
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  voiceEnabled?: boolean;
  currentStockData?: StockLookupResponse | null;
  connected?: boolean;
  connecting?: boolean;
  connectionError?: string | null;
  onNavigate?: (destination: string) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  onSendMessage,
  isLoading = false,
  voiceEnabled = false,
  currentStockData = null,
  connected = false,
  connecting = false,
  connectionError = null,
  onNavigate,
}) => {
  const theme = useTheme();
  const [inputValue, setInputValue] = useState('');
  const [showVoiceSettings, setShowVoiceSettings] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [continuousListening, setContinuousListening] = useState(false);
  const [speechRate, setSpeechRate] = useState(1);
  const [speechPitch, setSpeechPitch] = useState(1);
  const [speechVolume, setSpeechVolume] = useState(1);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<string>('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Voice functionality
  const {
    isListening,
    isSupported: voiceSupported,
    transcript,
    confidence,
    error: voiceRecognitionError,
    startListening,
    stopListening,
    speak,
    isSpeaking,
    stopSpeaking,
    voices,
    selectedVoice,
    setSelectedVoice,
  } = useVoice({
    onResult: handleVoiceResult,
    onError: handleVoiceError,
    onStart: () => setVoiceError(null),
    continuous: continuousListening,
    interimResults: true,
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    if (inputRef.current && typeof inputRef.current.focus === 'function') {
      inputRef.current.focus();
    }
  }, []);

  // Auto-speak responses if enabled
  useEffect(() => {
    if (autoSpeak && voiceEnabled && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.type === 'assistant' && lastMessage.content !== lastResponse) {
        setLastResponse(lastMessage.content);
        // Extract text content from response (remove any markdown or formatting)
        const textContent = extractTextContent(lastMessage.content);
        if (textContent.trim()) {
          speak(textContent, {
            rate: speechRate,
            pitch: speechPitch,
            volume: speechVolume,
            voice: selectedVoice,
          });
        }
      }
    }
  }, [messages, autoSpeak, voiceEnabled, lastResponse, speak, speechRate, speechPitch, speechVolume, selectedVoice]);

  // Voice result handler
  const handleVoiceResult = useCallback((result: { transcript: string; confidence: number; isFinal: boolean }) => {
    if (result.isFinal && result.transcript.trim()) {
      const command = voiceCommandProcessor.processCommand(result.transcript, result.confidence);
      handleVoiceCommand(command);
    } else if (result.transcript.trim()) {
      // Show interim results in input field
      setInputValue(result.transcript);
    }
  }, []);

  // Voice error handler
  const handleVoiceError = useCallback((error: string) => {
    setVoiceError(error);
    console.error('Voice recognition error:', error);
  }, []);

  // Handle voice commands
  const handleVoiceCommand = useCallback((command: VoiceCommand) => {
    switch (command.type) {
      case 'stock_query':
        const message = voiceCommandProcessor.convertToMessage(command);
        onSendMessage(message);
        setInputValue('');
        break;
        
      case 'navigation':
        if (onNavigate && command.parameters.destination) {
          onNavigate(command.parameters.destination);
        }
        break;
        
      case 'action':
        handleActionCommand(command.parameters.action);
        break;
        
      default:
        // For unknown commands, just send the original text
        onSendMessage(command.originalText);
        setInputValue('');
        break;
    }
  }, [onSendMessage, onNavigate]);

  // Handle action commands
  const handleActionCommand = useCallback((action: string) => {
    switch (action) {
      case 'clear_chat':
        // This would need to be implemented in the parent component
        break;
      case 'repeat_last':
        if (lastResponse) {
          speak(extractTextContent(lastResponse), {
            rate: speechRate,
            pitch: speechPitch,
            volume: speechVolume,
            voice: selectedVoice,
          });
        }
        break;
      case 'stop_speaking':
        stopSpeaking();
        break;
      case 'help':
        const helpText = voiceCommandProcessor.getHelpText();
        speak(helpText, {
          rate: speechRate,
          pitch: speechPitch,
          volume: speechVolume,
          voice: selectedVoice,
        });
        break;
    }
  }, [lastResponse, speak, stopSpeaking, speechRate, speechPitch, speechVolume, selectedVoice]);

  // Extract text content from message (remove markdown, etc.)
  const extractTextContent = (content: string): string => {
    return content
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
      .replace(/\*(.*?)\*/g, '$1') // Remove italic markdown
      .replace(/`(.*?)`/g, '$1') // Remove code markdown
      .replace(/#{1,6}\s/g, '') // Remove headers
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Remove links, keep text
      .replace(/\n+/g, ' ') // Replace newlines with spaces
      .trim();
  };

  const handleSendMessage = () => {
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleVoiceToggle = () => {
    if (!voiceEnabled || !voiceSupported) return;
    
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const handleSpeakToggle = () => {
    if (isSpeaking) {
      stopSpeaking();
    } else if (lastResponse) {
      speak(extractTextContent(lastResponse), {
        rate: speechRate,
        pitch: speechPitch,
        volume: speechVolume,
        voice: selectedVoice,
      });
    }
  };

  const getPlaceholderText = () => {
    if (isLoading) return 'Processing your request...';
    if (isListening) return `Listening... ${transcript ? `"${transcript}"` : ''}`;
    if (voiceEnabled && voiceSupported) {
      return 'Ask about a stock or use voice input (e.g., "Analyze Apple")';
    }
    return 'Ask about a stock (e.g., "What\'s the analysis for AAPL?")';
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        maxHeight: '80vh',
        minHeight: '500px',
      }}
    >
      {/* Header */}
      <Paper
        elevation={1}
        sx={{
          p: 2,
          borderRadius: '12px 12px 0 0',
          backgroundColor: theme.palette.primary.main,
          color: theme.palette.primary.contrastText,
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h6" component="h2">
              Stock Research Chat
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Ask me anything about stocks, market analysis, or investment insights
            </Typography>
          </Box>
          
          {/* Voice and Connection Status */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* Voice Controls */}
            {voiceEnabled && (
              <>
                <Tooltip title={isSpeaking ? 'Stop speaking' : 'Speak last response'}>
                  <IconButton
                    size="small"
                    onClick={handleSpeakToggle}
                    disabled={!lastResponse}
                    sx={{ color: 'inherit' }}
                  >
                    {isSpeaking ? <VolumeOffIcon /> : <VolumeUpIcon />}
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Voice settings">
                  <IconButton
                    size="small"
                    onClick={() => setShowVoiceSettings(true)}
                    sx={{ color: 'inherit' }}
                  >
                    <SettingsIcon />
                  </IconButton>
                </Tooltip>
              </>
            )}
            
            {/* Connection Status Indicator */}
            {connecting ? (
              <>
                <SyncIcon 
                  sx={{ 
                    fontSize: 20, 
                    '@keyframes spin': {
                      '0%': { transform: 'rotate(0deg)' },
                      '100%': { transform: 'rotate(360deg)' }
                    },
                    animation: 'spin 1s linear infinite'
                  }} 
                />
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  Connecting...
                </Typography>
              </>
            ) : connected ? (
              <>
                <WifiIcon sx={{ fontSize: 20, color: theme.palette.success.light }} />
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  Real-time
                </Typography>
              </>
            ) : (
              <>
                <WifiOffIcon sx={{ fontSize: 20, color: theme.palette.warning.light }} />
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  {connectionError ? 'Error' : 'Offline'}
                </Typography>
              </>
            )}
          </Box>
        </Box>
      </Paper>

      {/* Messages Container */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          backgroundColor: theme.palette.background.default,
          minHeight: 0, // Important for flex child to shrink
        }}
      >
        {messages.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
              color: theme.palette.text.secondary,
            }}
          >
            <Typography variant="h6" gutterBottom>
              Welcome to Settlers of Stock!
            </Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Start by asking about a stock or requesting market analysis.
            </Typography>
            <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
              Try: "Analyze AAPL" or "What's the market sentiment for Tesla?"
            </Typography>
          </Box>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage 
                key={message.id} 
                message={message} 
                stockData={message.metadata?.stockSymbol && currentStockData?.stock.symbol === message.metadata.stockSymbol ? currentStockData : null}
              />
            ))}
            {isLoading && (
              <Fade in={isLoading}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    p: 2,
                    justifyContent: 'flex-start',
                  }}
                >
                  <CircularProgress size={20} />
                  <Typography variant="body2" color="text.secondary">
                    Analyzing market data...
                  </Typography>
                </Box>
              </Fade>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </Box>

      {/* Input Area */}
      <Paper
        elevation={2}
        sx={{
          p: 2,
          borderRadius: '0 0 12px 12px',
          backgroundColor: theme.palette.background.paper,
        }}
      >
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={getPlaceholderText()}
            disabled={isLoading || isListening}
            variant="outlined"
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: '20px',
                backgroundColor: theme.palette.background.default,
              },
            }}
          />
          
          {voiceEnabled && voiceSupported && (
            <Tooltip title={isListening ? 'Stop listening' : 'Start voice input'}>
              <IconButton
                onClick={handleVoiceToggle}
                disabled={isLoading}
                color={isListening ? 'secondary' : 'default'}
                sx={{
                  backgroundColor: isListening 
                    ? theme.palette.secondary.light 
                    : theme.palette.action.hover,
                  '&:hover': {
                    backgroundColor: isListening 
                      ? theme.palette.secondary.main 
                      : theme.palette.action.selected,
                  },
                  ...(isListening && {
                    '@keyframes pulse': {
                      '0%': { transform: 'scale(1)' },
                      '50%': { transform: 'scale(1.1)' },
                      '100%': { transform: 'scale(1)' },
                    },
                    animation: 'pulse 1.5s ease-in-out infinite',
                  }),
                }}
              >
                {isListening ? <MicOffIcon /> : <MicIcon />}
              </IconButton>
            </Tooltip>
          )}
          
          <IconButton
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading || isListening}
            color="primary"
            sx={{
              backgroundColor: theme.palette.primary.main,
              color: theme.palette.primary.contrastText,
              '&:hover': {
                backgroundColor: theme.palette.primary.dark,
              },
              '&:disabled': {
                backgroundColor: theme.palette.action.disabledBackground,
                color: theme.palette.action.disabled,
              },
            }}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Paper>

      {/* Voice Settings Dialog */}
      {voiceEnabled && (
        <VoiceSettings
          open={showVoiceSettings}
          onClose={() => setShowVoiceSettings(false)}
          voices={voices}
          selectedVoice={selectedVoice}
          onVoiceChange={setSelectedVoice}
          speechRate={speechRate}
          onSpeechRateChange={setSpeechRate}
          speechPitch={speechPitch}
          onSpeechPitchChange={setSpeechPitch}
          speechVolume={speechVolume}
          onSpeechVolumeChange={setSpeechVolume}
          autoSpeak={autoSpeak}
          onAutoSpeakChange={setAutoSpeak}
          continuousListening={continuousListening}
          onContinuousListeningChange={setContinuousListening}
        />
      )}

      {/* Voice Error Snackbar */}
      <Snackbar
        open={!!voiceError}
        autoHideDuration={6000}
        onClose={() => setVoiceError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setVoiceError(null)} 
          severity="warning" 
          sx={{ width: '100%' }}
        >
          {voiceError}
        </Alert>
      </Snackbar>

      {/* Voice Recognition Error Snackbar */}
      <Snackbar
        open={!!voiceRecognitionError}
        autoHideDuration={6000}
        onClose={() => {}} // Error is cleared by the hook
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          severity="error" 
          sx={{ width: '100%' }}
        >
          {voiceRecognitionError}
        </Alert>
      </Snackbar>

      {/* Voice Not Supported Warning */}
      {voiceEnabled && !voiceSupported && (
        <Snackbar
          open={true}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert severity="info" sx={{ width: '100%' }}>
            Voice input is not supported in your browser. Please use a modern browser like Chrome or Edge.
          </Alert>
        </Snackbar>
      )}
    </Box>
  );
};

export default ChatInterface;