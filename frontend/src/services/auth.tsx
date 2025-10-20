import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from './api'

interface User {
  id: number
  email: string
  username: string
  auth_provider: 'email' | 'google'
  google_id?: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  ibkr_connected: boolean
  ibkr_connected_at?: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  googleLogin: () => void
  logout: () => void
  handleAuthCallback: (token: string) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user

  useEffect(() => {
    // Cookie-based auth: just try to fetch user
    // If cookie exists, backend will authenticate automatically
    fetchUser()
  }, [])

  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
    } catch (error) {
      // Cookie is invalid or doesn't exist
      console.error('Failed to fetch user:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const response = await api.post('/auth/login', { email, password })
      const { user: userData } = response.data
      // Cookie is set automatically by the backend
      setUser(userData)
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const register = async (email: string, username: string, password: string) => {
    try {
      const response = await api.post('/auth/register', { 
        email, 
        username, 
        password, 
        confirm_password: password 
      })
      const { user: userData } = response.data
      // Cookie is set automatically by the backend
      setUser(userData)
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    }
  }

  const googleLogin = async () => {
    try {
      const response = await api.get('/auth/google/login')
      window.location.href = response.data.authorization_url
    } catch (error) {
      console.error('Google login failed:', error)
    }
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
      // Cookie is cleared by the backend
      setUser(null)
    } catch (error) {
      console.error('Logout failed:', error)
      // Clear user anyway
      setUser(null)
    }
  }

  const handleAuthCallback = async (token: string) => {
    // For OAuth flows, we might still receive a token
    // Just fetch the user (cookie should be set by backend)
    await fetchUser()
    window.location.href = '/dashboard'
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        register,
        googleLogin,
        logout,
        handleAuthCallback,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
