import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from '@/lib/axios'
import type { User } from '@/types'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  googleLogin: () => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user

  useEffect(() => {
    // Only try to fetch user if not on login page
    // This prevents unnecessary API calls on the login page
    const currentPath = window.location.pathname
    if (currentPath === '/login') {
      setIsLoading(false)
      return
    }
    
    // Cookie-based auth: just try to fetch user
    // If cookie exists, backend will authenticate automatically
    fetchUser()
  }, [])

  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
    } catch (error) {
      // Cookie is invalid or doesn't exist - this is expected
      // Silently fail and let the user login (no console error)
      setUser(null)
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
