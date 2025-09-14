import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Menu,
  MenuItem,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { useWatchlist } from '../hooks/useWatchlist';
import { WatchlistCreateRequest, WatchlistUpdateRequest, WatchlistSummary } from '../types';

interface WatchlistManagerProps {
  onSelectWatchlist?: (watchlistId: number) => void;
  selectedWatchlistId?: number;
}

const WatchlistManager: React.FC<WatchlistManagerProps> = ({
  onSelectWatchlist,
  selectedWatchlistId,
}) => {
  const {
    watchlists,
    loading,
    error,
    loadWatchlists,
    createNewWatchlist,
    updateExistingWatchlist,
    deleteExistingWatchlist,
    clearError,
  } = useWatchlist();

  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedWatchlist, setSelectedWatchlist] = useState<WatchlistSummary | null>(null);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    isDefault: false,
  });

  useEffect(() => {
    loadWatchlists();
  }, [loadWatchlists]);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, watchlist: WatchlistSummary) => {
    setMenuAnchor(event.currentTarget);
    setSelectedWatchlist(watchlist);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedWatchlist(null);
  };

  const handleCreateOpen = () => {
    setFormData({
      name: '',
      description: '',
      isDefault: false,
    });
    setCreateDialogOpen(true);
  };

  const handleEditOpen = () => {
    if (selectedWatchlist) {
      setFormData({
        name: selectedWatchlist.name,
        description: selectedWatchlist.description || '',
        isDefault: selectedWatchlist.isDefault,
      });
      setEditDialogOpen(true);
    }
    handleMenuClose();
  };

  const handleDeleteOpen = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleViewWatchlist = () => {
    if (selectedWatchlist && onSelectWatchlist) {
      onSelectWatchlist(selectedWatchlist.id);
    }
    handleMenuClose();
  };

  const handleCreateSubmit = async () => {
    try {
      const createData: WatchlistCreateRequest = {
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        isDefault: formData.isDefault,
      };
      
      await createNewWatchlist(createData);
      setCreateDialogOpen(false);
      setFormData({ name: '', description: '', isDefault: false });
    } catch (error) {
      // Error is handled by the hook
    }
  };

  const handleEditSubmit = async () => {
    if (!selectedWatchlist) return;
    
    try {
      const updateData: WatchlistUpdateRequest = {
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        isDefault: formData.isDefault,
      };
      
      await updateExistingWatchlist(selectedWatchlist.id, updateData);
      setEditDialogOpen(false);
      setSelectedWatchlist(null);
    } catch (error) {
      // Error is handled by the hook
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedWatchlist) return;
    
    try {
      await deleteExistingWatchlist(selectedWatchlist.id);
      setDeleteDialogOpen(false);
      setSelectedWatchlist(null);
    } catch (error) {
      // Error is handled by the hook
    }
  };

  const handleFormChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.type === 'checkbox' ? event.target.checked : event.target.value,
    }));
  };

  const isFormValid = formData.name.trim().length > 0;

  return (
    <Card elevation={2}>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" component="h2" sx={{ fontWeight: 'bold' }}>
            My Watchlists
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateOpen}
            size="small"
          >
            New Watchlist
          </Button>
        </Box>

        {/* Error Display */}
        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: 2 }}
            onClose={clearError}
          >
            {error}
          </Alert>
        )}

        {/* Loading State */}
        {loading.isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress size={24} />
            <Typography variant="body2" sx={{ ml: 1 }}>
              {loading.message}
            </Typography>
          </Box>
        )}

        {/* Watchlists List */}
        {watchlists.length > 0 ? (
          <List>
            {watchlists.map((watchlist, index) => (
              <React.Fragment key={watchlist.id}>
                <ListItem
                  button
                  selected={selectedWatchlistId === watchlist.id}
                  onClick={() => onSelectWatchlist?.(watchlist.id)}
                  sx={{
                    borderRadius: 1,
                    mb: 0.5,
                    '&.Mui-selected': {
                      backgroundColor: 'primary.50',
                      '&:hover': {
                        backgroundColor: 'primary.100',
                      },
                    },
                  }}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                          {watchlist.name}
                        </Typography>
                        {watchlist.isDefault && (
                          <StarIcon sx={{ fontSize: 16, color: 'primary.main' }} />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 0.5 }}>
                        {watchlist.description && (
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {watchlist.description}
                          </Typography>
                        )}
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                          <Chip
                            label={`${watchlist.totalItems} stocks`}
                            size="small"
                            variant="outlined"
                          />
                          <Typography variant="caption" color="text.secondary">
                            Updated {new Date(watchlist.updatedAt).toLocaleDateString()}
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleMenuOpen(e, watchlist);
                      }}
                      size="small"
                    >
                      <MoreVertIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
                {index < watchlists.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        ) : !loading.isLoading ? (
          <Box sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
            <Typography variant="body1" gutterBottom>
              No watchlists found
            </Typography>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={handleCreateOpen}
              sx={{ mt: 1 }}
            >
              Create Your First Watchlist
            </Button>
          </Box>
        ) : null}

        {/* Actions Menu */}
        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleViewWatchlist}>
            <VisibilityIcon sx={{ mr: 1, fontSize: 20 }} />
            View
          </MenuItem>
          <MenuItem onClick={handleEditOpen}>
            <EditIcon sx={{ mr: 1, fontSize: 20 }} />
            Edit
          </MenuItem>
          <MenuItem onClick={handleDeleteOpen} sx={{ color: 'error.main' }}>
            <DeleteIcon sx={{ mr: 1, fontSize: 20 }} />
            Delete
          </MenuItem>
        </Menu>

        {/* Create Watchlist Dialog */}
        <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Create New Watchlist</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Watchlist Name"
              fullWidth
              variant="outlined"
              value={formData.name}
              onChange={handleFormChange('name')}
              error={formData.name.length > 0 && formData.name.trim().length === 0}
              helperText={formData.name.length > 0 && formData.name.trim().length === 0 ? 'Name is required' : ''}
            />
            <TextField
              margin="dense"
              label="Description (Optional)"
              fullWidth
              variant="outlined"
              multiline
              rows={2}
              value={formData.description}
              onChange={handleFormChange('description')}
              sx={{ mt: 2 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.isDefault}
                  onChange={handleFormChange('isDefault')}
                />
              }
              label="Set as default watchlist"
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleCreateSubmit} 
              variant="contained"
              disabled={!isFormValid || loading.isLoading}
            >
              Create
            </Button>
          </DialogActions>
        </Dialog>

        {/* Edit Watchlist Dialog */}
        <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Edit Watchlist</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Watchlist Name"
              fullWidth
              variant="outlined"
              value={formData.name}
              onChange={handleFormChange('name')}
              error={formData.name.length > 0 && formData.name.trim().length === 0}
              helperText={formData.name.length > 0 && formData.name.trim().length === 0 ? 'Name is required' : ''}
            />
            <TextField
              margin="dense"
              label="Description (Optional)"
              fullWidth
              variant="outlined"
              multiline
              rows={2}
              value={formData.description}
              onChange={handleFormChange('description')}
              sx={{ mt: 2 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.isDefault}
                  onChange={handleFormChange('isDefault')}
                />
              }
              label="Set as default watchlist"
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleEditSubmit} 
              variant="contained"
              disabled={!isFormValid || loading.isLoading}
            >
              Save Changes
            </Button>
          </DialogActions>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
          <DialogTitle>Delete Watchlist</DialogTitle>
          <DialogContent>
            <Typography>
              Are you sure you want to delete "{selectedWatchlist?.name}"? This action cannot be undone.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleDeleteConfirm} 
              color="error"
              variant="contained"
              disabled={loading.isLoading}
            >
              Delete
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default WatchlistManager;