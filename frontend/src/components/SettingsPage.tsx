import { useState } from 'react'
import { useAuth } from '../services/auth'
import { IBKRIntegration } from './IBKRIntegration'
import { 
  User, 
  Mail, 
  Calendar, 
  Shield, 
  CheckCircle,
  XCircle
} from 'lucide-react'

export function SettingsPage() {
  const { user } = useAuth()

  const getAuthProviderIcon = (provider: string) => {
    switch (provider) {
      case 'google':
        return (
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
        )
      default:
        return <Mail className="w-5 h-5" />
    }
  }

  const getAuthProviderName = (provider: string) => {
    switch (provider) {
      case 'google':
        return 'Google'
      default:
        return 'Email'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Manage your account and integrations</p>
      </div>

      {/* Account Information */}
      <div className="card">
        <div className="flex items-center mb-4">
          <User className="h-6 w-6 text-primary-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Account Information</h3>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <div className="flex items-center p-3 bg-gray-50 rounded-lg">
              <User className="h-4 w-4 text-gray-400 mr-2" />
              <span className="text-sm text-gray-900">{user?.username}</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <div className="flex items-center p-3 bg-gray-50 rounded-lg">
              <Mail className="h-4 w-4 text-gray-400 mr-2" />
              <span className="text-sm text-gray-900">{user?.email}</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Account Type
            </label>
            <div className="flex items-center p-3 bg-gray-50 rounded-lg">
              {getAuthProviderIcon(user?.auth_provider || 'email')}
              <span className="text-sm text-gray-900 ml-2">
                {getAuthProviderName(user?.auth_provider || 'email')}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Member Since
            </label>
            <div className="flex items-center p-3 bg-gray-50 rounded-lg">
              <Calendar className="h-4 w-4 text-gray-400 mr-2" />
              <span className="text-sm text-gray-900">
                {new Date(user?.created_at || '').toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Shield className="h-5 w-5 text-gray-400 mr-2" />
              <span className="text-sm font-medium text-gray-700">Account Status</span>
            </div>
            <div className="flex items-center">
              {user?.is_verified ? (
                <>
                  <CheckCircle className="h-4 w-4 text-green-500 mr-1" />
                  <span className="text-sm text-green-600">Verified</span>
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 text-yellow-500 mr-1" />
                  <span className="text-sm text-yellow-600">Unverified</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* IBKR Integration */}
      <IBKRIntegration />

      {/* Security Settings */}
      <div className="card">
        <div className="flex items-center mb-4">
          <Shield className="h-6 w-6 text-primary-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Security</h3>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Two-Factor Authentication</h4>
              <p className="text-sm text-gray-600">Add an extra layer of security to your account</p>
            </div>
            <button className="btn btn-secondary text-sm">
              Enable 2FA
            </button>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Password</h4>
              <p className="text-sm text-gray-600">Update your account password</p>
            </div>
            <button className="btn btn-secondary text-sm">
              Change Password
            </button>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Login Sessions</h4>
              <p className="text-sm text-gray-600">Manage your active login sessions</p>
            </div>
            <button className="btn btn-secondary text-sm">
              View Sessions
            </button>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="card border-red-200">
        <div className="flex items-center mb-4">
          <XCircle className="h-6 w-6 text-red-600 mr-3" />
          <h3 className="text-lg font-medium text-red-900">Danger Zone</h3>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-red-900">Delete Account</h4>
              <p className="text-sm text-red-600">
                Permanently delete your account and all associated data. This action cannot be undone.
              </p>
            </div>
            <button className="btn btn-danger text-sm">
              Delete Account
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
