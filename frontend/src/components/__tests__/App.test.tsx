import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render, createMockChatMessage } from '../../test-utils';
import App from '../../App';

// Mock the services
jest.mock('../../services/api', () => ({
  stockApi: {
    getStock: jest.fn(),
    searchStocks: jest.fn(),
  },
  chatApi: {
    sendMessage: jest.fn(),
  },
  authApi: {
    login: jest.fn(),
    register: jest.fn(),
    getProfile: jest.fn(),
  },
}));

jest.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    isConnected: true,
    sendMessage: jest.fn(),
    lastMessage: null,
  }),
}));

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders main application layout', () => {
    render(<App />);
    
    expect(screen.getByText('Settlers of Stock')).toBeInTheDocument();
    expect(screen.getByText('Welcome to Settlers of Stock!')).toBeInTheDocument();
  });

  it('displays navigation tabs', () => {
    render(<App />);
    
    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByText('Watchlists')).toBeInTheDocument();
    expect(screen.getByText('Alerts')).toBeInTheDocument();
    expect(screen.getByText('Education')).toBeInTheDocument();
  });

  it('switches between tabs correctly', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Initially on Chat tab
    expect(screen.getByText('Welcome to Settlers of Stock!')).toBeInTheDocument();
    
    // Switch to Watchlists tab
    await user.click(screen.getByText('Watchlists'));
    await waitFor(() => {
      expect(screen.getByText('Your Watchlists')).toBeInTheDocument();
    });
    
    // Switch to Alerts tab
    await user.click(screen.getByText('Alerts'));
    await waitFor(() => {
      expect(screen.getByText('Price Alerts')).toBeInTheDocument();
    });
    
    // Switch to Education tab
    await user.click(screen.getByText('Education'));
    await waitFor(() => {
      expect(screen.getByText('Learn About Investing')).toBeInTheDocument();
    });
  });

  it('handles responsive design', () => {
    // Mock window.matchMedia for responsive testing
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query.includes('max-width: 600px'),
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });

    render(<App />);
    
    // Should render mobile-friendly layout
    expect(screen.getByRole('main')).toBeInTheDocument();
  });

  it('displays disclaimer banner', () => {
    render(<App />);
    
    expect(screen.getByText(/This application is for educational purposes only/)).toBeInTheDocument();
  });

  it('handles error boundary', () => {
    // Mock console.error to avoid error output in tests
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    const ThrowError = () => {
      throw new Error('Test error');
    };
    
    render(
      <App>
        <ThrowError />
      </App>
    );
    
    // Should display error fallback UI
    expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
    
    consoleSpy.mockRestore();
  });
});