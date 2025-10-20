import { useState } from 'react'
import { useAuth } from '../services/auth'
import { api } from '../services/api'
import { 
  TrendingUp, 
  CheckCircle, 
  XCircle, 
  Link, 
  Unlink,
  AlertCircle,
  ExternalLink
} from 'lucide-react'

export function IBKRIntegration() {
  const { user } = useAuth()
  const [isConnecting, setIsConnecting] = useState(false)
  const [isDisconnecting, setIsDisconnecting] = useState(false)
  const [error, setError] = useState('')

  const handleConnect = async () => {
    setIsConnecting(true)
    setError('')
    
    try {
      const response = await api.get('/auth/ibkr/connect')
      window.location.href = response.data.authorization_url
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initiate IBKR connection')
    } finally {
      setIsConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    if (!window.confirm('Are you sure you want to disconnect your IBKR account? This will prevent you from executing trading scripts.')) {
      return
    }

    setIsDisconnecting(true)
    setError('')
    
    try {
      await api.delete('/auth/ibkr/disconnect')
      // Refresh user data
      window.location.reload()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to disconnect IBKR account')
    } finally {
      setIsDisconnecting(false)
    }
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <TrendingUp className="h-6 w-6 text-primary-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">IBKR Integration</h3>
        </div>
        {user?.ibkr_connected ? (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle className="w-3 h-3 mr-1" />
            Connected
          </span>
        ) : (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            <XCircle className="w-3 h-3 mr-1" />
            Not Connected
          </span>
        )}
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      )}

      {user?.ibkr_connected ? (
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex">
              <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
              <div>
                <h4 className="text-sm font-medium text-green-800">IBKR Account Connected</h4>
                <p className="text-sm text-green-700 mt-1">
                  Your Interactive Brokers account is successfully connected and ready for trading script execution.
                </p>
              </div>
            </div>
          </div>

          {user.ibkr_connected_at && (
            <div className="text-sm text-gray-600">
              <p><strong>Connected on:</strong> {new Date(user.ibkr_connected_at).toLocaleDateString()}</p>
            </div>
          )}

          <div className="flex space-x-3">
            <button
              onClick={handleDisconnect}
              disabled={isDisconnecting}
              className="btn btn-secondary flex items-center"
            >
              <Unlink className="h-4 w-4 mr-2" />
              {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
            </button>
            
            <a
              href="https://www.interactivebrokers.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary flex items-center"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Visit IBKR
            </a>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-yellow-400 mr-2" />
              <div>
                <h4 className="text-sm font-medium text-yellow-800">IBKR Account Required</h4>
                <p className="text-sm text-yellow-700 mt-1">
                  Connect your Interactive Brokers account to execute trading scripts and access market data.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-900">Benefits of connecting:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Execute trading strategies automatically</li>
              <li>• Access real-time market data</li>
              <li>• Manage positions and orders</li>
              <li>• Portfolio analysis and reporting</li>
            </ul>
          </div>

          <button
            onClick={handleConnect}
            disabled={isConnecting}
            className="btn btn-primary flex items-center w-full justify-center"
          >
            <Link className="h-4 w-4 mr-2" />
            {isConnecting ? 'Connecting...' : 'Connect IBKR Account'}
          </button>

          <div className="text-xs text-gray-500 text-center">
            <p>
              You'll be redirected to Interactive Brokers to authorize the connection.
              We only request the necessary permissions for trading script execution.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
