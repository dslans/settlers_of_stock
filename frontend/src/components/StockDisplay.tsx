import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Grid,
  Divider,
  useTheme,
  alpha,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
} from '@mui/icons-material';
import { StockLookupResponse } from '../services/api';

interface StockDisplayProps {
  stockData: StockLookupResponse;
}

const StockDisplay: React.FC<StockDisplayProps> = ({ stockData }) => {
  const theme = useTheme();
  const { stock, market_data } = stockData;

  // Format numbers for display
  const formatPrice = (price: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  const formatNumber = (num: number): string => {
    if (num >= 1e12) {
      return `$${(num / 1e12).toFixed(2)}T`;
    } else if (num >= 1e9) {
      return `$${(num / 1e9).toFixed(2)}B`;
    } else if (num >= 1e6) {
      return `$${(num / 1e6).toFixed(2)}M`;
    } else if (num >= 1e3) {
      return `$${(num / 1e3).toFixed(2)}K`;
    }
    return `$${num.toFixed(2)}`;
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

  const formatPercent = (percent: number): string => {
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(2)}%`;
  };

  // Determine trend direction and color
  const getTrendIcon = () => {
    if (market_data.change > 0) {
      return <TrendingUpIcon sx={{ color: theme.palette.success.main }} />;
    } else if (market_data.change < 0) {
      return <TrendingDownIcon sx={{ color: theme.palette.error.main }} />;
    } else {
      return <TrendingFlatIcon sx={{ color: theme.palette.text.secondary }} />;
    }
  };

  const getChangeColor = () => {
    if (market_data.change > 0) {
      return theme.palette.success.main;
    } else if (market_data.change < 0) {
      return theme.palette.error.main;
    } else {
      return theme.palette.text.secondary;
    }
  };

  const getChangeBackgroundColor = () => {
    if (market_data.change > 0) {
      return alpha(theme.palette.success.main, 0.1);
    } else if (market_data.change < 0) {
      return alpha(theme.palette.error.main, 0.1);
    } else {
      return alpha(theme.palette.text.secondary, 0.1);
    }
  };

  return (
    <Card 
      elevation={2} 
      sx={{ 
        maxWidth: 600, 
        margin: '16px 0',
        border: `1px solid ${theme.palette.divider}`,
      }}
    >
      <CardContent>
        {/* Header with company info */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold' }}>
              {stock.symbol}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {stock.name}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
              <Chip 
                label={stock.exchange} 
                size="small" 
                variant="outlined"
                sx={{ fontSize: '0.75rem' }}
              />
              {stock.sector && (
                <Chip 
                  label={stock.sector} 
                  size="small" 
                  variant="outlined"
                  sx={{ fontSize: '0.75rem' }}
                />
              )}
            </Box>
          </Box>
          
          {market_data.isStale && (
            <Chip 
              label="Cached Data" 
              size="small" 
              color="warning"
              sx={{ ml: 1 }}
            />
          )}
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Price and change information */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
              {formatPrice(market_data.price)}
            </Typography>
            <Box 
              sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1,
                backgroundColor: getChangeBackgroundColor(),
                padding: '4px 8px',
                borderRadius: '8px',
                mt: 1,
                width: 'fit-content'
              }}
            >
              {getTrendIcon()}
              <Typography 
                variant="body1" 
                sx={{ 
                  color: getChangeColor(),
                  fontWeight: 'medium'
                }}
              >
                {formatPrice(market_data.change)} ({formatPercent(market_data.changePercent)})
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Market data grid */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Volume
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                {formatVolume(market_data.volume)}
              </Typography>
            </Box>
          </Grid>
          
          {market_data.avgVolume && (
            <Grid item xs={6} sm={3}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Avg Volume
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                  {formatVolume(market_data.avgVolume)}
                </Typography>
              </Box>
            </Grid>
          )}
          
          {market_data.marketCap && (
            <Grid item xs={6} sm={3}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Market Cap
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                  {formatNumber(market_data.marketCap)}
                </Typography>
              </Box>
            </Grid>
          )}
          
          {market_data.peRatio && (
            <Grid item xs={6} sm={3}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  P/E Ratio
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                  {market_data.peRatio.toFixed(2)}
                </Typography>
              </Box>
            </Grid>
          )}
        </Grid>

        {/* 52-week range */}
        {market_data.high52Week && market_data.low52Week && (
          <>
            <Divider sx={{ my: 2 }} />
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                52-Week Range
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body2">
                  {formatPrice(market_data.low52Week)}
                </Typography>
                <Box 
                  sx={{ 
                    flex: 1, 
                    height: 4, 
                    backgroundColor: theme.palette.grey[300],
                    borderRadius: 2,
                    position: 'relative'
                  }}
                >
                  <Box
                    sx={{
                      position: 'absolute',
                      left: `${((market_data.price - market_data.low52Week) / 
                        (market_data.high52Week - market_data.low52Week)) * 100}%`,
                      top: -2,
                      width: 8,
                      height: 8,
                      backgroundColor: theme.palette.primary.main,
                      borderRadius: '50%',
                      transform: 'translateX(-50%)'
                    }}
                  />
                </Box>
                <Typography variant="body2">
                  {formatPrice(market_data.high52Week)}
                </Typography>
              </Box>
            </Box>
          </>
        )}

        {/* Timestamp */}
        <Box sx={{ mt: 2, pt: 1, borderTop: `1px solid ${theme.palette.divider}` }}>
          <Typography variant="caption" color="text.secondary">
            Last updated: {new Date(market_data.timestamp).toLocaleString()}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default StockDisplay;