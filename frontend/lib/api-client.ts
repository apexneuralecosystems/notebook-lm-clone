import axios from 'axios';

// Get API URL from environment variable
// Next.js automatically reads .env file during build
// In local: use .env.local
// In production (Dokploy): use .env file
const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Validate at runtime only (not during build) to allow build to complete
// This allows Next.js to read .env file during build without throwing errors
if (typeof window !== 'undefined' && !API_URL) {
  // Runtime validation (client-side only)
  console.error('NEXT_PUBLIC_API_URL environment variable is required');
  console.error('Please set it in .env.local (local) or .env (production)');
  throw new Error('NEXT_PUBLIC_API_URL is not set. Please configure it in your .env file.');
}

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Enhanced error logging for connection issues
    if (!error.response) {
      // Network error - backend not reachable
      console.error('Network Error:', {
        message: error.message,
        apiUrl: API_URL,
        code: error.code,
        suggestion: 'Make sure the backend server is running and NEXT_PUBLIC_API_URL is correct'
      });
    }
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/api/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token, refresh_token } = response.data.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;

// Auth API
export const authAPI = {
  signup: async (email: string, password: string, fullName?: string, username?: string) => {
    const payload: any = { email, password };
    if (fullName) payload.full_name = fullName;
    if (username) payload.username = username;
    
    const response = await apiClient.post('/api/auth/signup', payload);
    return response.data;
  },
  
  login: async (email: string, password: string) => {
    const response = await apiClient.post('/api/auth/login', { email, password });
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await apiClient.get('/api/auth/me');
    return response.data;
  },
  
  refreshToken: async (refreshToken: string) => {
    const response = await apiClient.post('/api/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },
};

// Document processing API
export const documentAPI = {
  uploadFiles: async (files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    
    const response = await apiClient.post('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  processURLs: async (urls: string[]) => {
    const urlList = Array.isArray(urls) ? urls : [urls];
    const response = await apiClient.post('/api/documents/urls', { urls: urlList });
    return response.data;
  },
  
  processYouTube: async (url: string) => {
    const response = await apiClient.post('/api/documents/youtube', { url });
    return response.data;
  },
  
  processText: async (text: string, title?: string) => {
    const response = await apiClient.post('/api/documents/text', { text, title });
    return response.data;
  },
  
  getSources: async () => {
    const response = await apiClient.get('/api/documents/sources');
    return response.data;
  },
  
  deleteSource: async (sourceName: string) => {
    // URL encode the source name to handle special characters
    const encodedName = encodeURIComponent(sourceName);
    const response = await apiClient.delete(`/api/documents/sources/${encodedName}`);
    return response.data;
  },
};

// Chat API
export const chatAPI = {
  sendMessage: async (query: string, sessionId?: string) => {
    const response = await apiClient.post('/api/chat/message', { query, session_id: sessionId });
    return response.data;
  },
  
  getHistory: async (sessionId: string) => {
    const response = await apiClient.get(`/api/chat/history/${sessionId}`);
    return response.data;
  },
};

// Podcast API
export const podcastAPI = {
  generatePodcast: async (sourceName: string, style: string, length: string) => {
    const response = await apiClient.post('/api/podcast/generate', {
      source_name: sourceName,
      style,
      length,
    });
    return response.data;
  },
  
  getPodcastStatus: async (jobId: string) => {
    const response = await apiClient.get(`/api/podcast/status/${jobId}`);
    return response.data;
  },
};

