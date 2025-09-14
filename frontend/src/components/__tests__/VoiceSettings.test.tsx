import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import VoiceSettings from '../VoiceSettings';

// Mock speech synthesis
const mockSpeak = jest.fn();
const mockCancel = jest.fn();

const mockSpeechSynthesisUtterance = jest.fn().mockImplementation((text) => ({
  text,
  voice: null,
  rate: 1,
  pitch: 1,
  volume: 1,
  onstart: null,
  onend: null,
  onerror: null,
}));

Object.defineProperty(window, 'speechSynthesis', {
  writable: true,
  value: {
    speak: mockSpeak,
    cancel: mockCancel,
  },
});

Object.defineProperty(window, 'SpeechSynthesisUtterance', {
  writable: true,
  value: mockSpeechSynthesisUtterance,
});

const mockVoices: SpeechSynthesisVoice[] = [
  {
    name: 'English Voice 1',
    lang: 'en-US',
    default: true,
    localService: true,
    voiceURI: 'en-voice-1',
  } as SpeechSynthesisVoice,
  {
    name: 'English Voice 2',
    lang: 'en-GB',
    default: false,
    localService: true,
    voiceURI: 'en-voice-2',
  } as SpeechSynthesisVoice,
  {
    name: 'Spanish Voice',
    lang: 'es-ES',
    default: false,
    localService: true,
    voiceURI: 'es-voice-1',
  } as SpeechSynthesisVoice,
];

const defaultProps = {
  open: true,
  onClose: jest.fn(),
  voices: mockVoices,
  selectedVoice: mockVoices[0],
  onVoiceChange: jest.fn(),
  speechRate: 1,
  onSpeechRateChange: jest.fn(),
  speechPitch: 1,
  onSpeechPitchChange: jest.fn(),
  speechVolume: 1,
  onSpeechVolumeChange: jest.fn(),
  autoSpeak: true,
  onAutoSpeakChange: jest.fn(),
  continuousListening: false,
  onContinuousListeningChange: jest.fn(),
};

