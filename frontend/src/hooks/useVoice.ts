import { useState, useEffect, useRef, useCallback } from 'react';

interface VoiceRecognitionResult {
  transcript: string;
  confidence: number;
  isFinal: boolean;
}

interface VoiceHookOptions {
  onResult?: (result: VoiceRecognitionResult) => void;
  onError?: (error: string) => void;
  onStart?: () => void;
  onEnd?: () => void;
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
}

interface VoiceHook {
  isListening: boolean;
  isSupported: boolean;
  transcript: string;
  confidence: number;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
  speak: (text: string, options?: SpeechSynthesisUtteranceOptions) => void;
  isSpeaking: boolean;
  stopSpeaking: () => void;
  voices: SpeechSynthesisVoice[];
  selectedVoice: SpeechSynthesisVoice | null;
  setSelectedVoice: (voice: SpeechSynthesisVoice | null) => void;
}

interface SpeechSynthesisUtteranceOptions {
  rate?: number;
  pitch?: number;
  volume?: number;
  voice?: SpeechSynthesisVoice | null;
}

export const useVoice = (options: VoiceHookOptions = {}): VoiceHook => {
  const {
    onResult,
    onError,
    onStart,
    onEnd,
    language = 'en-US',
    continuous = false,
    interimResults = true,
  } = options;

  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  // Check if Web Speech API is supported
  const isSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;

  // Initialize speech synthesis
  useEffect(() => {
    if ('speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis;
      
      const loadVoices = () => {
        const availableVoices = synthRef.current?.getVoices() || [];
        setVoices(availableVoices);
        
        // Set default voice (prefer English voices)
        const englishVoice = availableVoices.find(voice => 
          voice.lang.startsWith('en') && voice.default
        ) || availableVoices.find(voice => 
          voice.lang.startsWith('en')
        ) || availableVoices[0];
        
        if (englishVoice && !selectedVoice) {
          setSelectedVoice(englishVoice);
        }
      };

      loadVoices();
      
      // Some browsers load voices asynchronously
      if (synthRef.current.onvoiceschanged !== undefined) {
        synthRef.current.onvoiceschanged = loadVoices;
      }
    }
  }, [selectedVoice]);

  // Initialize speech recognition
  useEffect(() => {
    if (!isSupported) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = continuous;
    recognition.interimResults = interimResults;
    recognition.lang = language;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
      setTranscript('');
      setConfidence(0);
      onStart?.();
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      let interimTranscript = '';
      let maxConfidence = 0;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0].transcript;
        const confidence = result[0].confidence;

        if (result.isFinal) {
          finalTranscript += transcript;
          maxConfidence = Math.max(maxConfidence, confidence);
        } else {
          interimTranscript += transcript;
        }
      }

      const currentTranscript = finalTranscript || interimTranscript;
      const currentConfidence = finalTranscript ? maxConfidence : 0;

      setTranscript(currentTranscript);
      setConfidence(currentConfidence);

      if (onResult) {
        onResult({
          transcript: currentTranscript,
          confidence: currentConfidence,
          isFinal: !!finalTranscript,
        });
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      const errorMessage = getErrorMessage(event.error);
      setError(errorMessage);
      setIsListening(false);
      onError?.(errorMessage);
    };

    recognition.onend = () => {
      setIsListening(false);
      onEnd?.();
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [isSupported, language, continuous, interimResults, onResult, onError, onStart, onEnd]);

  const startListening = useCallback(() => {
    if (!isSupported || !recognitionRef.current || isListening) return;

    try {
      recognitionRef.current.start();
    } catch (error) {
      const errorMessage = 'Failed to start voice recognition';
      setError(errorMessage);
      onError?.(errorMessage);
    }
  }, [isSupported, isListening, onError]);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current || !isListening) return;

    recognitionRef.current.stop();
  }, [isListening]);

  const speak = useCallback((text: string, options: SpeechSynthesisUtteranceOptions = {}) => {
    if (!synthRef.current || !text.trim()) return;

    // Cancel any ongoing speech
    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Set options
    utterance.rate = options.rate ?? 1;
    utterance.pitch = options.pitch ?? 1;
    utterance.volume = options.volume ?? 1;
    utterance.voice = options.voice ?? selectedVoice;

    utterance.onstart = () => {
      setIsSpeaking(true);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
    };

    utterance.onerror = (event) => {
      setIsSpeaking(false);
      const errorMessage = `Speech synthesis error: ${event.error}`;
      setError(errorMessage);
      onError?.(errorMessage);
    };

    synthRef.current.speak(utterance);
  }, [selectedVoice, onError]);

  const stopSpeaking = useCallback(() => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  }, []);

  return {
    isListening,
    isSupported,
    transcript,
    confidence,
    error,
    startListening,
    stopListening,
    speak,
    isSpeaking,
    stopSpeaking,
    voices,
    selectedVoice,
    setSelectedVoice,
  };
};

// Helper function to get user-friendly error messages
const getErrorMessage = (error: string): string => {
  switch (error) {
    case 'no-speech':
      return 'No speech detected. Please try again.';
    case 'audio-capture':
      return 'Audio capture failed. Please check your microphone.';
    case 'not-allowed':
      return 'Microphone access denied. Please allow microphone access and try again.';
    case 'network':
      return 'Network error occurred. Please check your connection.';
    case 'service-not-allowed':
      return 'Speech recognition service not allowed.';
    case 'bad-grammar':
      return 'Speech recognition grammar error.';
    case 'language-not-supported':
      return 'Language not supported for speech recognition.';
    default:
      return `Speech recognition error: ${error}`;
  }
};

// Extend the Window interface to include speech recognition
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}