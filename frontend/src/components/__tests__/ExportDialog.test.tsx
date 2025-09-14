import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ExportDialog from '../ExportDialog';
import * as exportService from '../../services/export';

// Mock the export service
jest.mock('../../services/export');

const mockExportService = exportService as jest.Mocked<typeof exportService>;

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('ExportDialog', () => {
  const defaultProps = {
    open: true,
    onClose: jest.fn(),
    symbol: 'AAPL',
    analysisData: {
      stock: {
        symbol: 'AAPL',
        name: 'Apple Inc.',
        exchange: 'NASDAQ',
        sector: 'Technology',
        industry: 'Consumer Electronics',
        marketCap: 3000000000000,
        lastUpdated: '2024-01-15T10:00:00Z'
      },
      market_data: {
        symbol: 'AAPL',
        price: 150.00,
        change: 2.50,
        changePercent: 1.69,
        volume: 50000000,
        high52Week: 180.00,
        low52Week: 120.00,
        avgVolume: 60000000,
        marketCap: 3000000000000,
        peRatio: 25.5,
        timestamp: '2024-01-15T15:30:00Z',
        isStale: false
      }
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock export formats
    mockExportService.getExportFormats.mockResolvedValue([
      {
        format: 'pdf',
        name: 'PDF Report',
        description: 'Comprehensive analysis report with charts and formatting',
        mime_type: 'application/pdf',
        supports_charts: true
      },
      {
        format: 'csv',
        name: 'CSV Data',
        description: 'Raw analysis data in comma-separated values format',
        mime_type: 'text/csv',
        supports_charts: false
      },
      {
        format: 'json',
        name: 'JSON Data',
        description: 'Structured analysis data in JSON format',
        mime_type: 'application/json',
        supports_charts: false
      }
    ]);
  });

  it('renders dialog with correct title and symbol', async () => {
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    expect(screen.getByText('Export & Share Analysis')).toBeInTheDocument();
    expect(screen.getByText('AAPL Analysis')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(mockExportService.getExportFormats).toHaveBeenCalled();
    });
  });

  it('displays export format options', async () => {
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('PDF Report')).toBeInTheDocument();
      expect(screen.getByText('CSV Data')).toBeInTheDocument();
      expect(screen.getByText('JSON Data')).toBeInTheDocument();
    });
  });

  it('shows format details when format is selected', async () => {
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('application/pdf')).toBeInTheDocument();
      expect(screen.getByText('Charts: Supported')).toBeInTheDocument();
    });
  });

  it('handles PDF export', async () => {
    const user = userEvent.setup();
    const mockBlob = new Blob(['fake pdf content'], { type: 'application/pdf' });
    mockExportService.exportPdfReport.mockResolvedValue(mockBlob);
    mockExportService.downloadBlob = jest.fn();
    
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Export as PDF')).toBeInTheDocument();
    });
    
    const exportButton = screen.getByText('Export as PDF');
    await user.click(exportButton);
    
    await waitFor(() => {
      expect(mockExportService.exportPdfReport).toHaveBeenCalledWith('AAPL', true, true);
      expect(mockExportService.downloadBlob).toHaveBeenCalledWith(mockBlob, expect.stringContaining('AAPL_analysis_'));
    });
  });

  it('handles CSV export', async () => {
    const user = userEvent.setup();
    const mockBlob = new Blob(['fake csv content'], { type: 'text/csv' });
    mockExportService.exportCsvData.mockResolvedValue(mockBlob);
    mockExportService.downloadBlob = jest.fn();
    
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    // Select CSV format
    await waitFor(() => {
      const csvRadio = screen.getByLabelText(/CSV Data/);
      fireEvent.click(csvRadio);
    });
    
    const exportButton = screen.getByText('Export as CSV');
    await user.click(exportButton);
    
    await waitFor(() => {
      expect(mockExportService.exportCsvData).toHaveBeenCalledWith('AAPL', true);
      expect(mockExportService.downloadBlob).toHaveBeenCalledWith(mockBlob, expect.stringContaining('AAPL_analysis_'));
    });
  });

  it('handles JSON export', async () => {
    const user = userEvent.setup();
    const mockBlob = new Blob(['fake json content'], { type: 'application/json' });
    mockExportService.exportJsonData.mockResolvedValue(mockBlob);
    mockExportService.downloadBlob = jest.fn();
    
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    // Select JSON format
    await waitFor(() => {
      const jsonRadio = screen.getByLabelText(/JSON Data/);
      fireEvent.click(jsonRadio);
    });
    
    const exportButton = screen.getByText('Export as JSON');
    await user.click(exportButton);
    
    await waitFor(() => {
      expect(mockExportService.exportJsonData).toHaveBeenCalledWith('AAPL', true, true);
      expect(mockExportService.downloadBlob).toHaveBeenCalledWith(mockBlob, expect.stringContaining('AAPL_analysis_'));
    });
  });

  it('creates shareable link', async () => {
    const user = userEvent.setup();
    const mockShareResponse = {
      link_id: 'test-link-id',
      share_url: '/share/test-link-id',
      expires_at: '2024-01-16T15:30:00Z',
      created_at: '2024-01-15T15:30:00Z'
    };
    mockExportService.createShareLink.mockResolvedValue(mockShareResponse);
    mockExportService.getShareUrl.mockReturnValue('http://localhost:3000/share/test-link-id');
    
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    await waitFor(() => {
      const createLinkButton = screen.getByText('Create Shareable Link');
      expect(createLinkButton).toBeInTheDocument();
    });
    
    const createLinkButton = screen.getByText('Create Shareable Link');
    await user.click(createLinkButton);
    
    await waitFor(() => {
      expect(mockExportService.createShareLink).toHaveBeenCalledWith({
        symbol: 'AAPL',
        include_sentiment: true,
        expires_in_hours: 24
      });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Shareable Link Created')).toBeInTheDocument();
      expect(screen.getByDisplayValue('http://localhost:3000/share/test-link-id')).toBeInTheDocument();
    });
  });

  it('copies share link to clipboard', async () => {
    const user = userEvent.setup();
    const mockShareResponse = {
      link_id: 'test-link-id',
      share_url: '/share/test-link-id',
      expires_at: '2024-01-16T15:30:00Z',
      created_at: '2024-01-15T15:30:00Z'
    };
    mockExportService.createShareLink.mockResolvedValue(mockShareResponse);
    mockExportService.getShareUrl.mockReturnValue('http://localhost:3000/share/test-link-id');
    mockExportService.copyToClipboard.mockResolvedValue(true);
    
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    // Create share link first
    const createLinkButton = screen.getByText('Create Shareable Link');
    await user.click(createLinkButton);
    
    await waitFor(() => {
      expect(screen.getByText('Shareable Link Created')).toBeInTheDocument();
    });
    
    // Click copy button
    const copyButton = screen.getByRole('button', { name: /copy to clipboard/i });
    await user.click(copyButton);
    
    await waitFor(() => {
      expect(mockExportService.copyToClipboard).toHaveBeenCalledWith('http://localhost:3000/share/test-link-id');
    });
  });

  it('validates expiration hours', async () => {
    const user = userEvent.setup();
    
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    // Set invalid expiration time
    const expirationInput = screen.getByLabelText('Link expires in (hours)');
    await user.clear(expirationInput);
    await user.type(expirationInput, '200');
    
    const createLinkButton = screen.getByText('Create Shareable Link');
    await user.click(createLinkButton);
    
    await waitFor(() => {
      expect(screen.getByText('Expiration time must be between 1 and 168 hours')).toBeInTheDocument();
    });
    
    expect(mockExportService.createShareLink).not.toHaveBeenCalled();
  });

  it('handles export error', async () => {
    const user = userEvent.setup();
    mockExportService.exportPdfReport.mockRejectedValue(new Error('Export failed'));
    
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    await waitFor(() => {
      const exportButton = screen.getByText('Export as PDF');
      expect(exportButton).toBeInTheDocument();
    });
    
    const exportButton = screen.getByText('Export as PDF');
    await user.click(exportButton);
    
    await waitFor(() => {
      expect(screen.getByText('Export failed')).toBeInTheDocument();
    });
  });

  it('handles share link creation error', async () => {
    const user = userEvent.setup();
    mockExportService.createShareLink.mockRejectedValue(new Error('Share link creation failed'));
    
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    const createLinkButton = screen.getByText('Create Shareable Link');
    await user.click(createLinkButton);
    
    await waitFor(() => {
      expect(screen.getByText('Share link creation failed')).toBeInTheDocument();
    });
  });

  it('shows loading states', async () => {
    const user = userEvent.setup();
    mockExportService.exportPdfReport.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    await waitFor(() => {
      const exportButton = screen.getByText('Export as PDF');
      expect(exportButton).toBeInTheDocument();
    });
    
    const exportButton = screen.getByText('Export as PDF');
    await user.click(exportButton);
    
    expect(screen.getByText('Exporting...')).toBeInTheDocument();
    expect(exportButton).toBeDisabled();
  });

  it('closes dialog when close button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();
    
    renderWithTheme(<ExportDialog {...defaultProps} onClose={onClose} />);
    
    const closeButton = screen.getByText('Close');
    await user.click(closeButton);
    
    expect(onClose).toHaveBeenCalled();
  });

  it('handles dialog with no symbol', () => {
    renderWithTheme(<ExportDialog {...defaultProps} symbol="" />);
    
    expect(screen.getByText('Stock Analysis')).toBeInTheDocument();
  });

  it('updates options based on format selection', async () => {
    const user = userEvent.setup();
    
    renderWithTheme(<ExportDialog {...defaultProps} />);
    
    // Initially PDF is selected, charts option should be visible
    await waitFor(() => {
      expect(screen.getByText('Include charts and visualizations')).toBeInTheDocument();
    });
    
    // Select CSV format
    const csvRadio = screen.getByLabelText(/CSV Data/);
    await user.click(csvRadio);
    
    // Charts option should not be visible for CSV
    expect(screen.queryByText('Include charts and visualizations')).not.toBeInTheDocument();
    
    // Select JSON format
    const jsonRadio = screen.getByLabelText(/JSON Data/);
    await user.click(jsonRadio);
    
    // Metadata option should be visible for JSON
    expect(screen.getByText('Include export metadata')).toBeInTheDocument();
  });
});