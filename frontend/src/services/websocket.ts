/**
 * WebSocket service for real-time chat communication
 * Handles connection management, message sending/receiving, and reconnection logic
 */

import { ChatMessage } from '../types';

export interface WebSocketMessage {
  type: string;
  timestamp: string;
}

export interface ChatWebSocketMessage extends WebSocketMessage {
  type: 'chat_message';
  message: string;
  analysis_data?: any;
}

export interface ChatResponseMessage extends WebSocketMessage {
  type: 'chat_response';
  message: string;
  message_type: string;
  analysis_data?: any;
  suggestions: string[];
  requires_follow_up: boolean;
}

export interface SystemMessage extends WebSocketMessage {
  type: 'system_message' | 'connection_status' | 'error';
  message: string;
  level?: string;
  status?: string;
  user_count?: number;
  error_code?: string;
}

export interface MarketUpdateMessage extends WebSocketMessage {
  type: 'market_update';
  data: Record<string, { price: number; change: number }>;
}

export type WebSocketMessageType = 
  | ChatWebSocketMessage 
  | ChatResponseMessage 
  | SystemMessage 
  | MarketUpdateMessage;

export interface WebSocketConfig {
  url: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
}

export interface WebSocketCallbacks {
  onMessage?: (message: WebSocketMessageType) => void;
  onChatResponse?: (response: ChatResponseMessage) => void;
  onSystemMessage?: (message: SystemMessage) => void;
  onMarketUpdate?: (update: MarketUpdateMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onReconnect?: () => void;
  onError?: (error: Event) => void;
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private callbacks: WebSocketCallbacks;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private isManuallyDisconnected = false;
  private token: string | null = null;

  constructor(config: WebSocketConfig, callbacks: WebSocketCallbacks = {}) {
    this.config = {
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      ...config
    };
    this.callbacks = callbacks;
  }

  /**
   * Connect to WebSocket server
   */
  public connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.CONNECTING)) {
        reject(new Error('Connection already in progress'));
        return;
      }

      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.token = token;
      this.isConnecting = true;
      this.isManuallyDisconnected = false;

      try {
        // Add token as query parameter for authentication
        const wsUrl = `${this.config.url}?token=${encodeURIComponent(token)}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.callbacks.onConnect?.();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.isConnecting = false;
          this.stopHeartbeat();
          this.callbacks.onDisconnect?.();

          // Attempt reconnection if not manually disconnected
          if (!this.isManuallyDisconnected && event.code !== 1008) { // 1008 = policy violation (auth failed)
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          this.callbacks.onError?.(error);
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    this.isManuallyDisconnected = true;
    this.clearReconnectTimer();
    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  /**
   * Send chat message
   */
  public sendChatMessage(message: string, analysisData?: any): boolean {
    const chatMessage: ChatWebSocketMessage = {
      type: 'chat_message',
      message,
      analysis_data: analysisData,
      timestamp: new Date().toISOString()
    };

    return this.sendMessage(chatMessage);
  }

  /**
   * Send generic message
   */
  public sendMessage(message: WebSocketMessageType): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected. Message not sent:', message);
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      return false;
    }
  }

  /**
   * Get connection status
   */
  public getConnectionStatus(): {
    connected: boolean;
    connecting: boolean;
    readyState: number | null;
  } {
    return {
      connected: this.ws?.readyState === WebSocket.OPEN,
      connecting: this.isConnecting,
      readyState: this.ws?.readyState ?? null
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessageType = JSON.parse(event.data);
      
      // Call generic message callback
      this.callbacks.onMessage?.(message);

      // Call specific callbacks based on message type
      switch (message.type) {
        case 'chat_response':
          this.callbacks.onChatResponse?.(message as ChatResponseMessage);
          break;
        case 'system_message':
        case 'connection_status':
        case 'error':
          this.callbacks.onSystemMessage?.(message as SystemMessage);
          break;
        case 'market_update':
          this.callbacks.onMarketUpdate?.(message as MarketUpdateMessage);
          break;
        default:
          console.log('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.clearReconnectTimer();
    
    const delay = this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts); // Exponential backoff
    console.log(`Scheduling reconnection attempt ${this.reconnectAttempts + 1} in ${delay}ms`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.reconnect();
    }, delay);
  }

  /**
   * Attempt to reconnect
   */
  private async reconnect(): Promise<void> {
    if (this.isManuallyDisconnected || !this.token) {
      return;
    }

    console.log(`Reconnection attempt ${this.reconnectAttempts}`);

    try {
      await this.connect(this.token);
      console.log('Reconnection successful');
      this.callbacks.onReconnect?.();
    } catch (error) {
      console.error('Reconnection failed:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Clear reconnection timer
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        // Send ping message
        this.sendMessage({
          type: 'ping',
          timestamp: new Date().toISOString()
        } as WebSocketMessageType);
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}

/**
 * Create WebSocket service instance for chat
 */
export const createChatWebSocketService = (callbacks: WebSocketCallbacks): WebSocketService => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = process.env.REACT_APP_WS_URL || `${wsProtocol}//${window.location.host}`;
  const wsUrl = `${wsHost}/api/v1/ws/chat`;

  return new WebSocketService(
    {
      url: wsUrl,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000
    },
    callbacks
  );
};

/**
 * Create WebSocket service instance for market updates
 */
export const createMarketWebSocketService = (callbacks: WebSocketCallbacks): WebSocketService => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = process.env.REACT_APP_WS_URL || `${wsProtocol}//${window.location.host}`;
  const wsUrl = `${wsHost}/api/v1/ws/market-updates`;

  return new WebSocketService(
    {
      url: wsUrl,
      reconnectInterval: 5000,
      maxReconnectAttempts: 3,
      heartbeatInterval: 60000
    },
    callbacks
  );
};