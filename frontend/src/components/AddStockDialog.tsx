import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  Chip,
  Alert,
  CircularProgress,
  Autocomplete,
  Tabs,
  Tab,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useWatchlist } from '../hooks/useWatchlist';
import { validateSymbol } from '../services/api';
import { WatchlistItemCreateRequest, WatchlistBulkAddRequest } from '../types';

interface AddStockDialogProps {
  open: boolean;
  onClose: () => void;
  watchlistId: number;
  watchlistName: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`add-stock-tabpanel-${index}`}
      aria-labelledby={`add-stock-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
};

const AddStockDialog: React.FC<AddStockDialogProps> = ({
  open,
  onClose,
  watchlistId,
  watchlistName,
}) => {
  const { addStock, bulkAddStocks, loading, error } = useWatchlist();
  
  const [tabValue, setTabValue] = useState(0);
  const [validationLoading, setValidationLoading] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  
  // Single stock form
  const [singleStockForm, setSingleStockForm] = useState({
    symbol: '',
    companyName: '',
    notes: '',
    targetPrice: '',
    entryPrice: '',
    sharesOwned: '',
  });
  
  // Bulk add form
  const [bulkSymbols, setBulkSymbols] = useState('');
  const [bulkResult, setBulkResult] = useState<any>(null);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setValidationError(null);
    setBulkResult(null);
  };

  const handleSingleStockChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setSingleStockForm(prev => ({
      ...prev,
      [field]: event.target.value,
    }));
    setValidationError(null);
  };

  const validateSingleSymbol = async (symbol: string) => {
    if (!symbol.trim()) return;
    
    try {
      setValidationLoading(true);
      setValidationError(null);
      
      const result = await validateSymbol(symbol.trim());
      
      if (!result.isValid) {
        setValidationError(`Invalid symbol: ${symbol}. ${result.suggestions.join(', ')}`);
      }
    } catch (error) {
      setValidationError(error instanceof Error ? error.message : 'Failed to validate symbol');
    } finally {
      setValidationLoading(false);
    }
  };

  const handleSymbolBlur = () => {
    if (singleStockForm.symbol) {
      validateSingleSymbol(singleStockForm.symbol);
    }
  };

  const handleSingleStockSubmit = async () => {
    try {
      const stockData: WatchlistItemCreateRequest = {
        symbol: singleStockForm.symbol.trim().toUpperCase(),
        companyName: singleStockForm.companyName.trim() || undefined,
        notes: singleStockForm.notes.trim() || undefined,
        targetPrice: singleStockForm.targetPrice ? parseFloat(singleStockForm.targetPrice) : undefined,
        entryPrice: singleStockForm.entryPrice ? parseFloat(singleStockForm.entryPrice) : undefined,
        sharesOwned: singleStockForm.sharesOwned ? parseFloat(singleStockForm.sharesOwned) : undefined,
      };
      
      await addStock(watchlistId, stockData);
      handleClose();
    } catch (error) {
      // Error is handled by the hook
    }
  };

  const handleBulkSubmit = async () => {
    try {
      const symbols = bulkSymbols
        .split(/[,\n\s]+/)
        .map(s => s.trim().toUpperCase())
        .filter(s => s.length > 0);
      
      if (symbols.length === 0) {
        setValidationError('Please enter at least one symbol');
        return;
      }
      
      const bulkData: WatchlistBulkAddRequest = { symbols };
      const result = await bulkAddStocks(watchlistId, bulkData);
      setBulkResult(result);
      
      if (result.totalFailed === 0) {
        // All successful, close dialog after a short delay
        setTimeout(() => {
          handleClose();
        }, 2000);
      }
    } catch (error) {
      // Error is handled by the hook
    }
  };

  const handleClose = () => {
    setSingleStockForm({
      symbol: '',
      companyName: '',
      notes: '',
      targetPrice: '',
      entryPrice: '',
      sharesOwned: '',
    });
    setBulkSymbols('');
    setBulkResult(null);
    setValidationError(null);
    setTabValue(0);
    onClose();
  };

  const isSingleStockFormValid = singleStockForm.symbol.trim().length > 0 && !validationError;
  const isBulkFormValid = bulkSymbols.trim().length > 0;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Add Stocks to "{watchlistName}"
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Single Stock" />
            <Tab label="Bulk Add" />
          </Tabs>
        </Box>

        {/* Single Stock Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Stock Symbol"
              value={singleStockForm.symbol}
              onChange={handleSingleStockChange('symbol')}
              onBlur={handleSymbolBlur}
              placeholder="e.g., AAPL, GOOGL, TSLA"
              required
              error={!!validationError}
              helperText={validationError}
              InputProps={{
                endAdornment: validationLoading && <CircularProgress size={20} />,
              }}
            />
            
            <TextField
              label="Company Name (Optional)"
              value={singleStockForm.companyName}
              onChange={handleSingleStockChange('companyName')}
              placeholder="Will be auto-filled if left empty"
            />
            
            <TextField
              label="Notes (Optional)"
              value={singleStockForm.notes}
              onChange={handleSingleStockChange('notes')}
              multiline
              rows={2}
              placeholder="Your thoughts, analysis, or reminders about this stock"
            />
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="Target Price (Optional)"
                value={singleStockForm.targetPrice}
                onChange={handleSingleStockChange('targetPrice')}
                type="number"
                inputProps={{ step: 0.01, min: 0 }}
                placeholder="0.00"
              />
              
              <TextField
                label="Entry Price (Optional)"
                value={singleStockForm.entryPrice}
                onChange={handleSingleStockChange('entryPrice')}
                type="number"
                inputProps={{ step: 0.01, min: 0 }}
                placeholder="0.00"
              />
              
              <TextField
                label="Shares Owned (Optional)"
                value={singleStockForm.sharesOwned}
                onChange={handleSingleStockChange('sharesOwned')}
                type="number"
                inputProps={{ step: 0.0001, min: 0 }}
                placeholder="0"
              />
            </Box>
          </Box>
        </TabPanel>

        {/* Bulk Add Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Enter multiple stock symbols separated by commas, spaces, or new lines.
            </Typography>
            
            <TextField
              label="Stock Symbols"
              value={bulkSymbols}
              onChange={(e) => setBulkSymbols(e.target.value)}
              multiline
              rows={6}
              placeholder="AAPL, GOOGL, MSFT, TSLA&#10;AMZN NVDA&#10;META"
              fullWidth
            />
            
            {bulkResult && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Results:
                </Typography>
                
                {bulkResult.totalAdded > 0 && (
                  <Alert severity="success" sx={{ mb: 1 }}>
                    Successfully added {bulkResult.totalAdded} stocks: {bulkResult.addedSymbols.join(', ')}
                  </Alert>
                )}
                
                {bulkResult.totalFailed > 0 && (
                  <Alert severity="warning">
                    <Typography variant="body2" gutterBottom>
                      Failed to add {bulkResult.totalFailed} stocks:
                    </Typography>
                    {bulkResult.failedSymbols.map((failed: any, index: number) => (
                      <Typography key={index} variant="caption" display="block">
                        • {failed.symbol}: {failed.error}
                      </Typography>
                    ))}
                  </Alert>
                )}
              </Box>
            )}
          </Box>
        </TabPanel>

        {/* General Error Display */}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose}>
          Cancel
        </Button>
        
        {tabValue === 0 ? (
          <Button
            onClick={handleSingleStockSubmit}
            variant="contained"
            disabled={!isSingleStockFormValid || loading.isLoading || validationLoading}
            startIcon={loading.isLoading ? <CircularProgress size={16} /> : <AddIcon />}
          >
            Add Stock
          </Button>
        ) : (
          <Button
            onClick={handleBulkSubmit}
            variant="contained"
            disabled={!isBulkFormValid || loading.isLoading}
            startIcon={loading.isLoading ? <CircularProgress size={16} /> : <AddIcon />}
          >
            Add Stocks
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default AddStockDialog;