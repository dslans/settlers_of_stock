/**
 * Tests for useWebSocket hook
 * Tests React hook functionality for WebSocket management
 */

import { renderHook, act } from '@testing-library/react';
import { useWebSocket, useChatWebSocket } from '../useWebSocket';
import { WebSocketService } from '../../services/websocket';

// Mock WebSocket service
jest.mock('../../services/websocket');

const MockWebSocketService = WebSocketService as jest.MockedClass<typeof WebSocketService>;

describe('useWebSocket', () => {
  let mockService: jest.Mocked<WebSocketService>;

  beforeEach(() => {
    mockService = {
      connect: jest.fn().mockResolvedValue(undefined),
      disconnect: jest.fn(),
      sendChatMessage: jest.fn().mockReturnValue(true),
      sendMessage: jest.fn().mockReturnValue(true),
      getConnectionStatus: jest.fn().mockReturnValue({
        connected: false,
        connecting: false,
        readyState: null,
      }),
    } as any;

    MockWebSocketService.mockImplementation(() => mockService);

    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn().mockReturnValue('mock-token'),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      },
      writable: true,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Connection Management', () => {
    test('should initialize with disconnected state', () => {
      const { result } = renderHook(() => useWebSocket('chat'));

      expect(result.current.connected).toBe(false);
      expect(result.current.connecting).toBe(false);
      expect(result.current.error).toBeNull();
    });

    test('should connect successfully', async () => {
      const { result } = renderHook(() => useWebSocket('chat'));

      await act(async () => {
        await result.current.connect();
      });

      expect(mockService.connect).toHaveBeenCalledWith('mock-token');
    });

    test('should handle connection error', async () => {
      mockService.connect.mockRejectedValue(new Error('Connection failed'));

      const { result } = renderHook(() => useWebSocket('chat'));

      await act(async () => {
        try {
          await result.current.connect();
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe('Connection failed');
    });

    test('should disconnect properly', () => {
      const { result } = renderHook(() => useWebSocket('chat'));

      act(() => {
        result.current.disconnect();
      });

      expect(mockService.disconnect).toHaveBeenCalled();
    });

    test('should handle missing auth token', async () => {
      (window.localStorage.getItem as jest.Mock).mockReturnValue(null);

      const { result } = renderHook(() => useWebSocket('chat'));

      await act(async () => {
        try {
          await result.current.connect();
        } catch (error) {
          expect(error).toEqual(new Error('No authentication token available'));
        }
      });
    });
  });

  describe('Message Sending', () => {
    test('should send chat message successfully', () => {
      const { result } = renderHook(() => useWebSocket('chat'));

      const sent = result.current.sendMessage('Hello, world!');

      expect(sent).toBe(true);
      expect(mockService.sendChatMessage).toHaveBeenCalledWith('Hello, world!', undefined);
    });

    test('should send chat message with analysis data', () => {
      const { result } = renderHook(() => useWebSocket('chat'));
      const analysisData = { symbol: 'AAPL', price: 150 };

      const sent = result.current.sendMessage('Analyze AAPL', analysisData);

      expect(sent).toBe(true);
      expect(mockService.sendChatMessage).toHaveBeenCalledWith('Analyze AAPL', analysisData);
    });

    test('should handle message sending failure', () => {
      mockService.sendChatMessage.mockReturnValue(false);

      const { result } = renderHook(() => useWebSocket('chat'));

      const sent = result.current.sendMessage('Hello, world!');

      expect(sent).toBe(false);
    });

    test('should not send messages for market WebSocket', () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();

      const { result } = renderHook(() => useWebSocket('market'));

      const sent = result.current.sendMessage('Hello, world!');

      expect(sent).toBe(false);
      expect(consoleWarnSpy).toHaveBeenCalledWith('Sending messages not supported for market WebSocket');

      consoleWarnSpy.mockRestore();
    });
  });

  describe('Auto-connect', () => {
    test('should auto-connect when enabled', async () => {
      mockService.getConnectionStatus.mockReturnValue({
        connected: false,
        connecting: false,
        readyState: null,
      });

      renderHook(() => useWebSocket('chat', { autoConnect: true }));

      // Wait for useEffect to run
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(mockService.connect).toHaveBeenCalledWith('mock-token');
    });

    test('should not auto-connect when disabled', async () => {
      renderHook(() => useWebSocket('chat', { autoConnect: false }));

      // Wait for useEffect to run
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(mockService.connect).not.toHaveBeenCalled();
    });

    test('should not auto-connect when already connected', async () => {
      mockService.getConnectionStatus.mockReturnValue({
        connected: true,
        connecting: false,
        readyState: WebSocket.OPEN,
      });

      const { result } = renderHook(() => useWebSocket('chat', { autoConnect: true }));

      // Simulate connected state
      act(() => {
        // Trigger state update to simulate connection
      });

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
      });

      expect(mockService.connect).not.toHaveBeenCalled();
    });
  });

  describe('Callback Handling', () => {
    test('should call onConnectionChange callback', () => {
      const onConnectionChange = jest.fn();

      renderHook(() => useWebSocket('chat', { onConnectionChange }));

      // Simulate connection state change by calling the callback directly
      const callbacks = MockWebSocketService.mock.calls[0][1];
      
      act(() => {
        callbacks.onConnect?.();
      });

      expect(onConnectionChange).toHaveBeenCalledWith(true);

      act(() => {
        callbacks.onDisconnect?.();
      });

      expect(onConnectionChange).toHaveBeenCalledWith(false);
    });

    test('should call onChatResponse callback', () => {
      const onChatResponse = jest.fn();
      const mockResponse = {
        type: 'chat_response',
        message: 'Hello back!',
        message_type: 'assistant',
        suggestions: [],
        requires_follow_up: false,
        timestamp: new Date().toISOString(),
      };

      renderHook(() => useWebSocket('chat', { onChatResponse }));

      const callbacks = MockWebSocketService.mock.calls[0][1];
      
      act(() => {
        callbacks.onChatResponse?.(mockResponse);
      });

      expect(onChatResponse).toHaveBeenCalledWith(mockResponse);
    });

    test('should call onSystemMessage callback', () => {
      const onSystemMessage = jest.fn();
      const mockMessage = {
        type: 'system_message',
        message: 'System notification',
        level: 'info',
        timestamp: new Date().toISOString(),
      };

      renderHook(() => useWebSocket('chat', { onSystemMessage }));

      const callbacks = MockWebSocketService.mock.calls[0][1];
      
      act(() => {
        callbacks.onSystemMessage?.(mockMessage);
      });

      expect(onSystemMessage).toHaveBeenCalledWith(mockMessage);
    });

    test('should handle error in system message callback', () => {
      const { result } = renderHook(() => useWebSocket('chat'));

      const callbacks = MockWebSocketService.mock.calls[0][1];
      const errorMessage = {
        type: 'error',
        message: 'Something went wrong',
        error_code: 'PROCESSING_ERROR',
        timestamp: new Date().toISOString(),
      };
      
      act(() => {
        callbacks.onSystemMessage?.(errorMessage);
      });

      expect(result.current.error).toBe('Something went wrong');
    });
  });

  describe('Connection Status', () => {
    test('should return correct connection status', () => {
      mockService.getConnectionStatus.mockReturnValue({
        connected: true,
        connecting: false,
        readyState: WebSocket.OPEN,
      });

      const { result } = renderHook(() => useWebSocket('chat'));

      expect(result.current.connectionStatus.connected).toBe(true);
      expect(result.current.connectionStatus.connecting).toBe(false);
      expect(result.current.connectionStatus.readyState).toBe(WebSocket.OPEN);
    });
  });
});

describe('useChatWebSocket', () => {
  test('should create chat WebSocket with correct type', () => {
    const { result } = renderHook(() => useChatWebSocket());

    expect(result.current.connected).toBe(false);
    expect(MockWebSocketService).toHaveBeenCalled();
  });

  test('should pass options correctly', () => {
    const options = {
      autoConnect: true,
      onChatResponse: jest.fn(),
    };

    renderHook(() => useChatWebSocket(options));

    // Verify the service was created with chat type
    expect(MockWebSocketService).toHaveBeenCalled();
  });
});

describe('useMarketWebSocket', () => {
  test('should create market WebSocket with correct type', () => {
    const { useMarketWebSocket } = require('../useWebSocket');
    
    const { result } = renderHook(() => useMarketWebSocket());

    expect(result.current.connected).toBe(false);
    expect(MockWebSocketService).toHaveBeenCalled();
  });
});