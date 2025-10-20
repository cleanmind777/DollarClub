export type ScriptStatus = 'uploaded' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface Script {
  id: number
  filename: string
  original_filename: string
  file_size: number
  status: ScriptStatus
  execution_logs?: string
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
}

export interface ScriptListResponse {
  scripts: Script[]
  total: number
}

export interface ScriptStats {
  total: number
  running: number
  completed: number
  failed: number
}

