// Voice command processing service for stock queries and navigation

export interface VoiceCommand {
  type: 'stock_query' | 'navigation' | 'action' | 'unknown';
  intent: string;
  parameters: Record<string, any>;
  confidence: number;
  originalText: string;
}

export interface StockQueryCommand extends VoiceCommand {
  type: 'stock_query';
  parameters: {
    symbol?: string;
    company?: string;
    analysisType?: 'fundamental' | 'technical' | 'sentiment' | 'combined';
    action?: 'analyze' | 'price' | 'news' | 'compare';
  };
}

export interface NavigationCommand extends VoiceCommand {
  type: 'navigation';
  parameters: {
    destination: 'chat' | 'alerts' | 'education' | 'watchlist';
  };
}

export interface ActionCommand extends VoiceCommand {
  type: 'action';
  parameters: {
    action: 'clear_chat' | 'repeat_last' | 'stop_speaking' | 'help';
  };
}

class VoiceCommandProcessor {
  private stockSymbolPatterns = [
    // Direct symbol patterns - match 1-5 uppercase letters as word boundaries
    /\b([A-Z]{1,5})\b/g,
    // "Stock symbol X" patterns
    /(?:stock\s+symbol\s+|symbol\s+)([A-Z]{1,5})/gi,
    // "Ticker X" patterns
    /(?:ticker\s+)([A-Z]{1,5})/gi,
  ];

  private companyNamePatterns = [
    // Common company names and their symbols
    { names: ['apple', 'apple inc', 'apple incorporated'], symbol: 'AAPL' },
    { names: ['microsoft', 'microsoft corp', 'microsoft corporation'], symbol: 'MSFT' },
    { names: ['google', 'alphabet', 'alphabet inc'], symbol: 'GOOGL' },
    { names: ['amazon', 'amazon.com', 'amazon inc'], symbol: 'AMZN' },
    { names: ['tesla', 'tesla inc', 'tesla motors'], symbol: 'TSLA' },
    { names: ['meta', 'facebook', 'meta platforms'], symbol: 'META' },
    { names: ['netflix', 'netflix inc'], symbol: 'NFLX' },
    { names: ['nvidia', 'nvidia corp', 'nvidia corporation'], symbol: 'NVDA' },
    { names: ['intel', 'intel corp', 'intel corporation'], symbol: 'INTC' },
    { names: ['amd', 'advanced micro devices'], symbol: 'AMD' },
    { names: ['disney', 'walt disney', 'disney company'], symbol: 'DIS' },
    { names: ['coca cola', 'coca-cola', 'coke'], symbol: 'KO' },
    { names: ['pepsi', 'pepsico'], symbol: 'PEP' },
    { names: ['walmart', 'wal-mart'], symbol: 'WMT' },
    { names: ['target', 'target corp'], symbol: 'TGT' },
    { names: ['home depot', 'homedepot'], symbol: 'HD' },
    { names: ['mcdonalds', 'mcdonald\'s'], symbol: 'MCD' },
    { names: ['starbucks'], symbol: 'SBUX' },
    { names: ['boeing'], symbol: 'BA' },
    { names: ['general electric', 'ge'], symbol: 'GE' },
  ];

  private analysisTypePatterns = [
    { keywords: ['fundamental', 'fundamentals', 'financial', 'ratios', 'earnings'], type: 'fundamental' },
    { keywords: ['technical', 'chart', 'indicators', 'moving average', 'rsi', 'macd'], type: 'technical' },
    { keywords: ['sentiment', 'news', 'social', 'opinion', 'buzz'], type: 'sentiment' },
    { keywords: ['analysis', 'analyze', 'complete', 'full', 'comprehensive'], type: 'combined' },
  ];

  private actionPatterns = [
    { keywords: ['analyze', 'analysis', 'tell me about', 'what about', 'how is'], action: 'analyze' },
    { keywords: ['price', 'cost', 'value', 'worth', 'trading at'], action: 'price' },
    { keywords: ['news', 'latest', 'recent', 'updates'], action: 'news' },
    { keywords: ['compare', 'versus', 'vs', 'against'], action: 'compare' },
  ];

