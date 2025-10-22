import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/services/auth'

type Props = { children: React.ReactElement }

export function ProtectedRoute({ children }: Props) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) return null
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

export default ProtectedRoute


