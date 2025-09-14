import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const theme = createTheme();

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };

// Mock data factories for testing
export const createMockChatMessage = (overrides = {}) => ({
  id: 'test-message-1',
  type: 'user' as const,
  content: 'Test message',
  timestamp: new Date('2024-01-01T12:00:00Z'),
  ...overrides,
});

export const createMockStockData = (overrides = {}) => ({
  symbol: 'AAPL',
  name: 'Apple Inc.',
  price: 150.00,
  change: 2.50,
  changePercent: 1.69,
  volume: 50000000,
  marketCap: 2500000000000,
  ...overrides,
});

export const createMockAnalysisResult = (overrides = {}) => ({
  symbol: 'AAPL',
  recommendation: 'BUY' as const,
  confidence: 85,
  reasoning: ['Strong fundamentals', 'Positive technical indicators'],
  risks: ['Market volatility', 'Sector rotation'],
  targets: {
    shortTerm: 160.00,
    mediumTerm: 180.00,
    longTerm: 200.00,
  },
  timestamp: new Date('2024-01-01T12:00:00Z'),
  ...overrides,
});

export const createMockWatchlist = (overrides = {}) => ({
  id: 'test-watchlist-1',
  name: 'Test Watchlist',
  description: 'A test watchlist',
  items: [],
  createdAt: new Date('2024-01-01T12:00:00Z'),
  updatedAt: new Date('2024-01-01T12:00:00Z'),
  ...overrides,
});

export const createMockAlert = (overrides = {}) => ({
  id: 'test-alert-1',
  symbol: 'AAPL',
  type: 'price_above' as const,
  conditionValue: 200.00,
  message: 'AAPL reached target price',
  isActive: true,
  createdAt: new Date('2024-01-01T12:00:00Z'),
  ...overrides,
});

// Mock API responses
export const mockApiResponse = <T>(data: T, delay = 0) => {
  return new Promise<T>((resolve) => {
    setTimeout(() => resolve(data), delay);
  });
};

export const mockApiError = (message = 'API Error', status = 500, delay = 0) => {
  return new Promise((_, reject) => {
    setTimeout(() => {
      const error = new Error(message);
      (error as any).status = status;
      reject(error);
    }, delay);
  });
};

// Test helpers
export const waitForLoadingToFinish = () => {
  return new Promise((resolve) => setTimeout(resolve, 0));
};

export const createMockIntersectionObserver = () => {
  const mockIntersectionObserver = jest.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  window.IntersectionObserver = mockIntersectionObserver;
  return mockIntersectionObserver;
};

export const createMockResizeObserver = () => {
  const mockResizeObserver = jest.fn();
  mockResizeObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  window.ResizeObserver = mockResizeObserver;
  return mockResizeObserver;
};