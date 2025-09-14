import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import App from './App';

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </QueryClientProvider>
  );
};

test('renders Settlers of Stock title', () => {
  renderWithProviders(<App />);
  const titleElement = screen.getByRole('heading', { level: 1 });
  expect(titleElement).toHaveTextContent('Settlers of Stock');
});

test('renders welcome message', () => {
  renderWithProviders(<App />);
  const welcomeElement = screen.getByText(/Welcome to Settlers of Stock/i);
  expect(welcomeElement).toBeInTheDocument();
});