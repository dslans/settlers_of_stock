import { renderHook, act } from '@testing-library/react';
import { useVoice } from '../useVoice';

// Mock Web Speech API
const mockSpeechRecognition = {
  start: jest.fn(),
  stop: jest.fn(),
  abort: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  continuous: false,
  interimResults: false,
  lang: 'en-US',
  maxAlternatives: 1,
  onstart: null,
  onresult: null,
  onerror: null,
  onend: null,
};

const mockSpeechSynthesis = {
  speak: jest.fn(),
  cancel: jest.fn(),
  getVoices: jest.fn(() => [
    {
      name: 'Test Voice 1',
      lang: 'en-US',
      default: true,
      localService: true,
      voiceURI: 'test-voice-1',
    },
    {
      name: 'Test Voice 2',
      lang: 'en-GB',
      default: false,
      localService: true,
      voiceURI: 'test-voice-2',
    },
  ]),
  onvoiceschanged: null,
};

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

// Setup global mocks
Object.defineProperty(window, 'SpeechRecognition', {
  writable: true,
  value: jest.fn().mockImplementation(() => mockSpeechRecognition),
});

Object.defineProperty(window, 'webkitSpeechRecognition', {
  writable: true,
  value: jest.fn().mockImplementation(() => mockSpeechRecognition),
});

Object.defineProperty(window, 'speechSynthesis', {
  writable: true,
  value: mockSpeechSynthesis,
});

Object.defineProperty(window, 'SpeechSynthesisUtterance', {
  writable: true,
  value: mockSpeechSynthesisUtterance,
});

