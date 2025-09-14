import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  Chip,
  useTheme,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Person as PersonIcon,
  SmartToy as BotIcon,
  Info as SystemIcon,
  MoreVert as MoreVertIcon,
  GetApp as ExportIcon,
  Share as ShareIcon,
  PictureAsPdf as PdfIcon,
  TableChart as CsvIcon,
  Code as JsonIcon,
} from '@mui/icons-material';
import { ChatMessage as ChatMessageType } from '../types';
import StockDisplay from './StockDisplay';
import StockChart from './StockChart';
import EducationalTooltip from './EducationalTooltip';
import ExportDialog from './ExportDialog';
import DisclaimerBanner from './DisclaimerBanner';
import { StockLookupResponse } from '../services/api';

interface ChatMessageProps {
  message: ChatMessageType;
  stockData?: StockLookupResponse | null;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, stockData }) => {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  
  const hasStockSymbol = message.metadata?.stockSymbol;
  const isAssistantMessage = message.type === 'assistant';
  const showExportOptions = hasStockSymbol && isAssistantMessage;

  // Financial concepts that should have educational tooltips
  const financialConcepts = [
    'P/E Ratio', 'P/E', 'Price-to-Earnings',
    'P/B Ratio', 'P/B', 'Price-to-Book',
    'ROE', 'Return on Equity',
    'Market Cap', 'Market Capitalization',
    'RSI', 'Relative Strength Index',
    'MACD', 'Moving Average Convergence Divergence',
    'SMA', 'Simple Moving Average',
    'EMA', 'Exponential Moving Average',
    'Bollinger Bands',
    'Volume',
    'Dividend Yield',
    'Beta',
    'Volatility',
    'Support', 'Resistance',
    'Bull Market', 'Bear Market',
    'Fundamental Analysis',
    'Technical Analysis'
  ];

  // Function to wrap financial concepts with educational tooltips
  const wrapWithTooltips = (text: string): React.ReactNode => {
    if (message.type !== 'assistant') {
      return text;
    }

    let processedText = text;
    const elements: React.ReactNode[] = [];
    let lastIndex = 0;

    // Sort concepts by length (longest first) to avoid partial matches
    const sortedConcepts = [...financialConcepts].sort((a, b) => b.length - a.length);

    for (const concept of sortedConcepts) {
      const regex = new RegExp(`\\b${concept.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi');
      let match;

      while ((match = regex.exec(processedText)) !== null) {
        // Add text before the match
        if (match.index > lastIndex) {
          elements.push(processedText.slice(lastIndex, match.index));
        }

        // Add the concept wrapped in tooltip
        elements.push(
          <EducationalTooltip
            key={`${concept}-${match.index}`}
            concept={concept}
            context={message.metadata?.stockSymbol}
          >
            <span style={{ 
              textDecoration: 'underline', 
              textDecorationStyle: 'dotted',
              cursor: 'help',
              color: theme.palette.primary.main
            }}>
              {match[0]}
            </span>
          </EducationalTooltip>
        );

        lastIndex = match.index + match[0].length;
        
        // Reset regex lastIndex to continue searching
        regex.lastIndex = lastIndex;
      }
    }

    // Add remaining text
    if (lastIndex < processedText.length) {
      elements.push(processedText.slice(lastIndex));
    }

    return elements.length > 0 ? elements : text;
  };

  const getMessageConfig = () => {
    switch (message.type) {
      case 'user':
        return {
          icon: <PersonIcon />,
          backgroundColor: theme.palette.primary.main,
          textColor: theme.palette.primary.contrastText,
          alignment: 'flex-end',
          avatarColor: theme.palette.primary.main,
        };
      case 'assistant':
        return {
          icon: <BotIcon />,
          backgroundColor: theme.palette.grey[100],
          textColor: theme.palette.text.primary,
          alignment: 'flex-start',
          avatarColor: theme.palette.secondary.main,
        };
      case 'system':
        return {
          icon: <SystemIcon />,
          backgroundColor: theme.palette.info.light,
          textColor: theme.palette.info.contrastText,
          alignment: 'center',
          avatarColor: theme.palette.info.main,
        };
      default:
        return {
          icon: <BotIcon />,
          backgroundColor: theme.palette.grey[100],
          textColor: theme.palette.text.primary,
          alignment: 'flex-start',
          avatarColor: theme.palette.secondary.main,
        };
    }
  };

  const config = getMessageConfig();
  const isUser = message.type === 'user';
  const isSystem = message.type === 'system';

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleExportClick = () => {
    setExportDialogOpen(true);
    handleMenuClose();
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: config.alignment,
        mb: 2,
        px: 1,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: isUser ? 'row-reverse' : 'row',
          alignItems: 'flex-start',
          maxWidth: isSystem ? '100%' : '80%',
          gap: 1,
        }}
      >
        {!isSystem && (
          <Avatar
            sx={{
              bgcolor: config.avatarColor,
              width: 32,
              height: 32,
              fontSize: '1rem',
            }}
          >
            {config.icon}
          </Avatar>
        )}
        
        <Paper
          elevation={1}
          sx={{
            p: 2,
            backgroundColor: config.backgroundColor,
            color: config.textColor,
            borderRadius: isSystem ? 1 : isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
            maxWidth: '100%',
            wordBreak: 'break-word',
            position: 'relative',
          }}
        >
          {/* Export Menu Button */}
          {showExportOptions && (
            <Box sx={{ position: 'absolute', top: 8, right: 8 }}>
              <Tooltip title="Export & Share">
                <IconButton
                  size="small"
                  onClick={handleMenuOpen}
                  sx={{
                    color: config.textColor,
                    opacity: 0.7,
                    '&:hover': { opacity: 1 },
                  }}
                >
                  <MoreVertIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
                PaperProps={{
                  sx: { minWidth: 200 }
                }}
              >
                <MenuItem onClick={handleExportClick}>
                  <ListItemIcon>
                    <ExportIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Export & Share" />
                </MenuItem>
              </Menu>
            </Box>
          )}
          <Typography
            variant="body1"
            sx={{
              whiteSpace: 'pre-wrap',
              lineHeight: 1.5,
            }}
          >
            {wrapWithTooltips(message.content)}
          </Typography>
          
          {/* Display stock data if available */}
          {stockData && message.type === 'assistant' && (
            <Box sx={{ mt: 2 }}>
              <StockDisplay stockData={stockData} />
            </Box>
          )}
          
          {/* Display charts if available */}
          {message.metadata?.charts && message.metadata.charts.length > 0 && (
            <Box sx={{ mt: 2 }}>
              {message.metadata.charts.map((chartData, index) => (
                <Box key={index} sx={{ mb: index < message.metadata!.charts!.length - 1 ? 2 : 0 }}>
                  <StockChart
                    symbol={chartData.symbol}
                    data={chartData.data}
                    timeframe={chartData.timeframe}
                    indicators={chartData.indicators}
                    annotations={chartData.annotations}
                    supportLevels={chartData.annotations?.filter(a => a.type === 'support').map(a => ({
                      level: a.value,
                      strength: 5,
                      type: 'support' as const,
                      touches: 1,
                    })) || []}
                    resistanceLevels={chartData.annotations?.filter(a => a.type === 'resistance').map(a => ({
                      level: a.value,
                      strength: 5,
                      type: 'resistance' as const,
                      touches: 1,
                    })) || []}
                    height={350}
                  />
                </Box>
              ))}
            </Box>
          )}
          
          {message.metadata?.stockSymbol && (
            <Box sx={{ mt: 1 }}>
              <Chip
                label={message.metadata.stockSymbol}
                size="small"
                variant="outlined"
                sx={{
                  borderColor: config.textColor,
                  color: config.textColor,
                }}
              />
            </Box>
          )}
          
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              mt: 1,
              opacity: 0.7,
              fontSize: '0.75rem',
            }}
          >
            {message.timestamp.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </Typography>
          
          {/* Add disclaimer for assistant messages with analysis or recommendations */}
          {message.type === 'assistant' && (
            <DisclaimerBanner
              context={
                message.content.toLowerCase().includes('recommend') || 
                message.content.toLowerCase().includes('buy') || 
                message.content.toLowerCase().includes('sell') || 
                message.content.toLowerCase().includes('hold')
                  ? 'recommendation'
                  : message.metadata?.stockSymbol
                    ? 'analysis_result'
                    : 'chat_response'
              }
              compact={true}
              symbol={message.metadata?.stockSymbol}
            />
          )}
        </Paper>
      </Box>
      
      {/* Export Dialog */}
      {showExportOptions && (
        <ExportDialog
          open={exportDialogOpen}
          onClose={() => setExportDialogOpen(false)}
          symbol={message.metadata?.stockSymbol || ''}
          analysisData={stockData}
        />
      )}
    </Box>
  );
};

export default ChatMessage;