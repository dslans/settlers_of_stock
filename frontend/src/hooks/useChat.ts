import { useState, useCallback, useEffect } from 'react';
import { ChatMessage } from '../types';
import { StockLookupResponse } from '../services/api';
import { useStockLookup } from './useStockLookup';
import { useChatWebSocket } from './useWebSocket';
import { ChatResponseMessage, SystemMessage } from '../services/websocket';
import { educationService, EducationalConceptSummary } from '../services/education';

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  connected: boolean;
  connecting: boolean;
  connectionError: string | null;
  sendMessage: (content: string) => void;
  clearMessages: () => void;
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  currentStockData: StockLookupResponse | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  educationalSuggestions: EducationalConceptSummary[];
}

export const useChat = (): UseChatReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [educationalSuggestions, setEducationalSuggestions] = useState<EducationalConceptSummary[]>([]);
  const { 
    lookupStock, 
    stockData, 
    error: stockError,
    isLoading: stockLoading 
  } = useStockLookup();

  // WebSocket integration
  const {
    connected,
    connecting,
    error: connectionError,
    connect: connectWs,
    disconnect: disconnectWs,
    sendMessage: sendWsMessage
  } = useChatWebSocket({
    autoConnect: true,
    onChatResponse: handleChatResponse,
    onSystemMessage: handleSystemMessage,
    onConnectionChange: handleConnectionChange
  });

  const generateMessageId = (): string => {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  // Get educational suggestions based on chat content
  const getEducationalSuggestionsForMessage = useCallback(async (
    content: string, 
    stockSymbol?: string
  ) => {
    try {
      const suggestions = await educationService.getContextualSuggestions(content, stockSymbol);
      setEducationalSuggestions(suggestions);
    } catch (error) {
      console.warn('Failed to get educational suggestions:', error);
    }
  }, []);

  // Handle chat responses from WebSocket
  function handleChatResponse(response: ChatResponseMessage) {
    const botMessage: ChatMessage = {
      id: generateMessageId(),
      type: 'assistant',
      content: response.message,
      timestamp: new Date(response.timestamp),
      metadata: {
        analysisData: response.analysis_data,
        suggestions: response.suggestions,
        requiresFollowUp: response.requires_follow_up,
        stockSymbol: response.analysis_data?.symbol
      }
    };

    setMessages(prev => [...prev, botMessage]);
    setIsLoading(false);

    // Get educational suggestions based on the response content
    getEducationalSuggestionsForMessage(response.message, response.analysis_data?.symbol);
  }

  // Handle system messages from WebSocket
  function handleSystemMessage(message: SystemMessage) {
    if (message.type === 'error') {
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: generateMessageId(),
        type: 'system',
        content: `Error: ${message.message}`,
        timestamp: new Date(message.timestamp),
        metadata: {
          errorCode: message.error_code,
          level: 'error'
        }
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsLoading(false);
    } else if (message.type === 'connection_status' && message.status === 'connected') {
      // Add welcome message when connected
      const welcomeMessage: ChatMessage = {
        id: generateMessageId(),
        type: 'system',
        content: `🔗 ${message.message}`,
        timestamp: new Date(message.timestamp),
        metadata: {
          level: 'info'
        }
      };
      setMessages(prev => [...prev, welcomeMessage]);
    }
  }

  // Handle connection state changes
  function handleConnectionChange(isConnected: boolean) {
    if (!isConnected && messages.length > 0) {
      // Add disconnection notice
      const disconnectMessage: ChatMessage = {
        id: generateMessageId(),
        type: 'system',
        content: '⚠️ Connection lost. Attempting to reconnect...',
        timestamp: new Date(),
        metadata: {
          level: 'warning'
        }
      };
      setMessages(prev => [...prev, disconnectMessage]);
    }
  }

  const addMessage = useCallback((message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: generateMessageId(),
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, newMessage]);
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading || stockLoading) return;

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: generateMessageId(),
      type: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Check if the message contains a stock symbol request
      const stockSymbol = extractStockSymbol(content);
      let analysisData = null;

      // If it's a stock lookup request, get the data first
      if (stockSymbol && isStockLookupRequest(content)) {
        try {
          const stockData = await lookupStock(stockSymbol);
          if (stockData) {
            analysisData = {
              symbol: stockSymbol,
              stock_data: stockData
            };
          }
        } catch (error) {
          console.warn('Failed to fetch stock data for WebSocket message:', error);
        }
      }

      // Try to send via WebSocket first
      if (connected) {
        const sent = sendWsMessage(content, analysisData);
        if (!sent) {
          throw new Error('Failed to send message via WebSocket');
        }
        // WebSocket response will be handled by handleChatResponse
      } else {
        // Fallback to original logic if WebSocket not connected
        if (stockSymbol && isStockLookupRequest(content)) {
          await handleStockLookupRequest(content, stockSymbol);
        } else {
          await simulateApiResponse(content);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: generateMessageId(),
        type: 'system',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
      setIsLoading(false);
    }
  }, [isLoading, stockLoading, lookupStock, connected, sendWsMessage]);

  // Check if the user input is requesting stock lookup
  const isStockLookupRequest = (input: string): boolean => {
    const lookupKeywords = [
      'analyze', 'analysis', 'lookup', 'look up', 'check', 'show me',
      'what is', 'whats', 'tell me about', 'info', 'information',
      'price', 'stock', 'quote', 'data'
    ];
    
    const lowerInput = input.toLowerCase();
    return lookupKeywords.some(keyword => lowerInput.includes(keyword));
  };

  // Handle stock lookup request with real API
  const handleStockLookupRequest = async (userInput: string, symbol: string): Promise<void> => {
    try {
      const stockData = await lookupStock(symbol);
      
      if (stockData) {
        // Generate response based on real stock data
        const responseContent = generateStockAnalysisResponse(stockData, userInput);
        
        const assistantMessage: ChatMessage = {
          id: generateMessageId(),
          type: 'assistant',
          content: responseContent,
          timestamp: new Date(),
          metadata: {
            stockSymbol: symbol,
            analysisType: 'combined',
          },
        };

        setMessages(prev => [...prev, assistantMessage]);
        
        // Get educational suggestions for the response
        getEducationalSuggestionsForMessage(responseContent, symbol);
      } else {
        throw new Error('Failed to fetch stock data');
      }
    } catch (error: any) {
      // Handle stock lookup error
      const errorContent = stockError || error.message || 'Failed to lookup stock data';
      
      const errorMessage: ChatMessage = {
        id: generateMessageId(),
        type: 'assistant',
        content: `I'm sorry, I couldn't find information for "${symbol}". ${errorContent}

Please try:
• Checking the symbol spelling (e.g., AAPL for Apple)
• Using the full ticker symbol
• Asking about a different stock

You can ask me things like:
• "Analyze AAPL"
• "Show me Tesla stock info"
• "What's the price of Microsoft?"`,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    }
  };

  // Generate analysis response from real stock data
  const generateStockAnalysisResponse = (stockData: StockLookupResponse, userInput: string): string => {
    const { stock, market_data } = stockData;
    
    const formatPrice = (price: number) => 
      new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(price);
    
    const formatPercent = (percent: number) => {
      const sign = percent >= 0 ? '+' : '';
      return `${sign}${percent.toFixed(2)}%`;
    };
    
    const formatNumber = (num: number) => {
      if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
      if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
      if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
      return `$${num.toLocaleString()}`;
    };

    const changeEmoji = market_data.change >= 0 ? '📈' : '📉';
    const trendEmoji = market_data.change > 0 ? '🟢' : market_data.change < 0 ? '🔴' : '🟡';
    
    return `${changeEmoji} **${stock.name} (${stock.symbol})**

**Current Price**: ${formatPrice(market_data.price)} ${trendEmoji}
**Daily Change**: ${formatPrice(market_data.change)} (${formatPercent(market_data.changePercent)})
**Volume**: ${market_data.volume.toLocaleString()}
${market_data.marketCap ? `**Market Cap**: ${formatNumber(market_data.marketCap)}` : ''}
${market_data.peRatio ? `**P/E Ratio**: ${market_data.peRatio.toFixed(2)}` : ''}

**Company Info**:
• **Exchange**: ${stock.exchange}
${stock.sector ? `• **Sector**: ${stock.sector}` : ''}
${stock.industry ? `• **Industry**: ${stock.industry}` : ''}

${market_data.high52Week && market_data.low52Week ? 
`**52-Week Range**: ${formatPrice(market_data.low52Week)} - ${formatPrice(market_data.high52Week)}` : ''}

${market_data.isStale ? '⚠️ *Note: This data may be cached and not real-time*' : ''}

The stock data above shows the current market information. Would you like me to provide more detailed analysis, compare with other stocks, or explain any of these metrics?`;
  };

  // Simulate API response for non-stock requests
  const simulateApiResponse = async (userInput: string): Promise<void> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        let responseContent = '';
        
        // Simple pattern matching for demo purposes
        const input = userInput.toLowerCase();
        
        if (input.includes('aapl') || input.includes('apple')) {
          responseContent = `Here's what I found about Apple (AAPL):

📈 **Current Price**: $193.42 (+1.2%)
📊 **Analysis**: Strong fundamentals with solid revenue growth
🎯 **Recommendation**: BUY (Confidence: 85%)

**Key Points:**
• P/E Ratio: 28.5 (reasonable for tech)
• Strong cash position and dividend yield
• iPhone sales showing resilience
• Services revenue growing consistently

**Risks to Consider:**
• High valuation compared to market
• Regulatory pressure in EU markets
• Supply chain dependencies

Would you like me to dive deeper into any specific aspect of Apple's analysis?`;
        } else if (input.includes('tsla') || input.includes('tesla')) {
          responseContent = `Tesla (TSLA) Analysis:

📈 **Current Price**: $248.50 (-2.1%)
📊 **Analysis**: Mixed signals with high volatility
🎯 **Recommendation**: HOLD (Confidence: 65%)

**Key Points:**
• Leading EV market position
• Strong production growth trajectory  
• Expanding into energy storage and AI
• Innovative manufacturing processes

**Concerns:**
• High valuation multiples
• Increased competition in EV space
• Regulatory challenges in key markets
• Execution risk on ambitious timelines

The stock shows high beta - great for risk-tolerant investors but volatile.`;
        } else if (input.includes('market') || input.includes('spy') || input.includes('s&p')) {
          responseContent = `📊 **Market Overview (S&P 500)**:

**Current Sentiment**: Cautiously Optimistic
**Trend**: Sideways with upward bias
**Key Levels**: Support at 4,200, Resistance at 4,400

**Sector Performance**:
🟢 Technology: +2.1%
🟢 Healthcare: +1.8%  
🔴 Energy: -1.5%
🔴 Real Estate: -0.8%

**Market Drivers**:
• Fed policy expectations
• Earnings season results
• Geopolitical developments
• Economic data trends

**Risk Factors**:
• Interest rate uncertainty
• Inflation concerns
• Global supply chain issues

Would you like analysis on any specific sector or stock?`;
        } else {
          responseContent = `I understand you're asking about "${userInput}". 

I can help you with:
• **Stock Analysis** - Fundamental and technical analysis
• **Market Overview** - Sector performance and trends  
• **Investment Research** - Company financials and recommendations
• **Risk Assessment** - Portfolio and individual stock risks

Try asking about:
• "Analyze [STOCK SYMBOL]" 
• "What's the market sentiment?"
• "Compare AAPL vs MSFT"
• "Show me tech sector performance"

What specific analysis would you like me to provide?`;
        }

        const assistantMessage: ChatMessage = {
          id: generateMessageId(),
          type: 'assistant',
          content: responseContent,
          timestamp: new Date(),
          metadata: {
            stockSymbol: extractStockSymbol(userInput),
            analysisType: 'combined',
          },
        };

        setMessages(prev => [...prev, assistantMessage]);
        
        // Get educational suggestions for the response
        getEducationalSuggestionsForMessage(responseContent);
        
        resolve();
      }, 1500 + Math.random() * 1000); // Simulate 1.5-2.5s response time
    });
  };

  const extractStockSymbol = (input: string): string | undefined => {
    const symbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA'];
    const upperInput = input.toUpperCase();
    
    for (const symbol of symbols) {
      if (upperInput.includes(symbol)) {
        return symbol;
      }
    }
    
    // Check for company names
    if (input.toLowerCase().includes('apple')) return 'AAPL';
    if (input.toLowerCase().includes('tesla')) return 'TSLA';
    if (input.toLowerCase().includes('microsoft')) return 'MSFT';
    if (input.toLowerCase().includes('google') || input.toLowerCase().includes('alphabet')) return 'GOOGL';
    if (input.toLowerCase().includes('amazon')) return 'AMZN';
    if (input.toLowerCase().includes('meta') || input.toLowerCase().includes('facebook')) return 'META';
    if (input.toLowerCase().includes('nvidia')) return 'NVDA';
    
    return undefined;
  };

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Connect function
  const connect = useCallback(async () => {
    try {
      await connectWs();
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      // Add connection error message
      const errorMessage: ChatMessage = {
        id: generateMessageId(),
        type: 'system',
        content: '⚠️ Failed to establish real-time connection. Using fallback mode.',
        timestamp: new Date(),
        metadata: { level: 'warning' }
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  }, [connectWs]);

  // Disconnect function
  const disconnect = useCallback(() => {
    disconnectWs();
  }, [disconnectWs]);

  return {
    messages,
    isLoading: isLoading || stockLoading,
    connected,
    connecting,
    connectionError,
    sendMessage,
    clearMessages,
    addMessage,
    currentStockData: stockData,
    connect,
    disconnect,
    educationalSuggestions,
  };
};