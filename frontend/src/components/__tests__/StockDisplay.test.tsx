import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import StockDisplay from '../StockDisplay';
import { StockLookupResponse } from '../../services/api';

const theme = createTheme();

const mockStockData: StockLookupResponse = {
  stock: {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    exchange: 'NASDAQ',
    sector: 'Technology',
    industry: 'Consumer Electronics',
    marketCap: 3000000000000,
    lastUpdated: '2024-01-15T10:30:00Z'
  },
  market_data: {
    symbol: 'AAPL',
    price: 150.25,
    change: 2.50,
    changePercent: 1.69,
    volume: 75000000,
    high52Week: 180.00,
    low52Week: 120.00,
    avgVolume: 80000000,
    marketCap: 2500000000000,
    peRatio: 25.5,
    timestamp: '2024-01-15T15:30:00Z',
    isStale: false
  }
};

const mockStockDataNegative: StockLookupResponse = {
  ...mockStockData,
  market_data: {
    ...mockStockData.market_data,
    change: -2.50,
    changePercent: -1.69
  }
};

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('StockDisplay', () => {
  it('renders stock information correctly', () => {
    renderWithTheme(<StockDisplay stockData={mockStockData} />);
    
    // Check basic stock info
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    expect(screen.getByText('NASDAQ')).toBeInTheDocument();
    expect(screen.getByText('Technology')).toBeInTheDocument();
  });

  it('displays price information correctly', () => {
    renderWithTheme(<StockDisplay stockData={mockStockData} />);
    
    // Check price formatting
    expect(screen.getByText('$150.25')).toBeInTheDocument();
    // Check for parts of the change text since it's split across elements
    expect(screen.getByText('$2.50')).toBeInTheDocument();
    expect(screen.getByText('+1.69%')).toBeInTheDocument();
  });

  it('displays negative price changes correctly', () => {
    renderWithTheme(<StockDisplay stockData={mockStockDataNegative} />);
    
    // Check negative price formatting - text is split across elements
    expect(screen.getByText('-$2.50')).toBeInTheDocument();
    expect(screen.getByText('-1.69%')).toBeInTheDocument();
  });

  it('displays market data correctly', () => {
    renderWithTheme(<StockDisplay stockData={mockStockData} />);
    
    // Check volume formatting
    expect(screen.getByText('75.00M')).toBeInTheDocument();
    expect(screen.getByText('80.00M')).toBeInTheDocument(); // Avg volume
    
    // Check market cap formatting
    expect(screen.getByText('$2.50T')).toBeInTheDocument();
    
    // Check P/E ratio
    expect(screen.getByText('25.50')).toBeInTheDocument();
  });

  it('displays 52-week range correctly', () => {
    renderWithTheme(<StockDisplay stockData={mockStockData} />);
    
    expect(screen.getByText('52-Week Range')).toBeInTheDocument();
    expect(screen.getByText('$120.00')).toBeInTheDocument();
    expect(screen.getByText('$180.00')).toBeInTheDocument();
  });

  it('shows stale data indicator when data is cached', () => {
    const staleData = {
      ...mockStockData,
      market_data: {
        ...mockStockData.market_data,
        isStale: true
      }
    };
    
    renderWithTheme(<StockDisplay stockData={staleData} />);
    
    expect(screen.getByText('Cached Data')).toBeInTheDocument();
  });

  it('handles missing optional data gracefully', () => {
    const minimalData: StockLookupResponse = {
      stock: {
        symbol: 'TEST',
        name: 'Test Company',
        exchange: 'NYSE',
        lastUpdated: '2024-01-15T10:30:00Z'
      },
      market_data: {
        symbol: 'TEST',
        price: 100.00,
        change: 0,
        changePercent: 0,
        volume: 1000000,
        timestamp: '2024-01-15T15:30:00Z'
      }
    };
    
    renderWithTheme(<StockDisplay stockData={minimalData} />);
    
    expect(screen.getByText('TEST')).toBeInTheDocument();
    expect(screen.getByText('Test Company')).toBeInTheDocument();
    expect(screen.getByText('$100.00')).toBeInTheDocument();
  });

  it('formats large numbers correctly', () => {
    const largeNumberData = {
      ...mockStockData,
      market_data: {
        ...mockStockData.market_data,
        volume: 1500000000, // 1.5B
        marketCap: 5000000000000 // 5T
      }
    };
    
    renderWithTheme(<StockDisplay stockData={largeNumberData} />);
    
    expect(screen.getByText('1.50B')).toBeInTheDocument();
    expect(screen.getByText('$5.00T')).toBeInTheDocument();
  });

  it('displays timestamp correctly', () => {
    renderWithTheme(<StockDisplay stockData={mockStockData} />);
    
    // Check that timestamp is displayed (exact format may vary by locale)
    expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
  });
});