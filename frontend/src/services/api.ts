import axios from 'axios'

// Use environment variable for API URL
// In development: uses /api (proxied by Vite to remove /api prefix)
// In production: uses full backend URL directly (backend has no /api prefix)
const baseURL = import.meta.env.VITE_API_URL 
  ? import.meta.env.VITE_API_URL
  : '/api'

export const api = axios.create({
  baseURL,
  timeout: 10000,
  withCredentials: true,  // Important: Send cookies with requests
})

// Response interceptor for handling 401 errors and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // If 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Try to refresh the access token
        await api.post('/auth/refresh')
        
        // Retry the original request
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, redirect to login
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)
