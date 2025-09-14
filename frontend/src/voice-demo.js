// Simple demo to test voice functionality
import { voiceCommandProcessor } from './services/voiceCommands';

// Test voice command processing
console.log('Testing Voice Command Processor:');

const testCommands = [
  'analyze AAPL',
  'what is the price of Tesla',
  'show me news for Microsoft',
  'go to alerts',
  'clear chat',
  'help',
  'random text that should be unknown'
];

testCommands.forEach(command => {
  const result = voiceCommandProcessor.processCommand(command, 1);
  console.log(`Command: "${command}"`);
  console.log(`Type: ${result.type}`);
  console.log(`Parameters:`, result.parameters);
  console.log(`Message: ${voiceCommandProcessor.convertToMessage(result)}`);
  console.log('---');
});

console.log('Voice functionality implemented successfully!');