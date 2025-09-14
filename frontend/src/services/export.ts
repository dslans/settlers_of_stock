import { apiClient } from './api';

export interface ExportFormat {
  format: string;
  name: string;
  description: string;
  mime_type: string;
  supports_charts: boolean;
}

export interface ShareLinkRequest {
  symbol: string;
  include_sentiment?: boolean;
  expires_in_hours?: number;
}

export interface ShareLinkResponse {
  link_id: string;
  share_url: string;
  expires_at: string;
  created_at: string;
}

export interface SharedAnalysis {
  analysis: any;
  sentiment?: any;
  created_at: string;
  view_count: number;
  expires_at: string;
}

export interface UserExport {
  id: string;
  symbol: string;
  format: string;
  created_at: string;
  file_url: string;
  file_size: number;
}

/**
 * Get available export formats
 */
export const getExportFormats = async (): Promise<ExportFormat[]> => {
  try {
    const response = await apiClient.get('/api/v1/export/formats');
    return response.data.formats;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to get export formats');
  }
};

/**
 * Export analysis as PDF report
 */
export const exportPdfReport = async (
  symbol: string,
  includeSentiment: boolean = true,
  includeCharts: boolean = true
): Promise<Blob> => {
  try {
    const response = await apiClient.post(
      `/api/v1/export/pdf/${symbol.toUpperCase()}`,
      {},
      {
        params: {
          include_sentiment: includeSentiment,
          include_charts: includeCharts,
        },
        responseType: 'blob',
      }
    );
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to export PDF report');
  }
};

/**
 * Export analysis data as CSV
 */
export const exportCsvData = async (
  symbol: string,
  includeSentiment: boolean = true
): Promise<Blob> => {
  try {
    const response = await apiClient.post(
      `/api/v1/export/csv/${symbol.toUpperCase()}`,
      {},
      {
        params: {
          include_sentiment: includeSentiment,
        },
        responseType: 'blob',
      }
    );
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to export CSV data');
  }
};

/**
 * Export analysis data as JSON
 */
export const exportJsonData = async (
  symbol: string,
  includeSentiment: boolean = true,
  includeMetadata: boolean = true
): Promise<Blob> => {
  try {
    const response = await apiClient.post(
      `/api/v1/export/json/${symbol.toUpperCase()}`,
      {},
      {
        params: {
          include_sentiment: includeSentiment,
          include_metadata: includeMetadata,
        },
        responseType: 'blob',
      }
    );
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to export JSON data');
  }
};

/**
 * Create a shareable link for analysis results
 */
export const createShareLink = async (
  request: ShareLinkRequest
): Promise<ShareLinkResponse> => {
  try {
    const response = await apiClient.post('/api/v1/export/share', request);
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to create shareable link');
  }
};

/**
 * Get shared analysis by link ID
 */
export const getSharedAnalysis = async (linkId: string): Promise<SharedAnalysis> => {
  try {
    const response = await apiClient.get(`/api/v1/export/share/${linkId}`);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      throw new Error('Shared link not found or expired');
    }
    throw new Error(error.response?.data?.detail || 'Failed to get shared analysis');
  }
};

/**
 * Delete a shareable link
 */
export const deleteShareLink = async (linkId: string): Promise<void> => {
  try {
    await apiClient.delete(`/api/v1/export/share/${linkId}`);
  } catch (error: any) {
    if (error.response?.status === 404) {
      throw new Error('Shared link not found or you don\'t have permission to delete it');
    }
    throw new Error(error.response?.data?.detail || 'Failed to delete shareable link');
  }
};

/**
 * Get user's recent exports
 */
export const getUserExports = async (limit: number = 10): Promise<UserExport[]> => {
  try {
    const response = await apiClient.get('/api/v1/export/user/exports', {
      params: { limit },
    });
    return response.data.exports;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to get user exports');
  }
};

/**
 * Download a file blob with a given filename
 */
export const downloadBlob = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Generate filename for export based on symbol and format
 */
export const generateExportFilename = (
  symbol: string,
  format: string,
  timestamp?: Date
): string => {
  const date = timestamp || new Date();
  const dateStr = date.toISOString().slice(0, 19).replace(/[:-]/g, '');
  return `${symbol.toUpperCase()}_analysis_${dateStr}.${format}`;
};

/**
 * Copy text to clipboard
 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    } else {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      const result = document.execCommand('copy');
      document.body.removeChild(textArea);
      return result;
    }
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
    return false;
  }
};

/**
 * Format file size in human readable format
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Validate share link expiration time
 */
export const validateExpirationHours = (hours: number): boolean => {
  return hours >= 1 && hours <= 168; // Between 1 hour and 1 week
};

/**
 * Get share URL for frontend
 */
export const getShareUrl = (linkId: string): string => {
  const baseUrl = window.location.origin;
  return `${baseUrl}/share/${linkId}`;
};