describe('VoiceSettings', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render voice settings dialog when open', () => {
    render(<VoiceSettings {...defaultProps} />);
    
    expect(screen.getByText('Voice Settings')).toBeInTheDocument();
    expect(screen.getByLabelText('Voice')).toBeInTheDocument();
    expect(screen.getByText('Speech Rate: 1.0x')).toBeInTheDocument();
    expect(screen.getByText('Speech Pitch: 1.0')).toBeInTheDocument();
    expect(screen.getByText('Speech Volume: 100%')).toBeInTheDocument();
  });

  it('should not render when closed', () => {
    render(<VoiceSettings {...defaultProps} open={false} />);
    
    expect(screen.queryByText('Voice Settings')).not.toBeInTheDocument();
  });

  it('should display available voices grouped by language', () => {
    render(<VoiceSettings {...defaultProps} />);
    
    // Open voice select
    fireEvent.mouseDown(screen.getByLabelText('Voice'));
    
    expect(screen.getByText('EN Voices')).toBeInTheDocument();
    expect(screen.getByText('ES Voices')).toBeInTheDocument();
    expect(screen.getByText('English Voice 1 (Default)')).toBeInTheDocument();
    expect(screen.getByText('English Voice 2')).toBeInTheDocument();
    expect(screen.getByText('Spanish Voice')).toBeInTheDocument();
  });

  it('should call onVoiceChange when voice is selected', async () => {
    const user = userEvent.setup();
    render(<VoiceSettings {...defaultProps} />);
    
    // Open voice select
    await user.click(screen.getByLabelText('Voice'));
    
    // Select a different voice
    await user.click(screen.getByText('English Voice 2'));
    
    expect(defaultProps.onVoiceChange).toHaveBeenCalledWith(mockVoices[1]);
  });

  it('should update speech rate when slider is moved', async () => {
    render(<VoiceSettings {...defaultProps} />);
    
    // Find sliders by their container text since MUI sliders don't have accessible names
    const sliders = screen.getAllByRole('slider');
    const rateSlider = sliders[0]; // First slider is rate
    
    // Simulate slider change
    fireEvent.change(rateSlider, { target: { value: '1.5' } });
    
    expect(defaultProps.onSpeechRateChange).toHaveBeenCalledWith(1.5);
  });

  it('should update speech pitch when slider is moved', () => {
    render(<VoiceSettings {...defaultProps} />);
    
    const sliders = screen.getAllByRole('slider');
    const pitchSlider = sliders[1]; // Second slider is pitch
    
    fireEvent.change(pitchSlider, { target: { value: '0.8' } });
    
    expect(defaultProps.onSpeechPitchChange).toHaveBeenCalledWith(0.8);
  });

  it('should update speech volume when slider is moved', () => {
    render(<VoiceSettings {...defaultProps} />);
    
    const sliders = screen.getAllByRole('slider');
    const volumeSlider = sliders[2]; // Third slider is volume
    
    fireEvent.change(volumeSlider, { target: { value: '0.7' } });
    
    expect(defaultProps.onSpeechVolumeChange).toHaveBeenCalledWith(0.7);
  });

  it('should toggle auto-speak when switch is clicked', async () => {
    const user = userEvent.setup();
    render(<VoiceSettings {...defaultProps} />);
    
    const autoSpeakSwitch = screen.getByRole('checkbox', { name: /auto-speak responses/i });
    
    await user.click(autoSpeakSwitch);
    
    expect(defaultProps.onAutoSpeakChange).toHaveBeenCalledWith(false);
  });

  it('should toggle continuous listening when switch is clicked', async () => {
    const user = userEvent.setup();
    render(<VoiceSettings {...defaultProps} />);
    
    const continuousSwitch = screen.getByRole('checkbox', { name: /continuous listening mode/i });
    
    await user.click(continuousSwitch);
    
    expect(defaultProps.onContinuousListeningChange).toHaveBeenCalledWith(true);
  });

  it('should test voice when test button is clicked', async () => {
    const user = userEvent.setup();
    render(<VoiceSettings {...defaultProps} />);
    
    const testButton = screen.getByText('Test Voice Settings');
    
    await user.click(testButton);
    
    expect(mockCancel).toHaveBeenCalled();
    expect(mockSpeak).toHaveBeenCalled();
  });

  it('should disable test button when no voice is selected', () => {
    render(<VoiceSettings {...defaultProps} selectedVoice={null} />);
    
    const testButton = screen.getByText('Test Voice Settings');
    
    expect(testButton).toBeDisabled();
  });

  it('should reset settings when reset button is clicked', async () => {
    const user = userEvent.setup();
    render(<VoiceSettings {...defaultProps} />);
    
    const resetButton = screen.getByText('Reset to Defaults');
    
    await user.click(resetButton);
    
    expect(defaultProps.onSpeechRateChange).toHaveBeenCalledWith(1);
    expect(defaultProps.onSpeechPitchChange).toHaveBeenCalledWith(1);
    expect(defaultProps.onSpeechVolumeChange).toHaveBeenCalledWith(1);
    expect(defaultProps.onAutoSpeakChange).toHaveBeenCalledWith(true);
    expect(defaultProps.onContinuousListeningChange).toHaveBeenCalledWith(false);
    expect(defaultProps.onVoiceChange).toHaveBeenCalledWith(mockVoices[0]); // Default voice
  });

  it('should close dialog when done button is clicked', async () => {
    const user = userEvent.setup();
    render(<VoiceSettings {...defaultProps} />);
    
    const doneButton = screen.getByText('Done');
    
    await user.click(doneButton);
    
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('should display correct slider values', () => {
    render(
      <VoiceSettings 
        {...defaultProps} 
        speechRate={1.5}
        speechPitch={0.8}
        speechVolume={0.6}
      />
    );
    
    expect(screen.getByText('Speech Rate: 1.5x')).toBeInTheDocument();
    expect(screen.getByText('Speech Pitch: 0.8')).toBeInTheDocument();
    expect(screen.getByText('Speech Volume: 60%')).toBeInTheDocument();
  });

  it('should show warning when speech synthesis is not supported', () => {
    // Mock speechSynthesis as undefined
    const originalSpeechSynthesis = window.speechSynthesis;
    delete (window as any).speechSynthesis;

    render(<VoiceSettings {...defaultProps} />);
    
    expect(screen.getByText(/Speech synthesis is not supported/)).toBeInTheDocument();
    
    // Restore
    window.speechSynthesis = originalSpeechSynthesis;
  });

  it('should show warning when speech recognition is not supported', () => {
    // Mock speech recognition as undefined
    const originalSpeechRecognition = window.SpeechRecognition;
    const originalWebkitSpeechRecognition = window.webkitSpeechRecognition;
    
    delete (window as any).SpeechRecognition;
    delete (window as any).webkitSpeechRecognition;

    render(<VoiceSettings {...defaultProps} />);
    
    expect(screen.getByText(/Speech recognition is not supported/)).toBeInTheDocument();

    // Restore
    window.SpeechRecognition = originalSpeechRecognition;
    window.webkitSpeechRecognition = originalWebkitSpeechRecognition;
  });

  it('should handle empty voices array', () => {
    render(<VoiceSettings {...defaultProps} voices={[]} selectedVoice={null} />);
    
    // Should still render without errors
    expect(screen.getByText('Voice Settings')).toBeInTheDocument();
    expect(screen.getByText('Voice')).toBeInTheDocument(); // Check for label text instead
  });

  it('should display voice options section', () => {
    render(<VoiceSettings {...defaultProps} />);
    
    expect(screen.getByText('Voice Options')).toBeInTheDocument();
    expect(screen.getByText('Auto-speak responses')).toBeInTheDocument();
    expect(screen.getByText('Continuous listening mode')).toBeInTheDocument();
  });

  it('should reflect current switch states', () => {
    render(
      <VoiceSettings 
        {...defaultProps} 
        autoSpeak={false}
        continuousListening={true}
      />
    );
    
    const autoSpeakSwitch = screen.getByRole('checkbox', { name: /auto-speak responses/i });
    const continuousSwitch = screen.getByRole('checkbox', { name: /continuous listening mode/i });
    
    expect(autoSpeakSwitch).not.toBeChecked();
    expect(continuousSwitch).toBeChecked();
  });
});