describe('useVoice', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should initialize with correct default values', () => {
    const { result } = renderHook(() => useVoice());

    expect(result.current.isListening).toBe(false);
    expect(result.current.isSupported).toBe(true);
    expect(result.current.transcript).toBe('');
    expect(result.current.confidence).toBe(0);
    expect(result.current.error).toBe(null);
    expect(result.current.isSpeaking).toBe(false);
    expect(result.current.voices).toEqual(expect.any(Array));
  });

  it('should detect speech recognition support', () => {
    const { result } = renderHook(() => useVoice());
    expect(result.current.isSupported).toBe(true);
  });

  it('should detect when speech recognition is not supported', () => {
    // Temporarily remove speech recognition
    const originalSpeechRecognition = window.SpeechRecognition;
    const originalWebkitSpeechRecognition = window.webkitSpeechRecognition;
    
    delete (window as any).SpeechRecognition;
    delete (window as any).webkitSpeechRecognition;

    const { result } = renderHook(() => useVoice());
    expect(result.current.isSupported).toBe(false);

    // Restore
    window.SpeechRecognition = originalSpeechRecognition;
    window.webkitSpeechRecognition = originalWebkitSpeechRecognition;
  });

  it('should start listening when startListening is called', () => {
    const { result } = renderHook(() => useVoice());

    act(() => {
      result.current.startListening();
    });

    expect(mockSpeechRecognition.start).toHaveBeenCalled();
  });

  it('should stop listening when stopListening is called', () => {
    const { result } = renderHook(() => useVoice());

    // First start listening
    act(() => {
      result.current.startListening();
    });

    // Simulate recognition starting
    act(() => {
      if (mockSpeechRecognition.onstart) {
        mockSpeechRecognition.onstart();
      }
    });

    // Then stop listening
    act(() => {
      result.current.stopListening();
    });

    expect(mockSpeechRecognition.stop).toHaveBeenCalled();
  });

  it('should handle speech recognition results', () => {
    const onResult = jest.fn();
    const { result } = renderHook(() => useVoice({ onResult }));

    act(() => {
      result.current.startListening();
    });

    // Simulate recognition result
    const mockEvent = {
      resultIndex: 0,
      results: [
        {
          0: { transcript: 'test transcript', confidence: 0.9 },
          isFinal: true,
          length: 1,
        },
      ],
    };

    act(() => {
      if (mockSpeechRecognition.onresult) {
        mockSpeechRecognition.onresult(mockEvent as any);
      }
    });

    expect(result.current.transcript).toBe('test transcript');
    expect(result.current.confidence).toBe(0.9);
    expect(onResult).toHaveBeenCalledWith({
      transcript: 'test transcript',
      confidence: 0.9,
      isFinal: true,
    });
  });

  it('should handle speech recognition errors', () => {
    const onError = jest.fn();
    const { result } = renderHook(() => useVoice({ onError }));

    act(() => {
      result.current.startListening();
    });

    // Simulate recognition error
    const mockError = { error: 'no-speech' };

    act(() => {
      if (mockSpeechRecognition.onerror) {
        mockSpeechRecognition.onerror(mockError as any);
      }
    });

    expect(result.current.error).toBe('No speech detected. Please try again.');
    expect(result.current.isListening).toBe(false);
    expect(onError).toHaveBeenCalledWith('No speech detected. Please try again.');
  });

  it('should speak text using speech synthesis', () => {
    const { result } = renderHook(() => useVoice());

    act(() => {
      result.current.speak('Hello world');
    });

    expect(mockSpeechSynthesis.speak).toHaveBeenCalled();
    expect(mockSpeechSynthesisUtterance).toHaveBeenCalledWith('Hello world');
  });

  it('should stop speaking when stopSpeaking is called', () => {
    const { result } = renderHook(() => useVoice());

    act(() => {
      result.current.stopSpeaking();
    });

    expect(mockSpeechSynthesis.cancel).toHaveBeenCalled();
  });

  it('should load available voices', () => {
    const { result } = renderHook(() => useVoice());

    expect(result.current.voices.length).toBeGreaterThan(0);
    expect(result.current.voices[0].name).toBe('Test Voice 1');
    expect(result.current.selectedVoice?.name).toBe('Test Voice 1'); // Should select default voice
  });

  it('should handle voice selection', () => {
    const { result } = renderHook(() => useVoice());

    const newVoice = result.current.voices[1];

    act(() => {
      result.current.setSelectedVoice(newVoice);
    });

    expect(result.current.selectedVoice).toBe(newVoice);
  });

  it('should handle speech synthesis with custom options', () => {
    const { result } = renderHook(() => useVoice());

    const options = {
      rate: 1.5,
      pitch: 0.8,
      volume: 0.7,
      voice: result.current.voices[0],
    };

    act(() => {
      result.current.speak('Test message', options);
    });

    expect(mockSpeechSynthesis.speak).toHaveBeenCalled();
    
    // Check that utterance was created with correct options
    const utteranceCall = mockSpeechSynthesisUtterance.mock.calls[0];
    expect(utteranceCall[0]).toBe('Test message');
  });

  it('should handle continuous listening mode', () => {
    const { result } = renderHook(() => useVoice({ continuous: true }));

    act(() => {
      result.current.startListening();
    });

    expect(mockSpeechRecognition.continuous).toBe(true);
  });

  it('should handle interim results', () => {
    const onResult = jest.fn();
    const { result } = renderHook(() => useVoice({ onResult, interimResults: true }));

    act(() => {
      result.current.startListening();
    });

    // Simulate interim result
    const mockEvent = {
      resultIndex: 0,
      results: [
        {
          0: { transcript: 'interim text', confidence: 0.5 },
          isFinal: false,
          length: 1,
        },
      ],
    };

    act(() => {
      if (mockSpeechRecognition.onresult) {
        mockSpeechRecognition.onresult(mockEvent as any);
      }
    });

    expect(result.current.transcript).toBe('interim text');
    expect(onResult).toHaveBeenCalledWith({
      transcript: 'interim text',
      confidence: 0,
      isFinal: false,
    });
  });

  it('should not start listening if already listening', () => {
    const { result } = renderHook(() => useVoice());

    act(() => {
      result.current.startListening();
    });

    // Simulate recognition starting
    act(() => {
      if (mockSpeechRecognition.onstart) {
        mockSpeechRecognition.onstart();
      }
    });

    // Clear the mock to check if start is called again
    mockSpeechRecognition.start.mockClear();

    act(() => {
      result.current.startListening();
    });

    expect(mockSpeechRecognition.start).not.toHaveBeenCalled();
  });

  it('should not speak empty text', () => {
    const { result } = renderHook(() => useVoice());

    act(() => {
      result.current.speak('');
    });

    expect(mockSpeechSynthesis.speak).not.toHaveBeenCalled();

    act(() => {
      result.current.speak('   ');
    });

    expect(mockSpeechSynthesis.speak).not.toHaveBeenCalled();
  });
});