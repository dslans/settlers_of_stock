/**
 * Tests for WebSocket service functionality
 * Tests connection management, message handling, and error scenarios
 */

import { WebSocketService, createChatWebSocketService } from '../websocket';

// Mock WebSocket
class MockWebSocket {
  public readyState: number = WebSocket.CONNECTING;
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  
  private listeners: { [key: string]: Function[] } = {};
  
  constructor(public url: string) {
    // Simulate async connection
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.onopen?.(new Event('open'));
    }, 10);
  }
  
  send(data: string): void {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    // Echo back for testing
    setTimeout(() => {
      const message = new MessageEvent('message', { data });
      this.onmessage?.(message);
    }, 5);
  }
  
  close(code?: number, reason?: string): void {
    this.readyState = WebSocket.CLOSED;
    const closeEvent = new CloseEvent('close', { code: code || 1000, reason: reason || '' });
    this.onclose?.(closeEvent);
  }
  
  addEventListener(type: string, listener: Function): void {
    if (!this.listeners[type]) {
      this.listeners[type] = [];
    }
    this.listeners[type].push(listener);
  }
  
  removeEventListener(type: string, listener: Function): void {
    if (this.listeners[type]) {
      this.listeners[type] = this.listeners[type].filter(l => l !== listener);
    }
  }
}

// Mock global WebSocket
(global as any).WebSocket = MockWebSocket;

describe('WebSocketService', () => {
  let service: WebSocketService;
  let mockCallbacks: any;

  beforeEach(() => {
    mockCallbacks = {
      onConnect: jest.fn(),
      onDisconnect: jest.fn(),
      onReconnect: jest.fn(),
      onError: jest.fn(),
      onMessage: jest.fn(),
      onChatResponse: jest.fn(),
      onSystemMessage: jest.fn(),
    };

    service = new WebSocketService(
      {
        url: 'ws://localhost:8000/ws/chat',
        reconnectInterval: 100,
        maxReconnectAttempts: 3,
        heartbeatInterval: 1000,
      },
      mockCallbacks
    );
  });

  afterEach(() => {
    service.disconnect();
  });

  describe('Connection Management', () => {
    test('should connect successfully', async () => {
      await service.connect('test-token');
      
      expect(mockCallbacks.onConnect).toHaveBeenCalled();
      
      const status = service.getConnectionStatus();
      expect(status.connected).toBe(true);
      expect(status.connecting).toBe(false);
    });

    test('should handle connection failure', async () => {
      // Mock WebSocket constructor to throw error
      (global as any).WebSocket = jest.fn().mockImplementation(() => {
        throw new Error('Connection failed');
      });

      await expect(service.connect('test-token')).rejects.toThrow('Connection failed');
      expect(mockCallbacks.onError).toHaveBeenCalled();
    });

    test('should disconnect properly', async () => {
      await service.connect('test-token');
      service.disconnect();
      
      expect(mockCallbacks.onDisconnect).toHaveBeenCalled();
      
      const status = service.getConnectionStatus();
      expect(status.connected).toBe(false);
    });

    test('should prevent multiple simultaneous connections', async () => {
      const promise1 = service.connect('test-token');
      const promise2 = service.connect('test-token');
      
      await expect(promise2).rejects.toThrow('Connection already in progress');
      await promise1; // Complete first connection
    });
  });

  describe('Message Handling', () => {
    beforeEach(async () => {
      await service.connect('test-token');
    });

    test('should send chat message successfully', () => {
      const result = service.sendChatMessage('Hello, world!');
      expect(result).toBe(true);
    });

    test('should handle message sending when disconnected', () => {
      service.disconnect();
      const result = service.sendChatMessage('Hello, world!');
      expect(result).toBe(false);
    });

    test('should receive and parse messages', (done) => {
      const testMessage = {
        type: 'chat_response',
        message: 'Hello back!',
        timestamp: new Date().toISOString(),
      };

      mockCallbacks.onChatResponse.mockImplementation((message: any) => {
        expect(message.type).toBe('chat_response');
        expect(message.message).toBe('Hello back!');
        done();
      });

      // Simulate receiving message
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify(testMessage),
      });
      
      // Access the WebSocket instance and trigger message handler
      const ws = (service as any).ws;
      ws.onmessage(messageEvent);
    });

    test('should handle invalid JSON messages', () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      
      // Simulate receiving invalid JSON
      const messageEvent = new MessageEvent('message', {
        data: 'invalid json',
      });
      
      const ws = (service as any).ws;
      ws.onmessage(messageEvent);
      
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error parsing WebSocket message:',
        expect.any(Error)
      );
      
      consoleErrorSpy.mockRestore();
    });
  });

  describe('Reconnection Logic', () => {
    test('should attempt reconnection on unexpected disconnect', (done) => {
      let reconnectAttempts = 0;
      
      mockCallbacks.onReconnect = jest.fn(() => {
        reconnectAttempts++;
        if (reconnectAttempts === 1) {
          done();
        }
      });

      service.connect('test-token').then(() => {
        // Simulate unexpected disconnect
        const ws = (service as any).ws;
        ws.close(1006, 'Connection lost'); // Abnormal closure
      });
    });

    test('should not reconnect on manual disconnect', async () => {
      await service.connect('test-token');
      service.disconnect();
      
      // Wait a bit to see if reconnection is attempted
      await new Promise(resolve => setTimeout(resolve, 200));
      
      expect(mockCallbacks.onReconnect).not.toHaveBeenCalled();
    });

    test('should stop reconnecting after max attempts', (done) => {
      let disconnectCount = 0;
      
      // Mock WebSocket to always fail connection
      (global as any).WebSocket = jest.fn().mockImplementation(() => {
        const mockWs = new MockWebSocket('ws://test');
        setTimeout(() => {
          mockWs.readyState = WebSocket.CLOSED;
          mockWs.onclose?.(new CloseEvent('close', { code: 1006 }));
        }, 10);
        return mockWs;
      });

      mockCallbacks.onDisconnect = jest.fn(() => {
        disconnectCount++;
        if (disconnectCount >= 4) { // Initial + 3 reconnect attempts
          done();
        }
      });

      service.connect('test-token').catch(() => {
        // Expected to fail
      });
    });
  });

  describe('Connection Status', () => {
    test('should return correct status when disconnected', () => {
      const status = service.getConnectionStatus();
      expect(status.connected).toBe(false);
      expect(status.connecting).toBe(false);
      expect(status.readyState).toBeNull();
    });

    test('should return correct status when connected', async () => {
      await service.connect('test-token');
      
      const status = service.getConnectionStatus();
      expect(status.connected).toBe(true);
      expect(status.connecting).toBe(false);
      expect(status.readyState).toBe(WebSocket.OPEN);
    });
  });

  describe('Heartbeat', () => {
    test('should send heartbeat messages', (done) => {
      const service = new WebSocketService(
        {
          url: 'ws://localhost:8000/ws/chat',
          reconnectInterval: 100,
          maxReconnectAttempts: 3,
          heartbeatInterval: 50, // Very short for testing
        },
        mockCallbacks
      );

      let heartbeatReceived = false;
      
      // Mock send to capture heartbeat
      const originalSend = service.sendMessage;
      service.sendMessage = jest.fn((message: any) => {
        if (message.type === 'ping') {
          heartbeatReceived = true;
          done();
        }
        return originalSend.call(service, message);
      });

      service.connect('test-token');
    });
  });
});

