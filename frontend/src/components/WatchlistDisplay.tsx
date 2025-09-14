import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  Menu,
  MenuItem,
  Tooltip,
  useTheme,
  alpha,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  MoreVert as MoreVertIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Notes as NotesIcon,
} from '@mui/icons-material';
import { Watchlist, WatchlistItem } from '../types';
import { useWatchlist } from '../hooks/useWatchlist';

interface WatchlistDisplayProps {
  watchlist: Watchlist;
  onAddStock?: () => void;
  onEditWatchlist?: () => void;
  onDeleteWatchlist?: () => void;
  onEditItem?: (item: WatchlistItem) => void;
  onRemoveItem?: (item: WatchlistItem) => void;
}

const WatchlistDisplay: React.FC<WatchlistDisplayProps> = ({
  watchlist,
  onAddStock,
  onEditWatchlist,
  onDeleteWatchlist,
  onEditItem,
  onRemoveItem,
}) => {
  const theme = useTheme();
  const { refreshData, loading, error } = useWatchlist();
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedItem, setSelectedItem] = useState<WatchlistItem | null>(null);

  // Format numbers for display
  const formatPrice = (price: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  const formatPercent = (percent: number): string => {
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(2)}%`;
  };

  const formatVolume = (volume: number): string => {
    if (volume >= 1e9) {
      return `${(volume / 1e9).toFixed(2)}B`;
    } else if (volume >= 1e6) {
      return `${(volume / 1e6).toFixed(2)}M`;
    } else if (volume >= 1e3) {
      return `${(volume / 1e3).toFixed(2)}K`;
    }
    return volume.toLocaleString();
  };

  // Get trend icon and color
  const getTrendIcon = (change?: number) => {
    if (!change) return <TrendingFlatIcon sx={{ color: theme.palette.text.secondary }} />;
    
    if (change > 0) {
      return <TrendingUpIcon sx={{ color: theme.palette.success.main }} />;
    } else if (change < 0) {
      return <TrendingDownIcon sx={{ color: theme.palette.error.main }} />;
    } else {
      return <TrendingFlatIcon sx={{ color: theme.palette.text.secondary }} />;
    }
  };

  const getChangeColor = (change?: number) => {
    if (!change) return theme.palette.text.secondary;
    
    if (change > 0) {
      return theme.palette.success.main;
    } else if (change < 0) {
      return theme.palette.error.main;
    } else {
      return theme.palette.text.secondary;
    }
  };

  // Calculate portfolio metrics
  const calculatePortfolioMetrics = () => {
    let totalValue = 0;
    let totalGainLoss = 0;
    let itemsWithData = 0;

    watchlist.items.forEach(item => {
      if (item.currentPrice && item.sharesOwned) {
        const currentValue = item.currentPrice * item.sharesOwned;
        totalValue += currentValue;
        
        if (item.entryPrice) {
          const entryValue = item.entryPrice * item.sharesOwned;
          totalGainLoss += (currentValue - entryValue);
        }
        itemsWithData++;
      }
    });

    const totalGainLossPercent = totalValue > 0 ? (totalGainLoss / (totalValue - totalGainLoss)) * 100 : 0;

    return {
      totalValue,
      totalGainLoss,
      totalGainLossPercent,
      itemsWithData,
    };
  };

  const portfolioMetrics = calculatePortfolioMetrics();

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, item: WatchlistItem) => {
    setMenuAnchor(event.currentTarget);
    setSelectedItem(item);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedItem(null);
  };

  const handleRefresh = async () => {
    await refreshData(watchlist.id);
  };

  const handleEditItem = () => {
    if (selectedItem && onEditItem) {
      onEditItem(selectedItem);
    }
    handleMenuClose();
  };

  const handleRemoveItem = () => {
    if (selectedItem && onRemoveItem) {
      onRemoveItem(selectedItem);
    }
    handleMenuClose();
  };

  return (
    <Card elevation={2}>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="h5" component="h2" sx={{ fontWeight: 'bold' }}>
                {watchlist.name}
              </Typography>
              {watchlist.isDefault && (
                <Chip label="Default" size="small" color="primary" />
              )}
            </Box>
            {watchlist.description && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {watchlist.description}
              </Typography>
            )}
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Refresh data">
              <IconButton 
                onClick={handleRefresh} 
                disabled={loading.isLoading}
                size="small"
              >
                {loading.isLoading ? (
                  <CircularProgress size={20} />
                ) : (
                  <RefreshIcon />
                )}
              </IconButton>
            </Tooltip>
            
            {onAddStock && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={onAddStock}
                size="small"
              >
                Add Stock
              </Button>
            )}
            
            {onEditWatchlist && (
              <Tooltip title="Edit watchlist">
                <IconButton onClick={onEditWatchlist} size="small">
                  <EditIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>

        {/* Portfolio Summary */}
        {portfolioMetrics.itemsWithData > 0 && (
          <Box 
            sx={{ 
              p: 2, 
              mb: 2, 
              backgroundColor: alpha(theme.palette.primary.main, 0.05),
              borderRadius: 1,
              border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
            }}
          >
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Portfolio Summary
            </Typography>
            <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Total Value
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  {formatPrice(portfolioMetrics.totalValue)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Total Gain/Loss
                </Typography>
                <Typography 
                  variant="h6" 
                  sx={{ 
                    fontWeight: 'bold',
                    color: getChangeColor(portfolioMetrics.totalGainLoss)
                  }}
                >
                  {formatPrice(portfolioMetrics.totalGainLoss)} ({formatPercent(portfolioMetrics.totalGainLossPercent)})
                </Typography>
              </Box>
            </Box>
          </Box>
        )}

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Stocks Table */}
        {watchlist.items.length > 0 ? (
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Symbol</TableCell>
                  <TableCell>Company</TableCell>
                  <TableCell align="right">Price</TableCell>
                  <TableCell align="right">Change</TableCell>
                  <TableCell align="right">Volume</TableCell>
                  <TableCell align="right">Target</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {watchlist.items.map((item) => (
                  <TableRow key={item.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          {item.symbol}
                        </Typography>
                        {item.notes && (
                          <Tooltip title={item.notes}>
                            <NotesIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" noWrap>
                        {item.companyName || item.symbol}
                      </Typography>
                    </TableCell>
                    
                    <TableCell align="right">
                      {item.currentPrice ? (
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          {formatPrice(item.currentPrice)}
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          --
                        </Typography>
                      )}
                    </TableCell>
                    
                    <TableCell align="right">
                      {item.dailyChange !== undefined && item.dailyChangePercent !== undefined ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                          {getTrendIcon(item.dailyChange)}
                          <Box>
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                color: getChangeColor(item.dailyChange),
                                fontWeight: 'medium'
                              }}
                            >
                              {formatPrice(item.dailyChange)}
                            </Typography>
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                color: getChangeColor(item.dailyChange),
                                display: 'block'
                              }}
                            >
                              {formatPercent(item.dailyChangePercent)}
                            </Typography>
                          </Box>
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          --
                        </Typography>
                      )}
                    </TableCell>
                    
                    <TableCell align="right">
                      {item.volume ? (
                        <Typography variant="body2">
                          {formatVolume(item.volume)}
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          --
                        </Typography>
                      )}
                    </TableCell>
                    
                    <TableCell align="right">
                      {item.targetPrice ? (
                        <Typography variant="body2">
                          {formatPrice(item.targetPrice)}
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          --
                        </Typography>
                      )}
                    </TableCell>
                    
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, item)}
                      >
                        <MoreVertIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Box 
            sx={{ 
              textAlign: 'center', 
              py: 4,
              color: 'text.secondary'
            }}
          >
            <Typography variant="body1" gutterBottom>
              No stocks in this watchlist yet
            </Typography>
            {onAddStock && (
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={onAddStock}
                sx={{ mt: 1 }}
              >
                Add Your First Stock
              </Button>
            )}
          </Box>
        )}

        {/* Item Actions Menu */}
        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleEditItem}>
            <EditIcon sx={{ mr: 1, fontSize: 20 }} />
            Edit
          </MenuItem>
          <MenuItem onClick={handleRemoveItem} sx={{ color: 'error.main' }}>
            <DeleteIcon sx={{ mr: 1, fontSize: 20 }} />
            Remove
          </MenuItem>
        </Menu>
      </CardContent>
    </Card>
  );
};

export default WatchlistDisplay;