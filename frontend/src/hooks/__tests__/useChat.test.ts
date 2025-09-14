import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useChat } from '../useChat';
import * as api from '../../services/api';

// Mock the API
jest.mock('../../services/api');
const mockApi = api as jest.Mocked<typeof api>;

// Mock WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: WebSocket.OPEN,
};

global.WebSocket = jest.fn(() => mockWebSocket) as any;

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useChat Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('initializes with empty messages', () => {
    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('sends message and receives response', async () => {
    const mockResponse = {
      response: 'Apple Inc. (AAPL) is currently trading at $150.00',
      context: { currentStock: 'AAPL' },
      timestamp: new Date().toISOString(),
    };

    mockApi.chatApi.sendMessage.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.sendMessage('Tell me about AAPL');
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2);
    });

    expect(result.current.messages[0]).toMatchObject({
      type: 'user',
      content: 'Tell me about AAPL',
    });

    expect(result.current.messages[1]).toMatchObject({
      type: 'assistant',
      content: mockResponse.response,
    });

    expect(mockApi.chatApi.sendMessage).toHaveBeenCalledWith({
      message: 'Tell me about AAPL',
      context: {},
    });
  });

  it('handles API errors gracefully', async () => {
    const errorMessage = 'Failed to process request';
    mockApi.chatApi.sendMessage.mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    await waitFor(() => {
      expect(result.current.error).toBe(errorMessage);
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[1]).toMatchObject({
      type: 'system',
      content: expect.stringContaining('Sorry, I encountered an error'),
    });
  });

  it('maintains conversation context', async () => {
    const firstResponse = {
      response: 'Apple Inc. is a technology company',
      context: { currentStock: 'AAPL', previousTopics: ['company_info'] },
      timestamp: new Date().toISOString(),
    };

    const secondResponse = {
      response: 'AAPL is currently trading at $150.00',
      context: { currentStock: 'AAPL', previousTopics: ['company_info', 'price'] },
      timestamp: new Date().toISOString(),
    };

    mockApi.chatApi.sendMessage
      .mockResolvedValueOnce(firstResponse)
      .mockResolvedValueOnce(secondResponse);

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    // First message
    await act(async () => {
      await result.current.sendMessage('What is Apple?');
    });

    // Second message with context
    await act(async () => {
      await result.current.sendMessage('What is its current price?');
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(4);
    });

    // Verify second API call includes context from first response
    expect(mockApi.chatApi.sendMessage).toHaveBeenNthCalledWith(2, {
      message: 'What is its current price?',
      context: firstResponse.context,
    });
  });

  it('handles loading states correctly', async () => {
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    mockApi.chatApi.sendMessage.mockReturnValue(promise);

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    // Start sending message
    act(() => {
      result.current.sendMessage('Test message');
    });

    // Should be loading
    expect(result.current.isLoading).toBe(true);

    // Resolve the promise
    await act(async () => {
      resolvePromise!({
        response: 'Test response',
        context: {},
        timestamp: new Date().toISOString(),
      });
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('clears messages when requested', () => {
    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    // Add some messages first
    act(() => {
      result.current.addMessage({
        id: '1',
        type: 'user',
        content: 'Test message',
        timestamp: new Date(),
      });
    });

    expect(result.current.messages).toHaveLength(1);

    // Clear messages
    act(() => {
      result.current.clearMessages();
    });

    expect(result.current.messages).toHaveLength(0);
  });

  it('handles WebSocket messages', async () => {
    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    // Simulate WebSocket message
    const wsMessage = {
      type: 'stock_update',
      data: {
        symbol: 'AAPL',
        price: 151.00,
        change: 1.00,
      },
    };

    act(() => {
      // Simulate WebSocket message event
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify(wsMessage),
      });
      
      // Find the message event listener and call it
      const addEventListenerCalls = mockWebSocket.addEventListener.mock.calls;
      const messageListener = addEventListenerCalls.find(
        call => call[0] === 'message'
      )?.[1];
      
      if (messageListener) {
        messageListener(messageEvent);
      }
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(1);
    });

    expect(result.current.messages[0]).toMatchObject({
      type: 'system',
      content: expect.stringContaining('AAPL updated'),
    });
  });

  it('retries failed requests', async () => {
    mockApi.chatApi.sendMessage
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        response: 'Success after retry',
        context: {},
        timestamp: new Date().toISOString(),
      });

    const { result } = renderHook(() => useChat(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2);
    });

    // Should have retried and succeeded
    expect(mockApi.chatApi.sendMessage).toHaveBeenCalledTimes(2);
    expect(result.current.messages[1].content).toBe('Success after retry');
  });

  it('handles voice input integration', async () => {
    const { result } = renderHook(() => useChat({ voiceEnabled: true }), {
      wrapper: createWrapper(),
    });

    expect(result.current.voiceEnabled).toBe(true);

    // Mock voice recognition result
    const mockVoiceResult = 'Tell me about Apple stock';
    
    await act(async () => {
      result.current.handleVoiceInput(mockVoiceResult);
    });

    expect(mockApi.chatApi.sendMessage).toHaveBeenCalledWith({
      message: mockVoiceResult,
      context: {},
    });
  });

  it('manages conversation history limit', async () => {
    const { result } = renderHook(() => useChat({ maxMessages: 3 }), {
      wrapper: createWrapper(),
    });

    // Add messages beyond the limit
    for (let i = 0; i < 5; i++) {
      act(() => {
        result.current.addMessage({
          id: `msg-${i}`,
          type: 'user',
          content: `Message ${i}`,
          timestamp: new Date(),
        });
      });
    }

    // Should only keep the last 3 messages
    expect(result.current.messages).toHaveLength(3);
    expect(result.current.messages[0].content).toBe('Message 2');
    expect(result.current.messages[2].content).toBe('Message 4');
  });
});