/**
 * Tests for StartupDisclaimer Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import StartupDisclaimer from '../StartupDisclaimer';

// Mock the disclaimer service
jest.mock('../../services/disclaimer', () => ({
  disclaimerService: {
    acknowledgeDisclaimer: jest.fn(),
    getRequiredDisclaimersForContext: jest.fn(),
  }
}));

import { disclaimerService } from '../../services/disclaimer';

const mockDisclaimerService = disclaimerService as jest.Mocked<typeof disclaimerService>;

describe('StartupDisclaimer', () => {
  const mockOnAccept = jest.fn();
  const userId = 'test-user';

  beforeEach(() => {
    jest.clearAllMocks();
    mockDisclaimerService.getRequiredDisclaimersForContext.mockReturnValue([
      { id: 'investment_advice', title: 'Investment Disclaimer', content: 'Test content', severity: 'warning', required: true, contexts: ['app_startup'] },
      { id: 'risk_warning', title: 'Risk Warning', content: 'Test content', severity: 'error', required: true, contexts: ['app_startup'] }
    ]);
  });

  it('should render startup disclaimer modal when open', () => {
    render(
      <StartupDisclaimer
        open={true}
        onAccept={mockOnAccept}
        userId={userId}
      />
    );

    expect(screen.getByText('Welcome to Settlers of Stock')).toBeInTheDocument();
    expect(screen.getByText('Important Legal Notices and Disclaimers')).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    render(
      <StartupDisclaimer
        open={false}
        onAccept={mockOnAccept}
        userId={userId}
      />
    );

    expect(screen.queryByText('Welcome to Settlers of Stock')).not.toBeInTheDocument();
  });

  it('should display all required disclaimer sections', () => {
    render(
      <StartupDisclaimer
        open={true}
        onAccept={mockOnAccept}
        userId={userId}
      />
    );

    expect(screen.getByText('Investment Disclaimer')).toBeInTheDocument();
    expect(screen.getByText('Risk Warning')).toBeInTheDocument();
    expect(screen.getByText('AI Analysis Limitations')).toBeInTheDocument();
    expect(screen.getByText('Regulatory Notice')).toBeInTheDocument();
  });

  it('should have accept button disabled initially', () => {
    render(
      <StartupDisclaimer
        open={true}
        onAccept={mockOnAccept}
        userId={userId}
      />
    );

    const acceptButton = screen.getByText('I Acknowledge and Accept');
    expect(acceptButton).toBeDisabled();
  });

  it('should enable accept button when all checkboxes are checked', async () => {
    render(
      <StartupDisclaimer
        open={true}
        onAccept={mockOnAccept}
        userId={userId}
      />
    );

    // Check all required checkboxes
    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach(checkbox => {
      fireEvent.click(checkbox);
    });

    await waitFor(() => {
      const acceptButton = screen.getByText('I Acknowledge and Accept');
      expect(acceptButton).not.toBeDisabled();
    });
  });

  it('should call onAccept and acknowledge disclaimers when accept button is clicked', async () => {
    render(
      <StartupDisclaimer
        open={true}
        onAccept={mockOnAccept}
        userId={userId}
      />
    );

    // Check all required checkboxes
    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach(checkbox => {
      fireEvent.click(checkbox);
    });

    await waitFor(() => {
      const acceptButton = screen.getByText('I Acknowledge and Accept');
      expect(acceptButton).not.toBeDisabled();
    });

    const acceptButton = screen.getByText('I Acknowledge and Accept');
    fireEvent.click(acceptButton);

    expect(mockDisclaimerService.acknowledgeDisclaimer).toHaveBeenCalledWith(userId, 'investment_advice');
    expect(mockDisclaimerService.acknowledgeDisclaimer).toHaveBeenCalledWith(userId, 'risk_warning');
    expect(mockOnAccept).toHaveBeenCalled();
  });

  it('should show warning when not all disclaimers are acknowledged', () => {
    render(
      <StartupDisclaimer
        open={true}
        onAccept={mockOnAccept}
        userId={userId}
      />
    );

    expect(screen.getByText('Please acknowledge all disclaimers above to continue using the application.')).toBeInTheDocument();
  });

  it('should hide warning when all disclaimers are acknowledged', async () => {
    render(
      <StartupDisclaimer
        open={true}
        onAccept={mockOnAccept}
        userId={userId}
      />
    );

    // Check all required checkboxes
    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach(checkbox => {
      fireEvent.click(checkbox);
    });

    await waitFor(() => {
      expect(screen.queryByText('Please acknowledge all disclaimers above to continue using the application.')).not.toBeInTheDocument();
    });
  });

  it('should handle individual checkbox changes correctly', async () => {
    render(
      <StartupDisclaimer
        open={true}
        onAccept={mockOnAccept}
        userId={userId}
      />
    );

    const investmentCheckbox = screen.getByLabelText(/I understand this is not investment advice/);
    
    // Initially unchecked
    expect(investmentCheckbox).not.toBeChecked();
    
    // Check the checkbox
    fireEvent.click(investmentCheckbox);
    expect(investmentCheckbox).toBeChecked();
    
    // Uncheck the checkbox
    fireEvent.click(investmentCheckbox);
    expect(investmentCheckbox).not.toBeChecked();
  });

  it('should display terms and privacy policy notice', () => {
    render(
      <StartupDisclaimer
        open={true}
        onAccept={mockOnAccept}
        userId={userId}
      />
    );

    expect(screen.getByText(/By continuing, you also agree to our Terms of Use and Privacy Policy/)).toBeInTheDocument();
    expect(screen.getByText(/You can review these documents at any time in the application settings/)).toBeInTheDocument();
  });

  it('should not call acknowledgeDisclaimer when userId is not provided', async () => {
    render(
      <StartupDisclaimer
        open={true}
        onAccept={mockOnAccept}
      />
    );

    // Check all required checkboxes
    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach(checkbox => {
      fireEvent.click(checkbox);
    });

    await waitFor(() => {
      const acceptButton = screen.getByText('I Acknowledge and Accept');
      expect(acceptButton).not.toBeDisabled();
    });

    const acceptButton = screen.getByText('I Acknowledge and Accept');
    fireEvent.click(acceptButton);

    expect(mockDisclaimerService.acknowledgeDisclaimer).not.toHaveBeenCalled();
    expect(mockOnAccept).toHaveBeenCalled();
  });

  it('should have proper accessibility attributes', () => {
    render(
      <StartupDisclaimer
        open={true}
        onAccept={mockOnAccept}
        userId={userId}
      />
    );

    // Check for proper dialog attributes
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();

    // Check for proper button attributes
    const acceptButton = screen.getByText('I Acknowledge and Accept');
    expect(acceptButton).toHaveAttribute('type', 'button');

    // Check for proper checkbox labels
    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach(checkbox => {
      expect(checkbox).toHaveAccessibleName();
    });
  });
});