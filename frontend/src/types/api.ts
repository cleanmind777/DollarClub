export interface ApiError {
  detail: string
  status?: number
}

export interface ApiResponse<T = any> {
  data: T
  message?: string
}

export interface PaginationParams {
  skip?: number
  limit?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

