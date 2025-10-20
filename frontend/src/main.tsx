import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './services/auth'
import { queryClient } from '@/lib/queryClient'
import AppRouter from '@/routes/AppRouter'
import './index.css'

// Query client configured in lib/queryClient

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
