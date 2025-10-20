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
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
