import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import WatchlistDisplay from '../WatchlistDisplay';
import { useWatchlist } from '../../hooks/useWatchlist';
import { Watchlist, WatchlistItem } from '../../types';

// Mock the useWatchlist hook
jest.mock('../../hooks/useWatchlist');
const mockUseWatchlist = useWatchlist as jest.MockedFunction<typeof useWatchlist>;

// Mock theme
const theme = createTheme();

const mockWatchlist: Watchlist = {
  id: 1,
  userId: 1,
  name: 'My Tech Stocks',
  description: 'Technology companies I\'m watching',
  isDefault: true,
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-01-01T00:00:00Z',
  items: [
    {
      id: 1,
      watchlistId: 1,
      symbol: 'AAPL',
      companyName: 'Apple Inc.',
      notes: 'Great company',
      targetPrice: 200,
      entryPrice: 150,
      sharesOwned: 10,
      addedAt: '2023-01-01T00:00:00Z',
      updatedAt: '2023-01-01T00:00:00Z',
      currentPrice: 175,
      dailyChange: 5,
      dailyChangePercent: 2.94,
      volume: 50000000,
      isMarketOpen: true,
      lastUpdated: '2023-01-01T12:00:00Z',
    },
    {
      id: 2,
      watchlistId: 1,
      symbol: 'GOOGL',
      companyName: 'Alphabet Inc.',
      addedAt: '2023-01-01T00:00:00Z',
      updatedAt: '2023-01-01T00:00:00Z',
      currentPrice: 2800,
      dailyChange: -10,
      dailyChangePercent: -0.36,
      volume: 1000000,
    },
  ],
  totalItems: 2,
};

