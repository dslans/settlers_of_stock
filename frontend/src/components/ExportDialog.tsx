import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormGroup,
  Checkbox,
  TextField,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Divider,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Share as ShareIcon,
  ContentCopy as CopyIcon,
  Close as CloseIcon,
  PictureAsPdf as PdfIcon,
  TableChart as CsvIcon,
  Code as JsonIcon,
} from '@mui/icons-material';
import {
  getExportFormats,
  exportPdfReport,
  exportCsvData,
  exportJsonData,
  createShareLink,
  downloadBlob,
  generateExportFilename,
  copyToClipboard,
  getShareUrl,
  validateExpirationHours,
  ExportFormat,
  ShareLinkResponse,
} from '../services/export';

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
  symbol: string;
  analysisData?: any;
}

const ExportDialog: React.FC<ExportDialogProps> = ({
  open,
  onClose,
  symbol,
  analysisData,
}) => {
  const [exportFormats, setExportFormats] = useState<ExportFormat[]>([]);
  const [selectedFormat, setSelectedFormat] = useState<string>('pdf');
  const [includeSentiment, setIncludeSentiment] = useState<boolean>(true);
  const [includeCharts, setIncludeCharts] = useState<boolean>(true);
  const [includeMetadata, setIncludeMetadata] = useState<boolean>(true);
  const [expirationHours, setExpirationHours] = useState<number>(24);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [isCreatingLink, setIsCreatingLink] = useState<boolean>(false);
  const [shareLink, setShareLink] = useState<ShareLinkResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load export formats on mount
  useEffect(() => {
    const loadFormats = async () => {
      try {
        const formats = await getExportFormats();
        setExportFormats(formats);
      } catch (error: any) {
        setError(error.message);
      }
    };

    if (open) {
      loadFormats();
    }
  }, [open]);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (open) {
      setError(null);
      setSuccess(null);
      setShareLink(null);
    }
  }, [open]);

  const handleExport = async () => {
    if (!symbol) return;

    setIsExporting(true);
    setError(null);
    setSuccess(null);

    try {
      let blob: Blob;
      let filename: string;

      switch (selectedFormat) {
        case 'pdf':
          blob = await exportPdfReport(symbol, includeSentiment, includeCharts);
          filename = generateExportFilename(symbol, 'pdf');
          break;
        case 'csv':
          blob = await exportCsvData(symbol, includeSentiment);
          filename = generateExportFilename(symbol, 'csv');
          break;
        case 'json':
          blob = await exportJsonData(symbol, includeSentiment, includeMetadata);
          filename = generateExportFilename(symbol, 'json');
          break;
        default:
          throw new Error('Invalid export format');
      }

      downloadBlob(blob, filename);
      setSuccess(`${selectedFormat.toUpperCase()} export downloaded successfully!`);
    } catch (error: any) {
      setError(error.message);
    } finally {
      setIsExporting(false);
    }
  };

  const handleCreateShareLink = async () => {
    if (!symbol) return;

    if (!validateExpirationHours(expirationHours)) {
      setError('Expiration time must be between 1 and 168 hours');
      return;
    }

    setIsCreatingLink(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await createShareLink({
        symbol,
        include_sentiment: includeSentiment,
        expires_in_hours: expirationHours,
      });

      setShareLink(response);
      setSuccess('Shareable link created successfully!');
    } catch (error: any) {
      setError(error.message);
    } finally {
      setIsCreatingLink(false);
    }
  };

  const handleCopyShareLink = async () => {
    if (!shareLink) return;

    const fullUrl = getShareUrl(shareLink.link_id);
    const success = await copyToClipboard(fullUrl);

    if (success) {
      setSuccess('Share link copied to clipboard!');
    } else {
      setError('Failed to copy link to clipboard');
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf':
        return <PdfIcon />;
      case 'csv':
        return <CsvIcon />;
      case 'json':
        return <JsonIcon />;
      default:
        return <DownloadIcon />;
    }
  };

  const selectedFormatData = exportFormats.find(f => f.format === selectedFormat);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { borderRadius: 2 }
      }}
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h6">Export & Share Analysis</Typography>
          <Typography variant="body2" color="text.secondary">
            {symbol ? `${symbol.toUpperCase()} Analysis` : 'Stock Analysis'}
          </Typography>
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        {/* Export Section */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DownloadIcon />
            Export Analysis
          </Typography>

          <FormControl component="fieldset" sx={{ mb: 2 }}>
            <FormLabel component="legend">Export Format</FormLabel>
            <RadioGroup
              value={selectedFormat}
              onChange={(e) => setSelectedFormat(e.target.value)}
              sx={{ mt: 1 }}
            >
              {exportFormats.map((format) => (
                <FormControlLabel
                  key={format.format}
                  value={format.format}
                  control={<Radio />}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getFormatIcon(format.format)}
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {format.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {format.description}
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
              ))}
            </RadioGroup>
          </FormControl>

          {selectedFormatData && (
            <Box sx={{ mb: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary">
                <strong>Format:</strong> {selectedFormatData.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                <strong>Type:</strong> {selectedFormatData.mime_type}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                <strong>Charts:</strong> {selectedFormatData.supports_charts ? 'Supported' : 'Not supported'}
              </Typography>
            </Box>
          )}

          <FormGroup sx={{ mb: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={includeSentiment}
                  onChange={(e) => setIncludeSentiment(e.target.checked)}
                />
              }
              label="Include sentiment analysis"
            />
            {selectedFormatData?.supports_charts && (
              <FormControlLabel
                control={
                  <Checkbox
                    checked={includeCharts}
                    onChange={(e) => setIncludeCharts(e.target.checked)}
                  />
                }
                label="Include charts and visualizations"
              />
            )}
            {selectedFormat === 'json' && (
              <FormControlLabel
                control={
                  <Checkbox
                    checked={includeMetadata}
                    onChange={(e) => setIncludeMetadata(e.target.checked)}
                  />
                }
                label="Include export metadata"
              />
            )}
          </FormGroup>

          <Button
            variant="contained"
            startIcon={isExporting ? <CircularProgress size={20} /> : <DownloadIcon />}
            onClick={handleExport}
            disabled={isExporting || !symbol}
            fullWidth
            sx={{ mb: 2 }}
          >
            {isExporting ? 'Exporting...' : `Export as ${selectedFormat.toUpperCase()}`}
          </Button>
        </Box>

        <Divider sx={{ my: 3 }} />

        {/* Share Section */}
        <Box>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ShareIcon />
            Share Analysis
          </Typography>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Create a shareable link that others can use to view this analysis.
          </Typography>

          <Box sx={{ mb: 2 }}>
            <TextField
              label="Link expires in (hours)"
              type="number"
              value={expirationHours}
              onChange={(e) => setExpirationHours(Number(e.target.value))}
              inputProps={{ min: 1, max: 168 }}
              size="small"
              sx={{ width: 200, mr: 2 }}
            />
            <Typography variant="caption" color="text.secondary">
              Maximum 168 hours (1 week)
            </Typography>
          </Box>

          <FormGroup sx={{ mb: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={includeSentiment}
                  onChange={(e) => setIncludeSentiment(e.target.checked)}
                />
              }
              label="Include sentiment analysis in shared link"
            />
          </FormGroup>

          {shareLink ? (
            <Box sx={{ p: 2, bgcolor: 'success.light', borderRadius: 1, mb: 2 }}>
              <Typography variant="body2" fontWeight="medium" gutterBottom>
                Shareable Link Created
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <TextField
                  value={getShareUrl(shareLink.link_id)}
                  size="small"
                  fullWidth
                  InputProps={{
                    readOnly: true,
                    endAdornment: (
                      <Tooltip title="Copy to clipboard">
                        <IconButton onClick={handleCopyShareLink} size="small">
                          <CopyIcon />
                        </IconButton>
                      </Tooltip>
                    ),
                  }}
                />
              </Box>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  label={`Expires: ${new Date(shareLink.expires_at).toLocaleString()}`}
                  size="small"
                  color="info"
                />
                <Chip
                  label={`Created: ${new Date(shareLink.created_at).toLocaleString()}`}
                  size="small"
                  variant="outlined"
                />
              </Box>
            </Box>
          ) : (
            <Button
              variant="outlined"
              startIcon={isCreatingLink ? <CircularProgress size={20} /> : <ShareIcon />}
              onClick={handleCreateShareLink}
              disabled={isCreatingLink || !symbol}
              fullWidth
            >
              {isCreatingLink ? 'Creating Link...' : 'Create Shareable Link'}
            </Button>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ExportDialog;