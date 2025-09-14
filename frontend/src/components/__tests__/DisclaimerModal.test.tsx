/**
 * Tests for DisclaimerModal Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import DisclaimerModal from '../DisclaimerModal';

// Mock the disclaimer service
jest.mock('../../services/disclaimer', () => ({
  disclaimerService: {
    getDisclaimersForContext: jest.fn(),
    getAllDisclaimers: jest.fn(),
    loadUserAcknowledgments: jest.fn(),
    hasUserAcknowledgedContext: jest.fn(),
    acknowledgeDisclaimer: jest.fn(),
    getTermsOfUse: jest.fn(),
    getPrivacyPolicy: jest.fn(),
  }
}));

import { disclaimerService } from '../../services/disclaimer';

const mockDisclaimerService = disclaimerService as jest.Mocked<typeof disclaimerService>;

describe('DisclaimerModal', () => {
  const mockOnClose = jest.fn();
  const mockOnAcknowledge = jest.fn();
  const userId = 'test-user';

  const mockDisclaimers = [
    {
      id: 'investment_advice',
      title: 'Investment Disclaimer',
      content: 'This is for informational purposes only.',
      severity: 'warning' as const,
      required: true,
      contexts: ['chat_response']
    },
    {
      id: 'data_accuracy',
      title: 'Data Accuracy',
      content: 'Data may not be accurate.',
      severity: 'info' as const,
      required: false,
      contexts: ['chat_response']
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockDisclaimerService.getDisclaimersForContext.mockReturnValue(mockDisclaimers);
    mockDisclaimerService.getAllDisclaimers.mockReturnValue(mockDisclaimers);
    mockDisclaimerService.hasUserAcknowledgedContext.mockReturnValue(false);
    mockDisclaimerService.getTermsOfUse.mockReturnValue('Terms of Use content');
    mockDisclaimerService.getPrivacyPolicy.mockReturnValue('Privacy Policy content');
  });

  it('should render disclaimer modal when open', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        context="chat_response"
        userId={userId}
      />
    );

    expect(screen.getByText('Disclaimers and Legal Information')).toBeInTheDocument();
    expect(screen.getByText('Investment Disclaimer')).toBeInTheDocument();
    expect(screen.getByText('Data Accuracy')).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    render(
      <DisclaimerModal
        open={false}
        onClose={mockOnClose}
        context="chat_response"
        userId={userId}
      />
    );

    expect(screen.queryByText('Disclaimers and Legal Information')).not.toBeInTheDocument();
  });

  it('should show terms and privacy tabs when showTermsAndPrivacy is true', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        showTermsAndPrivacy={true}
      />
    );

    expect(screen.getByText('Disclaimers')).toBeInTheDocument();
    expect(screen.getByText('Terms of Use')).toBeInTheDocument();
    expect(screen.getByText('Privacy Policy')).toBeInTheDocument();
  });

  it('should switch between tabs correctly', async () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        showTermsAndPrivacy={true}
      />
    );

    // Click on Terms of Use tab
    const termsTab = screen.getByText('Terms of Use');
    fireEvent.click(termsTab);

    await waitFor(() => {
      expect(screen.getByText('Terms of Use content')).toBeInTheDocument();
    });

    // Click on Privacy Policy tab
    const privacyTab = screen.getByText('Privacy Policy');
    fireEvent.click(privacyTab);

    await waitFor(() => {
      expect(screen.getByText('Privacy Policy content')).toBeInTheDocument();
    });
  });

  it('should handle checkbox changes correctly', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        context="chat_response"
        userId={userId}
      />
    );

    const checkbox = screen.getByLabelText(/I acknowledge and understand this investment disclaimer/);
    
    // Initially unchecked
    expect(checkbox).not.toBeChecked();
    
    // Check the checkbox
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
  });

  it('should call acknowledgeDisclaimer when accept is clicked', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        context="chat_response"
        userId={userId}
        onAcknowledge={mockOnAcknowledge}
      />
    );

    // Check the required disclaimer
    const checkbox = screen.getByLabelText(/I acknowledge and understand this investment disclaimer/);
    fireEvent.click(checkbox);

    // Click acknowledge button
    const acknowledgeButton = screen.getByText('Acknowledge');
    fireEvent.click(acknowledgeButton);

    expect(mockDisclaimerService.acknowledgeDisclaimer).toHaveBeenCalledWith(userId, 'investment_advice');
    expect(mockOnAcknowledge).toHaveBeenCalled();
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should show required disclaimer modal title when required is true', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        required={true}
      />
    );

    expect(screen.getByText('Important Legal Notices')).toBeInTheDocument();
  });

  it('should disable accept button when required disclaimers are not acknowledged', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        required={true}
        context="chat_response"
        userId={userId}
      />
    );

    const acceptButton = screen.getByText('Accept and Continue');
    expect(acceptButton).toBeDisabled();
  });

  it('should enable accept button when all required disclaimers are acknowledged', async () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        required={true}
        context="chat_response"
        userId={userId}
      />
    );

    // Check the required disclaimer
    const checkbox = screen.getByLabelText(/I acknowledge and understand this investment disclaimer/);
    fireEvent.click(checkbox);

    await waitFor(() => {
      const acceptButton = screen.getByText('Accept and Continue');
      expect(acceptButton).not.toBeDisabled();
    });
  });

  it('should prevent closing when required and not all acknowledged', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        required={true}
        context="chat_response"
        userId={userId}
      />
    );

    // Try to close without acknowledging
    const closeButton = screen.queryByLabelText('close');
    expect(closeButton).not.toBeInTheDocument(); // Close button should not be present when required
  });

  it('should show warning when required disclaimers are not acknowledged', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        required={true}
        context="chat_response"
        userId={userId}
      />
    );

    expect(screen.getByText('You must acknowledge all required disclaimers before continuing.')).toBeInTheDocument();
  });

  it('should load existing acknowledgments on mount', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        context="chat_response"
        userId={userId}
      />
    );

    expect(mockDisclaimerService.loadUserAcknowledgments).toHaveBeenCalledWith(userId);
  });

  it('should display correct severity icons', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        context="chat_response"
        userId={userId}
      />
    );

    // Check for warning and info alerts
    const alerts = screen.getAllByRole('alert');
    expect(alerts).toHaveLength(2); // One for each disclaimer
  });

  it('should handle missing userId gracefully', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        context="chat_response"
      />
    );

    // Should not crash and should not call user-specific methods
    expect(mockDisclaimerService.loadUserAcknowledgments).not.toHaveBeenCalled();
    
    // Acknowledge button should still work
    const acknowledgeButton = screen.getByText('Acknowledge');
    fireEvent.click(acknowledgeButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should show all disclaimers when no context is provided', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        userId={userId}
      />
    );

    expect(mockDisclaimerService.getAllDisclaimers).toHaveBeenCalled();
  });

  it('should have proper accessibility attributes', () => {
    render(
      <DisclaimerModal
        open={true}
        onClose={mockOnClose}
        context="chat_response"
        userId={userId}
      />
    );

    // Check for proper dialog attributes
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();

    // Check for proper button attributes
    const acknowledgeButton = screen.getByText('Acknowledge');
    expect(acknowledgeButton).toHaveAttribute('type', 'button');

    // Check for proper checkbox labels
    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach(checkbox => {
      expect(checkbox).toHaveAccessibleName();
    });
  });
});