  private navigationPatterns = [
    { keywords: ['chat', 'conversation', 'talk'], destination: 'chat' },
    { keywords: ['alerts', 'notifications', 'warnings'], destination: 'alerts' },
    { keywords: ['education', 'learn', 'tutorial', 'help'], destination: 'education' },
    { keywords: ['watchlist', 'watch list', 'favorites'], destination: 'watchlist' },
  ];

  private actionCommandPatterns = [
    { keywords: ['clear chat', 'reset chat', 'start over'], action: 'clear_chat' },
    { keywords: ['repeat', 'say again', 'again'], action: 'repeat_last' },
    { keywords: ['stop talking', 'stop speaking', 'quiet', 'silence'], action: 'stop_speaking' },
    { keywords: ['help', 'commands', 'what can you do'], action: 'help' },
  ];

  processCommand(text: string, confidence: number = 1): VoiceCommand {
    const normalizedText = text.toLowerCase().trim();
    
    // Check for action commands first (more specific)
    const actionCommand = this.detectAction(normalizedText);
    if (actionCommand) {
      return {
        type: 'action',
        intent: 'execute_action',
        parameters: actionCommand,
        confidence,
        originalText: text,
      };
    }

    // Check for navigation commands
    const navigationCommand = this.detectNavigation(normalizedText);
    if (navigationCommand) {
      return {
        type: 'navigation',
        intent: 'navigate',
        parameters: navigationCommand,
        confidence,
        originalText: text,
      };
    }

    // Check for stock queries
    const stockQuery = this.detectStockQuery(normalizedText);
    if (stockQuery) {
      return {
        type: 'stock_query',
        intent: 'analyze_stock',
        parameters: stockQuery,
        confidence,
        originalText: text,
      };
    }

    // Default to unknown command
    return {
      type: 'unknown',
      intent: 'unknown',
      parameters: {},
      confidence,
      originalText: text,
    };
  }

  private detectStockQuery(text: string): Record<string, any> | null {
    const result: Record<string, any> = {};

    // Try to extract stock symbol
    const symbol = this.extractStockSymbol(text);
    if (symbol) {
      result.symbol = symbol;
    }

    // Try to extract company name
    const company = this.extractCompanyName(text);
    if (company) {
      result.company = company.name;
      result.symbol = company.symbol;
    }

    // Extract analysis type
    const analysisType = this.extractAnalysisType(text);
    if (analysisType) {
      result.analysisType = analysisType;
    }

    // Extract action
    const action = this.extractAction(text);
    if (action) {
      result.action = action;
    }

    // If we found a symbol or company, it's likely a stock query
    if (result.symbol || result.company) {
      return result;
    }

    // Check for general stock-related keywords
    const stockKeywords = ['stock', 'share', 'equity', 'ticker', 'company', 'investment'];
    const hasStockKeyword = stockKeywords.some(keyword => text.includes(keyword));
    
    if (hasStockKeyword && (result.analysisType || result.action)) {
      return result;
    }

    // Don't classify random text as stock queries
    if (!result.symbol && !result.company && !hasStockKeyword) {
      return null;
    }

    return result.symbol || result.company ? result : null;
  }

  private extractStockSymbol(text: string): string | null {
    // Convert to uppercase for pattern matching
    const upperText = text.toUpperCase();
    
    // Common stock symbols to validate against
    const commonSymbols = ['AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA', 'INTC', 'AMD', 'DIS', 'KO', 'PEP', 'WMT', 'TGT', 'HD', 'MCD', 'SBUX', 'BA', 'GE'];
    
    for (const pattern of this.stockSymbolPatterns) {
      // Reset the regex lastIndex to avoid issues with global flag
      pattern.lastIndex = 0;
      const matches = upperText.match(pattern);
      if (matches) {
        // Return the first valid-looking symbol (1-5 uppercase letters)
        for (const match of matches) {
          const symbol = match.replace(/[^A-Z]/g, '');
          if (symbol.length >= 1 && symbol.length <= 5) {
            // For testing purposes, accept common symbols or symbols in context
            if (commonSymbols.includes(symbol) || this.hasStockContext(text)) {
              return symbol;
            }
          }
        }
      }
    }
    return null;
  }

  private hasStockContext(text: string): boolean {
    const stockContextWords = ['analyze', 'stock', 'price', 'company', 'ticker', 'symbol', 'share', 'investment'];
    return stockContextWords.some(word => text.toLowerCase().includes(word));
  }