describe('createChatWebSocketService', () => {
  test('should create service with correct configuration', () => {
    const callbacks = {
      onConnect: jest.fn(),
    };

    const service = createChatWebSocketService(callbacks);
    expect(service).toBeInstanceOf(WebSocketService);
  });

  test('should use correct WebSocket URL', () => {
    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: {
        protocol: 'https:',
        host: 'example.com',
      },
      writable: true,
    });

    const service = createChatWebSocketService({});
    
    // Access private url property for testing
    const config = (service as any).config;
    expect(config.url).toContain('wss://');
    expect(config.url).toContain('example.com');
    expect(config.url).toContain('/api/v1/ws/chat');
  });
});

describe('Message Type Handling', () => {
  let service: WebSocketService;
  let mockCallbacks: any;

  beforeEach(async () => {
    mockCallbacks = {
      onConnect: jest.fn(),
      onChatResponse: jest.fn(),
      onSystemMessage: jest.fn(),
      onMarketUpdate: jest.fn(),
      onMessage: jest.fn(),
    };

    service = new WebSocketService(
      {
        url: 'ws://localhost:8000/ws/chat',
        reconnectInterval: 100,
        maxReconnectAttempts: 3,
        heartbeatInterval: 1000,
      },
      mockCallbacks
    );

    await service.connect('test-token');
  });

  afterEach(() => {
    service.disconnect();
  });

  test('should handle chat response messages', () => {
    const testMessage = {
      type: 'chat_response',
      message: 'Analysis complete',
      message_type: 'assistant',
      suggestions: ['Ask about risks', 'Compare with peers'],
      requires_follow_up: false,
      timestamp: new Date().toISOString(),
    };

    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify(testMessage),
    });

    const ws = (service as any).ws;
    ws.onmessage(messageEvent);

    expect(mockCallbacks.onChatResponse).toHaveBeenCalledWith(testMessage);
    expect(mockCallbacks.onMessage).toHaveBeenCalledWith(testMessage);
  });

  test('should handle system messages', () => {
    const testMessage = {
      type: 'system_message',
      message: 'Connection established',
      level: 'info',
      timestamp: new Date().toISOString(),
    };

    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify(testMessage),
    });

    const ws = (service as any).ws;
    ws.onmessage(messageEvent);

    expect(mockCallbacks.onSystemMessage).toHaveBeenCalledWith(testMessage);
    expect(mockCallbacks.onMessage).toHaveBeenCalledWith(testMessage);
  });

  test('should handle error messages', () => {
    const testMessage = {
      type: 'error',
      message: 'Processing failed',
      error_code: 'PROCESSING_ERROR',
      timestamp: new Date().toISOString(),
    };

    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify(testMessage),
    });

    const ws = (service as any).ws;
    ws.onmessage(messageEvent);

    expect(mockCallbacks.onSystemMessage).toHaveBeenCalledWith(testMessage);
  });

  test('should handle market update messages', () => {
    const testMessage = {
      type: 'market_update',
      data: {
        AAPL: { price: 150.25, change: 1.5 },
        TSLA: { price: 250.80, change: -2.1 },
      },
      timestamp: new Date().toISOString(),
    };

    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify(testMessage),
    });

    const ws = (service as any).ws;
    ws.onmessage(messageEvent);

    expect(mockCallbacks.onMarketUpdate).toHaveBeenCalledWith(testMessage);
    expect(mockCallbacks.onMessage).toHaveBeenCalledWith(testMessage);
  });

  test('should handle unknown message types', () => {
    const consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    
    const testMessage = {
      type: 'unknown_type',
      data: 'some data',
      timestamp: new Date().toISOString(),
    };

    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify(testMessage),
    });

    const ws = (service as any).ws;
    ws.onmessage(messageEvent);

    expect(consoleLogSpy).toHaveBeenCalledWith('Unknown message type:', 'unknown_type');
    expect(mockCallbacks.onMessage).toHaveBeenCalledWith(testMessage);
    
    consoleLogSpy.mockRestore();
  });
});