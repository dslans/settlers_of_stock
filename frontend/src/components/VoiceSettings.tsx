import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Typography,
  Box,
  Switch,
  FormControlLabel,
  Alert,
  Divider,
} from '@mui/material';
import {
  VolumeUp as VolumeUpIcon,
  Speed as SpeedIcon,
  GraphicEq as PitchIcon,
} from '@mui/icons-material';

interface VoiceSettingsProps {
  open: boolean;
  onClose: () => void;
  voices: SpeechSynthesisVoice[];
  selectedVoice: SpeechSynthesisVoice | null;
  onVoiceChange: (voice: SpeechSynthesisVoice | null) => void;
  speechRate: number;
  onSpeechRateChange: (rate: number) => void;
  speechPitch: number;
  onSpeechPitchChange: (pitch: number) => void;
  speechVolume: number;
  onSpeechVolumeChange: (volume: number) => void;
  autoSpeak: boolean;
  onAutoSpeakChange: (enabled: boolean) => void;
  continuousListening: boolean;
  onContinuousListeningChange: (enabled: boolean) => void;
}

const VoiceSettings: React.FC<VoiceSettingsProps> = ({
  open,
  onClose,
  voices,
  selectedVoice,
  onVoiceChange,
  speechRate,
  onSpeechRateChange,
  speechPitch,
  onSpeechPitchChange,
  speechVolume,
  onSpeechVolumeChange,
  autoSpeak,
  onAutoSpeakChange,
  continuousListening,
  onContinuousListeningChange,
}) => {
  const [testText] = useState('This is a test of the voice synthesis settings.');

  const handleTestVoice = () => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(testText);
      utterance.voice = selectedVoice;
      utterance.rate = speechRate;
      utterance.pitch = speechPitch;
      utterance.volume = speechVolume;
      
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleReset = () => {
    onSpeechRateChange(1);
    onSpeechPitchChange(1);
    onSpeechVolumeChange(1);
    onAutoSpeakChange(true);
    onContinuousListeningChange(false);
    
    // Reset to default voice
    const defaultVoice = voices.find(voice => voice.default) || voices[0];
    if (defaultVoice) {
      onVoiceChange(defaultVoice);
    }
  };

  // Group voices by language
  const groupedVoices = voices.reduce((groups, voice) => {
    const lang = voice.lang.split('-')[0];
    if (!groups[lang]) {
      groups[lang] = [];
    }
    groups[lang].push(voice);
    return groups;
  }, {} as Record<string, SpeechSynthesisVoice[]>);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Voice Settings</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 1 }}>
          {/* Voice Selection */}
          <FormControl fullWidth>
            <InputLabel>Voice</InputLabel>
            <Select
              value={selectedVoice?.name || ''}
              onChange={(e) => {
                const voice = voices.find(v => v.name === e.target.value) || null;
                onVoiceChange(voice);
              }}
              label="Voice"
            >
              {Object.entries(groupedVoices).map(([lang, langVoices]) => [
                <MenuItem key={`${lang}-header`} disabled sx={{ fontWeight: 'bold' }}>
                  {lang.toUpperCase()} Voices
                </MenuItem>,
                ...langVoices.map((voice) => (
                  <MenuItem key={voice.name} value={voice.name}>
                    {voice.name} {voice.default ? '(Default)' : ''}
                  </MenuItem>
                ))
              ])}
            </Select>
          </FormControl>

          {/* Speech Rate */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <SpeedIcon color="action" />
              <Typography variant="body2">
                Speech Rate: {speechRate.toFixed(1)}x
              </Typography>
            </Box>
            <Slider
              value={speechRate}
              onChange={(_, value) => onSpeechRateChange(value as number)}
              min={0.5}
              max={2}
              step={0.1}
              marks={[
                { value: 0.5, label: '0.5x' },
                { value: 1, label: '1x' },
                { value: 1.5, label: '1.5x' },
                { value: 2, label: '2x' },
              ]}
            />
          </Box>

          {/* Speech Pitch */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <PitchIcon color="action" />
              <Typography variant="body2">
                Speech Pitch: {speechPitch.toFixed(1)}
              </Typography>
            </Box>
            <Slider
              value={speechPitch}
              onChange={(_, value) => onSpeechPitchChange(value as number)}
              min={0.5}
              max={2}
              step={0.1}
              marks={[
                { value: 0.5, label: 'Low' },
                { value: 1, label: 'Normal' },
                { value: 2, label: 'High' },
              ]}
            />
          </Box>

          {/* Speech Volume */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <VolumeUpIcon color="action" />
              <Typography variant="body2">
                Speech Volume: {Math.round(speechVolume * 100)}%
              </Typography>
            </Box>
            <Slider
              value={speechVolume}
              onChange={(_, value) => onSpeechVolumeChange(value as number)}
              min={0}
              max={1}
              step={0.1}
              marks={[
                { value: 0, label: '0%' },
                { value: 0.5, label: '50%' },
                { value: 1, label: '100%' },
              ]}
            />
          </Box>

          <Divider />

          {/* Voice Options */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Voice Options
            </Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={autoSpeak}
                  onChange={(e) => onAutoSpeakChange(e.target.checked)}
                />
              }
              label="Auto-speak responses"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={continuousListening}
                  onChange={(e) => onContinuousListeningChange(e.target.checked)}
                />
              }
              label="Continuous listening mode"
            />
          </Box>

          {/* Test Voice */}
          <Box>
            <Button
              variant="outlined"
              onClick={handleTestVoice}
              fullWidth
              disabled={!selectedVoice}
            >
              Test Voice Settings
            </Button>
          </Box>

          {/* Browser Support Info */}
          {!('speechSynthesis' in window) && (
            <Alert severity="warning">
              Speech synthesis is not supported in your browser. Voice output will not work.
            </Alert>
          )}

          {!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) && (
            <Alert severity="warning">
              Speech recognition is not supported in your browser. Voice input will not work.
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleReset} color="secondary">
          Reset to Defaults
        </Button>
        <Button onClick={onClose} color="primary" variant="contained">
          Done
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default VoiceSettings;