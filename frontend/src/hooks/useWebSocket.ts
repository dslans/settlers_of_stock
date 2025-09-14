/**
 * React hook for managing WebSocket connections
 * Provides real-time chat functionality with connection management and error handling
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  WebSocketService, 
  WebSocketCallbacks, 
  ChatResponseMessage, 
  SystemMessage,
  MarketUpdateMessage,
  createChatWebSocketService,
  createMarketWebSocketService
} from '../services/websocket';
import { ChatMessage } from '../types';

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  onChatResponse?: (response: ChatResponseMessage) => void;
  onSystemMessage?: (message: SystemMessage) => void;
  onMarketUpdate?: (update: MarketUpdateMessage) => void;
  onConnectionChange?: (connected: boolean) => void;
}

export interface UseWebSocketReturn {
  // Connection state
  connected: boolean;
  connecting: boolean;
  error: string | null;
  
  // Connection management
  connect: () => Promise<void>;
  disconnect: () => void;
  
  // Message sending
  sendMessage: (message: string, analysisData?: any) => boolean;
  
  // Connection info
  connectionStatus: {
    connected: boolean;
    connecting: boolean;
    readyState: number | null;
  };
}

export const useWebSocket = (
  type: 'chat' | 'market' = 'chat',
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const wsServiceRef = useRef<WebSocketService | null>(null);
  const tokenRef = useRef<string | null>(null);

  // Get auth token
  const getToken = useCallback((): string | null => {
    return localStorage.getItem('access_token');
  }, []);

  // WebSocket callbacks
  const callbacks: WebSocketCallbacks = {
    onConnect: () => {
      console.log(`${type} WebSocket connected`);
      setConnected(true);
      setConnecting(false);
      setError(null);
      options.onConnectionChange?.(true);
    },
    
    onDisconnect: () => {
      console.log(`${type} WebSocket disconnected`);
      setConnected(false);
      setConnecting(false);
      options.onConnectionChange?.(false);
    },
    
    onReconnect: () => {
      console.log(`${type} WebSocket reconnected`);
      setError(null);
    },
    
    onError: (error) => {
      console.error(`${type} WebSocket error:`, error);
      setError('Connection error occurred');
      setConnecting(false);
    },
    
    onChatResponse: options.onChatResponse,
    onSystemMessage: (message) => {
      if (message.type === 'error') {
        setError(message.message);
      }
      options.onSystemMessage?.(message);
    },
    onMarketUpdate: options.onMarketUpdate
  };

  // Initialize WebSocket service
  useEffect(() => {
    if (type === 'chat') {
      wsServiceRef.current = createChatWebSocketService(callbacks);
    } else {
      wsServiceRef.current = createMarketWebSocketService(callbacks);
    }

    return () => {
      if (wsServiceRef.current) {
        wsServiceRef.current.disconnect();
      }
    };
  }, [type]);

  // Auto-connect if enabled
  useEffect(() => {
    if (options.autoConnect && wsServiceRef.current && !connected && !connecting) {
      const token = getToken();
      if (token) {
        connect();
      }
    }
  }, [options.autoConnect, connected, connecting]);

  // Connect function
  const connect = useCallback(async (): Promise<void> => {
    if (!wsServiceRef.current) {
      throw new Error('WebSocket service not initialized');
    }

    const token = getToken();
    if (!token) {
      throw new Error('No authentication token available');
    }

    setConnecting(true);
    setError(null);
    tokenRef.current = token;

    try {
      await wsServiceRef.current.connect(token);
    } catch (error) {
      setConnecting(false);
      const errorMessage = error instanceof Error ? error.message : 'Connection failed';
      setError(errorMessage);
      throw error;
    }
  }, [getToken]);

  // Disconnect function
  const disconnect = useCallback((): void => {
    if (wsServiceRef.current) {
      wsServiceRef.current.disconnect();
    }
    setConnected(false);
    setConnecting(false);
    setError(null);
  }, []);

  // Send message function
  const sendMessage = useCallback((message: string, analysisData?: any): boolean => {
    if (!wsServiceRef.current) {
      console.warn('WebSocket service not available');
      return false;
    }

    if (type === 'chat') {
      return wsServiceRef.current.sendChatMessage(message, analysisData);
    } else {
      // For market updates, we typically don't send messages
      console.warn('Sending messages not supported for market WebSocket');
      return false;
    }
  }, [type]);

  // Get connection status
  const connectionStatus = wsServiceRef.current?.getConnectionStatus() || {
    connected: false,
    connecting: false,
    readyState: null
  };

  return {
    connected,
    connecting,
    error,
    connect,
    disconnect,
    sendMessage,
    connectionStatus
  };
};

/**
 * Hook specifically for chat WebSocket functionality
 */
export const useChatWebSocket = (options: UseWebSocketOptions = {}) => {
  return useWebSocket('chat', options);
};

/**
 * Hook specifically for market updates WebSocket functionality
 */
export const useMarketWebSocket = (options: UseWebSocketOptions = {}) => {
  return useWebSocket('market', options);
};