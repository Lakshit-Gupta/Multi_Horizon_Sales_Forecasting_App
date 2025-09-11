import axios from 'axios';
import { getAuthToken } from '../services/auth';
import { API_URL } from '@env';

// Create an axios instance for the forecast API
export const forecastApi = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercept requests to add auth token
forecastApi.interceptors.request.use(
  async (config) => {
    try {
      const token = await getAuthToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.log('Not authenticated');
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Create a separate instance for GCP backend
export const gcpApi = {
  // Check if the GCP backend is healthy
  checkHealth: async () => {
    try {
      const response = await axios.get(`${API_URL}/health`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Direct file upload (GCP doesn't use pre-signed URLs)
  uploadFile: async (fileUri: string, fileName: string, mimeType: string) => {
    try {
      const token = await getAuthToken();
      
      const formData = new FormData();
      formData.append('file', {
        uri: fileUri,
        name: fileName || 'upload.xlsx',
        type: mimeType || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      } as any);
      
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data;
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    }
  },
  
  // Get template download URL
  getTemplateUrl: async () => {
    try {
      const token = await getAuthToken();
      // Return the direct download URL for the minimal API
      return `${API_URL}/download-template`; 
    } catch (error) {
      throw error;
    }
  },

  // Submit forecast request
  submitForecastRequest: async (data: any) => {
    try {
      const token = await getAuthToken();
      const response = await axios.post(`${API_URL}/forecast`, data, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Get latest forecast
  getLatestForecast: async () => {
    try {
      const token = await getAuthToken();
      const response = await axios.get(`${API_URL}/forecast`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  // Get historical data
  getHistoricalData: async () => {
    try {
      const token = await getAuthToken();
      const response = await axios.get(`${API_URL}/historical-data`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },
};

// Auth functions
export const register = async (email: string, password: string, storeName: string) => {
  try {
    const response = await axios.post(`${API_URL}/register`, {
      email,
      password,
      storeName
    });
    return response.data;
  } catch (error: any) {
    console.error('Registration error:', error);
    throw error.response?.data || { error: 'Registration failed' };
  }
};

// Generic API methods
export const api = {
  async get(endpoint: string) {
    try {
      const token = await getAuthToken();
      const response = await axios.get(`${API_URL}${endpoint}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching ${endpoint}:`, error);
      throw error;
    }
  },
  
  async post(endpoint: string, data: any) {
    try {
      const token = await getAuthToken();
      const response = await axios.post(`${API_URL}${endpoint}`, data, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      return response.data;
    } catch (error) {
      console.error(`Error posting to ${endpoint}:`, error);
      throw error;
    }
  },
  
  async uploadFile(endpoint: string, file: any) {
    try {
      const token = await getAuthToken();
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API_URL}${endpoint}`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error(`Error uploading to ${endpoint}:`, error);
      throw error;
    }
  }
};

export default api;