  private extractCompanyName(text: string): { name: string; symbol: string } | null {
    for (const company of this.companyNamePatterns) {
      for (const name of company.names) {
        if (text.includes(name.toLowerCase())) {
          return { name, symbol: company.symbol };
        }
      }
    }
    return null;
  }

  private extractAnalysisType(text: string): string | null {
    for (const pattern of this.analysisTypePatterns) {
      for (const keyword of pattern.keywords) {
        if (text.includes(keyword)) {
          return pattern.type;
        }
      }
    }
    return null;
  }

  private extractAction(text: string): string | null {
    // Check for more specific actions first (price, news, compare)
    const specificActions = [
      { keywords: ['price', 'cost', 'value', 'worth', 'trading at'], action: 'price' },
      { keywords: ['news', 'latest', 'recent', 'updates'], action: 'news' },
      { keywords: ['compare', 'versus', 'vs', 'against'], action: 'compare' },
    ];
    
    for (const pattern of specificActions) {
      for (const keyword of pattern.keywords) {
        if (text.includes(keyword)) {
          return pattern.action;
        }
      }
    }
    
    // Then check for general analyze action
    const analyzeKeywords = ['analyze', 'analysis', 'tell me about', 'what about', 'how is'];
    for (const keyword of analyzeKeywords) {
      if (text.includes(keyword)) {
        return 'analyze';
      }
    }
    
    return null;
  }

  private detectNavigation(text: string): Record<string, any> | null {
    for (const pattern of this.navigationPatterns) {
      for (const keyword of pattern.keywords) {
        if (text.includes(keyword)) {
          return { destination: pattern.destination };
        }
      }
    }
    return null;
  }

  private detectAction(text: string): Record<string, any> | null {
    // Check for exact phrase matches first
    for (const pattern of this.actionCommandPatterns) {
      for (const keyword of pattern.keywords) {
        if (text.includes(keyword)) {
          return { action: pattern.action };
        }
      }
    }
    return null;
  }

  // Convert voice command to chat message
  convertToMessage(command: VoiceCommand): string {
    switch (command.type) {
      case 'stock_query':
        return this.buildStockQueryMessage(command as StockQueryCommand);
      case 'navigation':
        return this.buildNavigationMessage(command as NavigationCommand);
      case 'action':
        return this.buildActionMessage(command as ActionCommand);
      default:
        return command.originalText;
    }
  }

  private buildStockQueryMessage(command: StockQueryCommand): string {
    const { symbol, company, analysisType, action } = command.parameters;
    
    let message = '';
    
    if (action === 'price') {
      message = `What's the current price of ${symbol || company}?`;
    } else if (action === 'news') {
      message = `Show me recent news for ${symbol || company}`;
    } else if (action === 'compare') {
      message = `Compare ${symbol || company} with similar stocks`;
    } else {
      // Default to analysis
      const target = symbol || company || 'the stock';
      const type = analysisType ? ` ${analysisType}` : '';
      message = `Analyze${type} ${target}`;
    }
    
    return message;
  }

  private buildNavigationMessage(command: NavigationCommand): string {
    const { destination } = command.parameters;
    return `Navigate to ${destination}`;
  }

  private buildActionMessage(command: ActionCommand): string {
    const { action } = command.parameters;
    
    switch (action) {
      case 'clear_chat':
        return 'Clear the chat';
      case 'repeat_last':
        return 'Repeat the last response';
      case 'stop_speaking':
        return 'Stop speaking';
      case 'help':
        return 'Show me what voice commands I can use';
      default:
        return command.originalText;
    }
  }

  // Get help text for voice commands
  getHelpText(): string {
    return `
Voice Commands Help:

Stock Queries:
• "Analyze Apple" or "Analyze AAPL"
• "What's the price of Tesla?"
• "Show me technical analysis for Microsoft"
• "Get fundamental data for GOOGL"
• "What's the news on Amazon?"

Navigation:
• "Go to alerts"
• "Show education"
• "Open chat"

Actions:
• "Clear chat"
• "Stop speaking"
• "Help" or "What can you do?"

You can also speak naturally, like:
• "Tell me about Apple's stock performance"
• "How is Tesla doing today?"
• "What do you think about Microsoft?"
    `.trim();
  }
}

export const voiceCommandProcessor = new VoiceCommandProcessor();