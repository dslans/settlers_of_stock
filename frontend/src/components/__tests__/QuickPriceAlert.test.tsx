/**
 * Tests for QuickPriceAlert component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QuickPriceAlert } from '../QuickPriceAlert';
import { alertService } from '../../services/alert';
import { Alert, AlertType, AlertStatus } from '../../types/alert';

// Mock the alert service
jest.mock('../../services/alert');
const mockAlertService = alertService as jest.Mocked<typeof alertService>;

const mockAlert: Alert = {
  id: 1,
  user_id: 1,
  symbol: 'AAPL',
  alert_type: AlertType.PRICE_ABOVE,
  status: AlertStatus.ACTIVE,
  condition_value: 150,
  condition_operator: '>=',
  name: 'AAPL above $150',
  description: null,
  message_template: null,
  notify_email: true,
  notify_push: true,
  notify_sms: false,
  expires_at: null,
  max_triggers: 1,
  trigger_count: 0,
  cooldown_minutes: 60,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  last_checked_at: null,
  last_triggered_at: null
};

describe('QuickPriceAlert', () => {
  const mockOnAlertCreated = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockAlertService.createQuickPriceAlert.mockResolvedValue(mockAlert);
  });

  it('renders the form correctly', () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Quick Price Alert')).toBeInTheDocument();
    expect(screen.getByLabelText('Stock Symbol')).toBeInTheDocument();
    expect(screen.getByLabelText('Alert When Price Goes')).toBeInTheDocument();
    expect(screen.getByLabelText('Target Price')).toBeInTheDocument();
    expect(screen.getByText('Create Alert')).toBeInTheDocument();
  });

  it('initializes with provided symbol', () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
        initialSymbol="TSLA"
      />
    );

    const symbolInput = screen.getByLabelText('Stock Symbol') as HTMLInputElement;
    expect(symbolInput.value).toBe('TSLA');
  });

  it('updates form fields correctly', () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    // Update symbol
    const symbolInput = screen.getByLabelText('Stock Symbol');
    fireEvent.change(symbolInput, { target: { value: 'aapl' } });
    expect((symbolInput as HTMLInputElement).value).toBe('AAPL'); // Should be uppercase

    // Update target price
    const priceInput = screen.getByLabelText('Target Price');
    fireEvent.change(priceInput, { target: { value: '150.50' } });
    expect((priceInput as HTMLInputElement).value).toBe('150.50');

    // Update alert direction
    const directionSelect = screen.getByLabelText('Alert When Price Goes');
    fireEvent.change(directionSelect, { target: { value: 'below' } });
    expect((directionSelect as HTMLSelectElement).value).toBe('below');
  });

  it('auto-generates alert name', () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    // Fill in symbol and price
    fireEvent.change(screen.getByLabelText('Stock Symbol'), { target: { value: 'AAPL' } });
    fireEvent.change(screen.getByLabelText('Target Price'), { target: { value: '150' } });

    // Check that name is auto-generated
    const nameInput = screen.getByLabelText('Alert Name (Optional)') as HTMLInputElement;
    expect(nameInput.value).toBe('AAPL above $150');
  });

  it('shows alert preview', () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    // Initially shows placeholder
    expect(screen.getByText(/Fill in the details above/)).toBeInTheDocument();

    // Fill in form
    fireEvent.change(screen.getByLabelText('Stock Symbol'), { target: { value: 'AAPL' } });
    fireEvent.change(screen.getByLabelText('Target Price'), { target: { value: '150' } });

    // Should show preview
    expect(screen.getByText(/You will be notified when AAPL goes above \$150/)).toBeInTheDocument();
  });

  it('validates form before submission', async () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    // Try to submit empty form
    fireEvent.click(screen.getByText('Create Alert'));

    await waitFor(() => {
      expect(screen.getByText('Stock symbol is required')).toBeInTheDocument();
      expect(screen.getByText('Target price must be greater than 0')).toBeInTheDocument();
    });

    expect(mockAlertService.createQuickPriceAlert).not.toHaveBeenCalled();
  });

  it('validates stock symbol format', async () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    // Enter invalid symbol
    fireEvent.change(screen.getByLabelText('Stock Symbol'), { target: { value: 'INVALID123' } });
    fireEvent.change(screen.getByLabelText('Target Price'), { target: { value: '150' } });
    fireEvent.click(screen.getByText('Create Alert'));

    await waitFor(() => {
      expect(screen.getByText(/Enter a valid stock symbol/)).toBeInTheDocument();
    });
  });

  it('validates target price', async () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    // Enter valid symbol but invalid price
    fireEvent.change(screen.getByLabelText('Stock Symbol'), { target: { value: 'AAPL' } });
    fireEvent.change(screen.getByLabelText('Target Price'), { target: { value: '0' } });
    fireEvent.click(screen.getByText('Create Alert'));

    await waitFor(() => {
      expect(screen.getByText('Target price must be greater than 0')).toBeInTheDocument();
    });

    // Test very high price
    fireEvent.change(screen.getByLabelText('Target Price'), { target: { value: '50000' } });
    fireEvent.click(screen.getByText('Create Alert'));

    await waitFor(() => {
      expect(screen.getByText('Target price seems too high')).toBeInTheDocument();
    });
  });

  it('submits form successfully', async () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    // Fill in valid form
    fireEvent.change(screen.getByLabelText('Stock Symbol'), { target: { value: 'AAPL' } });
    fireEvent.change(screen.getByLabelText('Target Price'), { target: { value: '150' } });
    fireEvent.change(screen.getByLabelText('Alert When Price Goes'), { target: { value: 'above' } });

    // Submit form
    fireEvent.click(screen.getByText('Create Alert'));

    await waitFor(() => {
      expect(mockAlertService.createQuickPriceAlert).toHaveBeenCalledWith({
        symbol: 'AAPL',
        target_price: 150,
        alert_when: 'above',
        name: 'AAPL above $150'
      });
      expect(mockOnAlertCreated).toHaveBeenCalledWith(mockAlert);
    });
  });

  it('handles API errors', async () => {
    mockAlertService.createQuickPriceAlert.mockRejectedValue({
      response: {
        data: {
          detail: 'Invalid stock symbol: INVALID. Try AAPL, MSFT'
        }
      }
    });

    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    // Fill in form
    fireEvent.change(screen.getByLabelText('Stock Symbol'), { target: { value: 'INVALID' } });
    fireEvent.change(screen.getByLabelText('Target Price'), { target: { value: '150' } });

    // Submit form
    fireEvent.click(screen.getByText('Create Alert'));

    await waitFor(() => {
      expect(screen.getByText(/Invalid stock symbol: INVALID/)).toBeInTheDocument();
    });

    expect(mockOnAlertCreated).not.toHaveBeenCalled();
  });

  it('shows loading state during submission', async () => {
    // Make the API call hang
    mockAlertService.createQuickPriceAlert.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 1000))
    );

    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    // Fill in form
    fireEvent.change(screen.getByLabelText('Stock Symbol'), { target: { value: 'AAPL' } });
    fireEvent.change(screen.getByLabelText('Target Price'), { target: { value: '150' } });

    // Submit form
    fireEvent.click(screen.getByText('Create Alert'));

    // Should show loading state
    expect(screen.getByText('Creating...')).toBeInTheDocument();
    expect(screen.getByText('Creating...')).toBeDisabled();
  });

  it('resets form when reset button is clicked', () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    // Fill in form
    fireEvent.change(screen.getByLabelText('Stock Symbol'), { target: { value: 'AAPL' } });
    fireEvent.change(screen.getByLabelText('Target Price'), { target: { value: '150' } });

    // Reset form
    fireEvent.click(screen.getByText('Reset'));

    // Form should be cleared
    expect((screen.getByLabelText('Stock Symbol') as HTMLInputElement).value).toBe('');
    expect((screen.getByLabelText('Target Price') as HTMLInputElement).value).toBe('');
    expect((screen.getByLabelText('Alert Name (Optional)') as HTMLInputElement).value).toBe('');
  });

  it('calls onCancel when cancel button is clicked', () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    fireEvent.click(screen.getByText('Cancel'));
    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('disables submit button when form is invalid', () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    const submitButton = screen.getByText('Create Alert');
    expect(submitButton).toBeDisabled();

    // Fill in symbol only
    fireEvent.change(screen.getByLabelText('Stock Symbol'), { target: { value: 'AAPL' } });
    expect(submitButton).toBeDisabled();

    // Fill in price as well
    fireEvent.change(screen.getByLabelText('Target Price'), { target: { value: '150' } });
    expect(submitButton).not.toBeDisabled();
  });

  it('clears errors when user starts typing', async () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    // Submit empty form to generate errors
    fireEvent.click(screen.getByText('Create Alert'));

    await waitFor(() => {
      expect(screen.getByText('Stock symbol is required')).toBeInTheDocument();
    });

    // Start typing in symbol field
    fireEvent.change(screen.getByLabelText('Stock Symbol'), { target: { value: 'A' } });

    // Error should be cleared
    expect(screen.queryByText('Stock symbol is required')).not.toBeInTheDocument();
  });

  it('displays helpful tips', () => {
    render(
      <QuickPriceAlert
        onAlertCreated={mockOnAlertCreated}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('💡 Tips')).toBeInTheDocument();
    expect(screen.getByText(/Use standard stock symbols/)).toBeInTheDocument();
    expect(screen.getByText(/Set realistic target prices/)).toBeInTheDocument();
  });
});