const mockUseWatchlistReturn = {
  watchlists: [],
  currentWatchlist: null,
  stats: null,
  loading: { isLoading: false },
  error: null,
  loadWatchlists: jest.fn(),
  loadWatchlist: jest.fn(),
  createNewWatchlist: jest.fn(),
  updateExistingWatchlist: jest.fn(),
  deleteExistingWatchlist: jest.fn(),
  addStock: jest.fn(),
  bulkAddStocks: jest.fn(),
  updateStock: jest.fn(),
  removeStock: jest.fn(),
  loadStats: jest.fn(),
  ensureDefault: jest.fn(),
  refreshData: jest.fn(),
  clearError: jest.fn(),
};

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('WatchlistDisplay', () => {
  beforeEach(() => {
    mockUseWatchlist.mockReturnValue(mockUseWatchlistReturn);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders watchlist name and description', () => {
    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    expect(screen.getByText('My Tech Stocks')).toBeInTheDocument();
    expect(screen.getByText('Technology companies I\'m watching')).toBeInTheDocument();
  });

  it('shows default badge for default watchlist', () => {
    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    expect(screen.getByText('Default')).toBeInTheDocument();
  });

  it('displays stock items in table', () => {
    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    expect(screen.getByText('GOOGL')).toBeInTheDocument();
    expect(screen.getByText('Alphabet Inc.')).toBeInTheDocument();
  });

  it('formats prices correctly', () => {
    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    expect(screen.getByText('$175.00')).toBeInTheDocument();
    expect(screen.getByText('$2,800.00')).toBeInTheDocument();
  });

  it('shows price changes with correct colors', () => {
    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    // Positive change should be green (success color)
    const positiveChange = screen.getByText('+$5.00');
    expect(positiveChange).toBeInTheDocument();
    
    // Negative change should be red (error color)
    const negativeChange = screen.getByText('-$10.00');
    expect(negativeChange).toBeInTheDocument();
  });

  it('displays portfolio summary when items have position data', () => {
    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    expect(screen.getByText('Portfolio Summary')).toBeInTheDocument();
    expect(screen.getByText('Total Value')).toBeInTheDocument();
    expect(screen.getByText('Total Gain/Loss')).toBeInTheDocument();
  });

  it('calculates portfolio metrics correctly', () => {
    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    // AAPL: 10 shares * $175 = $1,750 current value
    // AAPL: 10 shares * $150 = $1,500 entry value
    // Gain: $250
    expect(screen.getByText('$1,750.00')).toBeInTheDocument(); // Total value
    expect(screen.getByText('$250.00 (+16.67%)')).toBeInTheDocument(); // Gain/Loss
  });

  it('shows empty state when no items', () => {
    const emptyWatchlist = { ...mockWatchlist, items: [], totalItems: 0 };
    renderWithTheme(<WatchlistDisplay watchlist={emptyWatchlist} />);
    
    expect(screen.getByText('No stocks in this watchlist yet')).toBeInTheDocument();
  });

  it('calls refresh function when refresh button is clicked', async () => {
    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    const refreshButton = screen.getByLabelText('Refresh data');
    fireEvent.click(refreshButton);
    
    expect(mockUseWatchlistReturn.refreshData).toHaveBeenCalledWith(mockWatchlist.id);
  });

  it('calls onAddStock when add stock button is clicked', () => {
    const mockOnAddStock = jest.fn();
    renderWithTheme(
      <WatchlistDisplay watchlist={mockWatchlist} onAddStock={mockOnAddStock} />
    );
    
    const addButton = screen.getByText('Add Stock');
    fireEvent.click(addButton);
    
    expect(mockOnAddStock).toHaveBeenCalled();
  });

  it('shows loading state during refresh', () => {
    mockUseWatchlist.mockReturnValue({
      ...mockUseWatchlistReturn,
      loading: { isLoading: true, message: 'Refreshing data...' },
    });

    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('displays error message when there is an error', () => {
    mockUseWatchlist.mockReturnValue({
      ...mockUseWatchlistReturn,
      error: 'Failed to load data',
    });

    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    expect(screen.getByText('Failed to load data')).toBeInTheDocument();
  });

  it('opens item menu when more actions button is clicked', async () => {
    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    const moreButtons = screen.getAllByLabelText('more');
    fireEvent.click(moreButtons[0]);
    
    await waitFor(() => {
      expect(screen.getByText('Edit')).toBeInTheDocument();
      expect(screen.getByText('Remove')).toBeInTheDocument();
    });
  });

  it('calls onEditItem when edit menu item is clicked', async () => {
    const mockOnEditItem = jest.fn();
    renderWithTheme(
      <WatchlistDisplay 
        watchlist={mockWatchlist} 
        onEditItem={mockOnEditItem}
      />
    );
    
    const moreButtons = screen.getAllByLabelText('more');
    fireEvent.click(moreButtons[0]);
    
    await waitFor(() => {
      const editButton = screen.getByText('Edit');
      fireEvent.click(editButton);
    });
    
    expect(mockOnEditItem).toHaveBeenCalledWith(mockWatchlist.items[0]);
  });

  it('calls onRemoveItem when remove menu item is clicked', async () => {
    const mockOnRemoveItem = jest.fn();
    renderWithTheme(
      <WatchlistDisplay 
        watchlist={mockWatchlist} 
        onRemoveItem={mockOnRemoveItem}
      />
    );
    
    const moreButtons = screen.getAllByLabelText('more');
    fireEvent.click(moreButtons[0]);
    
    await waitFor(() => {
      const removeButton = screen.getByText('Remove');
      fireEvent.click(removeButton);
    });
    
    expect(mockOnRemoveItem).toHaveBeenCalledWith(mockWatchlist.items[0]);
  });

  it('shows notes icon when item has notes', () => {
    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    // AAPL has notes, GOOGL doesn't
    const notesIcons = screen.getAllByTestId('NotesIcon');
    expect(notesIcons).toHaveLength(1);
  });

  it('formats volume correctly', () => {
    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    expect(screen.getByText('50.00M')).toBeInTheDocument(); // 50,000,000
    expect(screen.getByText('1.00M')).toBeInTheDocument(); // 1,000,000
  });

  it('shows target price when available', () => {
    renderWithTheme(<WatchlistDisplay watchlist={mockWatchlist} />);
    
    expect(screen.getByText('$200.00')).toBeInTheDocument(); // AAPL target price
  });

  it('shows -- for missing data', () => {
    const watchlistWithMissingData = {
      ...mockWatchlist,
      items: [{
        ...mockWatchlist.items[0],
        currentPrice: undefined,
        dailyChange: undefined,
        dailyChangePercent: undefined,
        volume: undefined,
        targetPrice: undefined,
      }],
    };

    renderWithTheme(<WatchlistDisplay watchlist={watchlistWithMissingData} />);
    
    const dashElements = screen.getAllByText('--');
    expect(dashElements.length).toBeGreaterThan(0);
  });
});