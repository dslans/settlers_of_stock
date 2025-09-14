import { voiceCommandProcessor, VoiceCommand } from '../voiceCommands';

describe('VoiceCommandProcessor', () => {
  describe('Stock Query Detection', () => {
    it('should detect stock symbol queries', () => {
      const command = voiceCommandProcessor.processCommand('analyze AAPL', 1);
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('AAPL');
      expect(command.parameters.action).toBe('analyze');
    });

    it('should detect company name queries', () => {
      const command = voiceCommandProcessor.processCommand('tell me about Apple', 1);
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('AAPL');
      expect(command.parameters.company).toBe('apple');
    });

    it('should detect price queries', () => {
      const command = voiceCommandProcessor.processCommand('what is the price of Tesla', 1);
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('TSLA');
      expect(command.parameters.action).toBe('price');
    });

    it('should detect technical analysis queries', () => {
      const command = voiceCommandProcessor.processCommand('show me technical analysis for Microsoft', 1);
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('MSFT');
      expect(command.parameters.analysisType).toBe('technical');
    });

    it('should detect fundamental analysis queries', () => {
      const command = voiceCommandProcessor.processCommand('fundamental analysis of Google', 1);
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('GOOGL');
      expect(command.parameters.analysisType).toBe('fundamental');
    });

    it('should detect sentiment analysis queries', () => {
      const command = voiceCommandProcessor.processCommand('what is the sentiment for Amazon', 1);
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('AMZN');
      expect(command.parameters.analysisType).toBe('sentiment');
    });

    it('should detect news queries', () => {
      const command = voiceCommandProcessor.processCommand('show me news for Netflix', 1);
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('NFLX');
      expect(command.parameters.action).toBe('news');
    });

    it('should detect comparison queries', () => {
      const command = voiceCommandProcessor.processCommand('compare Meta with other stocks', 1);
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('META');
      expect(command.parameters.action).toBe('compare');
    });

    it('should handle multiple stock symbols and pick the first valid one', () => {
      const command = voiceCommandProcessor.processCommand('analyze AAPL and MSFT', 1);
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('AAPL');
    });

    it('should handle case-insensitive company names', () => {
      const command = voiceCommandProcessor.processCommand('ANALYZE APPLE INCORPORATED', 1);
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('AAPL');
    });
  });

  describe('Navigation Detection', () => {
    it('should detect chat navigation', () => {
      const command = voiceCommandProcessor.processCommand('go to chat', 1);
      
      expect(command.type).toBe('navigation');
      expect(command.parameters.destination).toBe('chat');
    });

    it('should detect alerts navigation', () => {
      const command = voiceCommandProcessor.processCommand('show me alerts', 1);
      
      expect(command.type).toBe('navigation');
      expect(command.parameters.destination).toBe('alerts');
    });

    it('should detect education navigation', () => {
      const command = voiceCommandProcessor.processCommand('open education', 1);
      
      expect(command.type).toBe('navigation');
      expect(command.parameters.destination).toBe('education');
    });

    it('should detect watchlist navigation', () => {
      const command = voiceCommandProcessor.processCommand('go to watchlist', 1);
      
      expect(command.type).toBe('navigation');
      expect(command.parameters.destination).toBe('watchlist');
    });
  });

  describe('Action Detection', () => {
    it('should detect clear chat action', () => {
      const command = voiceCommandProcessor.processCommand('clear chat', 1);
      
      expect(command.type).toBe('action');
      expect(command.parameters.action).toBe('clear_chat');
    });

    it('should detect repeat action', () => {
      const command = voiceCommandProcessor.processCommand('repeat that', 1);
      
      expect(command.type).toBe('action');
      expect(command.parameters.action).toBe('repeat_last');
    });

    it('should detect stop speaking action', () => {
      const command = voiceCommandProcessor.processCommand('stop talking', 1);
      
      expect(command.type).toBe('action');
      expect(command.parameters.action).toBe('stop_speaking');
    });

    it('should detect help action', () => {
      const command = voiceCommandProcessor.processCommand('what can you do', 1);
      
      expect(command.type).toBe('action');
      expect(command.parameters.action).toBe('help');
    });
  });

  describe('Unknown Commands', () => {
    it('should classify unrecognized commands as unknown', () => {
      const command = voiceCommandProcessor.processCommand('xyz random gibberish', 1);
      
      expect(command.type).toBe('unknown');
      expect(command.intent).toBe('unknown');
      expect(command.originalText).toBe('xyz random gibberish');
    });

    it('should preserve original text for unknown commands', () => {
      const originalText = 'this is some random text that should not match any patterns';
      const command = voiceCommandProcessor.processCommand(originalText, 1);
      
      expect(command.originalText).toBe(originalText);
    });
  });

  describe('Message Conversion', () => {
    it('should convert stock query to proper message', () => {
      const command: VoiceCommand = {
        type: 'stock_query',
        intent: 'analyze_stock',
        parameters: { symbol: 'AAPL', action: 'analyze' },
        confidence: 1,
        originalText: 'analyze Apple',
      };
      
      const message = voiceCommandProcessor.convertToMessage(command);
      expect(message).toBe('Analyze AAPL');
    });

    it('should convert price query to proper message', () => {
      const command: VoiceCommand = {
        type: 'stock_query',
        intent: 'analyze_stock',
        parameters: { symbol: 'TSLA', action: 'price' },
        confidence: 1,
        originalText: 'price of Tesla',
      };
      
      const message = voiceCommandProcessor.convertToMessage(command);
      expect(message).toBe('What\'s the current price of TSLA?');
    });

    it('should convert news query to proper message', () => {
      const command: VoiceCommand = {
        type: 'stock_query',
        intent: 'analyze_stock',
        parameters: { company: 'microsoft', action: 'news' },
        confidence: 1,
        originalText: 'news for Microsoft',
      };
      
      const message = voiceCommandProcessor.convertToMessage(command);
      expect(message).toBe('Show me recent news for microsoft');
    });

    it('should convert navigation command to proper message', () => {
      const command: VoiceCommand = {
        type: 'navigation',
        intent: 'navigate',
        parameters: { destination: 'alerts' },
        confidence: 1,
        originalText: 'go to alerts',
      };
      
      const message = voiceCommandProcessor.convertToMessage(command);
      expect(message).toBe('Navigate to alerts');
    });

    it('should convert action command to proper message', () => {
      const command: VoiceCommand = {
        type: 'action',
        intent: 'execute_action',
        parameters: { action: 'help' },
        confidence: 1,
        originalText: 'help',
      };
      
      const message = voiceCommandProcessor.convertToMessage(command);
      expect(message).toBe('Show me what voice commands I can use');
    });

    it('should return original text for unknown commands', () => {
      const command: VoiceCommand = {
        type: 'unknown',
        intent: 'unknown',
        parameters: {},
        confidence: 1,
        originalText: 'some random text',
      };
      
      const message = voiceCommandProcessor.convertToMessage(command);
      expect(message).toBe('some random text');
    });
  });

  describe('Complex Queries', () => {
    it('should handle complex stock analysis queries', () => {
      const command = voiceCommandProcessor.processCommand(
        'I want to see the fundamental analysis for Apple stock', 
        1
      );
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('AAPL');
      expect(command.parameters.analysisType).toBe('fundamental');
    });

    it('should handle natural language queries', () => {
      const command = voiceCommandProcessor.processCommand(
        'How is Tesla doing today?', 
        1
      );
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('TSLA');
    });

    it('should prioritize specific actions over general analysis', () => {
      const command = voiceCommandProcessor.processCommand(
        'What is the current price and analysis of Microsoft?', 
        1
      );
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('MSFT');
      expect(command.parameters.action).toBe('price'); // Price should be detected first
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty input', () => {
      const command = voiceCommandProcessor.processCommand('', 1);
      
      expect(command.type).toBe('unknown');
    });

    it('should handle whitespace-only input', () => {
      const command = voiceCommandProcessor.processCommand('   ', 1);
      
      expect(command.type).toBe('unknown');
    });

    it('should handle very long input', () => {
      const longText = 'analyze '.repeat(100) + 'AAPL';
      const command = voiceCommandProcessor.processCommand(longText, 1);
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('AAPL');
    });

    it('should handle mixed case input', () => {
      const command = voiceCommandProcessor.processCommand('AnAlYzE aPpLe', 1);
      
      expect(command.type).toBe('stock_query');
      expect(command.parameters.symbol).toBe('AAPL');
    });
  });

  describe('Help Text', () => {
    it('should provide comprehensive help text', () => {
      const helpText = voiceCommandProcessor.getHelpText();
      
      expect(helpText).toContain('Stock Queries');
      expect(helpText).toContain('Navigation');
      expect(helpText).toContain('Actions');
      expect(helpText).toContain('Analyze Apple');
      expect(helpText).toContain('Go to alerts');
      expect(helpText).toContain('Clear chat');
    });
  });
});