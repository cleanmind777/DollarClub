export interface User {
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

export interface UserResponse {
  user: User
  access_token?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
  confirm_password: string
}

