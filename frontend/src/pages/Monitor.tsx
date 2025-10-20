import { useQuery } from 'react-query'
import { api } from '@/lib/axios'
import type { Script, ScriptStats } from '@/types'
import {
  Activity,
  Clock,
  TrendingUp,
  TrendingDown,
  Zap,
  CheckCircle,
  XCircle,
  AlertCircle,
  BarChart3,
  PieChart,
  Timer
} from 'lucide-react'

interface PerformanceMetrics {
  totalExecutions: number
  successRate: number
  averageExecutionTime: number
  totalExecutionTime: number
  activeScripts: number
}

export function Monitor() {
  const { data: scriptsData, isLoading } = useQuery(
    'scripts-monitor',
    async () => {
      const response = await api.get('/scripts/list')
      return response.data
    },
    {
      refetchInterval: 5000, // Refresh every 5 seconds for real-time monitoring
      refetchOnWindowFocus: true,
    }
  )

  // Calculate performance metrics
  const scripts: Script[] = scriptsData?.scripts || []
  
  const metrics: PerformanceMetrics = {
    totalExecutions: scripts.filter(s => 
      s.status === 'completed' || s.status === 'failed' || s.status === 'running'
    ).length,
    successRate: scripts.length > 0
      ? (scripts.filter(s => s.status === 'completed').length / scripts.length) * 100
      : 0,
    averageExecutionTime: calculateAverageExecutionTime(scripts),
    totalExecutionTime: calculateTotalExecutionTime(scripts),
    activeScripts: scripts.filter(s => s.status === 'running').length,
  }

  const stats: ScriptStats = {
    total: scripts.length,
    running: scripts.filter((s: Script) => s.status === 'running').length,
    completed: scripts.filter((s: Script) => s.status === 'completed').length,
    failed: scripts.filter((s: Script) => s.status === 'failed').length,
  }

  const recentExecutions = scripts
    .filter(s => s.started_at)
    .sort((a, b) => new Date(b.started_at!).getTime() - new Date(a.started_at!).getTime())
    .slice(0, 10)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Performance Monitor</h1>
        <p className="text-gray-600">Real-time script execution metrics and analytics</p>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Executions */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Executions</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.totalExecutions}</p>
              <p className="text-xs text-gray-500 mt-1">All time</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Activity className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        {/* Success Rate */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Success Rate</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.successRate.toFixed(1)}%</p>
              <p className="text-xs text-gray-500 mt-1">
                {stats.completed} / {scripts.length} scripts
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              {metrics.successRate >= 80 ? (
                <TrendingUp className="h-6 w-6 text-green-600" />
              ) : (
                <TrendingDown className="h-6 w-6 text-red-600" />
              )}
            </div>
          </div>
        </div>

        {/* Average Execution Time */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Execution</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatDuration(metrics.averageExecutionTime)}
              </p>
              <p className="text-xs text-gray-500 mt-1">Per script</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <Timer className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>

        {/* Active Scripts */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Now</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.activeScripts}</p>
              <p className="text-xs text-gray-500 mt-1">Running scripts</p>
            </div>
            <div className={`p-3 rounded-lg ${
              metrics.activeScripts > 0 ? 'bg-orange-100' : 'bg-gray-100'
            }`}>
              <Zap className={`h-6 w-6 ${
                metrics.activeScripts > 0 ? 'text-orange-600 animate-pulse' : 'text-gray-400'
              }`} />
            </div>
          </div>
        </div>
      </div>

      {/* Status Distribution */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Status Breakdown */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Status Distribution</h3>
            <PieChart className="h-5 w-5 text-gray-400" />
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                <span className="text-sm text-gray-700">Completed</span>
              </div>
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-900 mr-2">{stats.completed}</span>
                <span className="text-xs text-gray-500">
                  ({scripts.length > 0 ? ((stats.completed / scripts.length) * 100).toFixed(0) : 0}%)
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                <span className="text-sm text-gray-700">Running</span>
              </div>
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-900 mr-2">{stats.running}</span>
                <span className="text-xs text-gray-500">
                  ({scripts.length > 0 ? ((stats.running / scripts.length) * 100).toFixed(0) : 0}%)
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-500 rounded-full mr-3"></div>
                <span className="text-sm text-gray-700">Failed</span>
              </div>
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-900 mr-2">{stats.failed}</span>
                <span className="text-xs text-gray-500">
                  ({scripts.length > 0 ? ((stats.failed / scripts.length) * 100).toFixed(0) : 0}%)
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-yellow-500 rounded-full mr-3"></div>
                <span className="text-sm text-gray-700">Uploaded</span>
              </div>
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-900 mr-2">
                  {scripts.filter(s => s.status === 'uploaded').length}
                </span>
                <span className="text-xs text-gray-500">
                  ({scripts.length > 0 ? ((scripts.filter(s => s.status === 'uploaded').length / scripts.length) * 100).toFixed(0) : 0}%)
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* System Health */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">System Health</h3>
            <BarChart3 className="h-5 w-5 text-gray-400" />
          </div>

          <div className="space-y-4">
            <HealthIndicator
              label="Success Rate"
              value={metrics.successRate}
              threshold={80}
              format={(v) => `${v.toFixed(1)}%`}
            />

            <HealthIndicator
              label="Active Scripts"
              value={metrics.activeScripts}
              threshold={5}
              format={(v) => v.toString()}
              inverse
            />

            <HealthIndicator
              label="Failed Scripts"
              value={stats.failed}
              threshold={3}
              format={(v) => v.toString()}
              inverse
            />

            <div className="pt-3 border-t border-gray-200">
              <div className="flex items-center text-sm">
                {getSystemStatus(metrics, stats) === 'healthy' ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                    <span className="text-green-700 font-medium">System Healthy</span>
                  </>
                ) : getSystemStatus(metrics, stats) === 'warning' ? (
                  <>
                    <AlertCircle className="h-4 w-4 text-yellow-500 mr-2" />
                    <span className="text-yellow-700 font-medium">Attention Required</span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-4 w-4 text-red-500 mr-2" />
                    <span className="text-red-700 font-medium">Issues Detected</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Executions */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Recent Executions</h3>
          <Clock className="h-5 w-5 text-gray-400" />
        </div>

        {recentExecutions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Activity className="mx-auto h-12 w-12 text-gray-300 mb-2" />
            <p>No executions yet</p>
          </div>
        ) : (
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Script</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Started</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentExecutions.map((script) => (
                  <tr key={script.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">{script.original_filename}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={script.status} />
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {script.started_at ? formatTimeAgo(script.started_at) : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {getExecutionDuration(script)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

// Helper Components
function HealthIndicator({ 
  label, 
  value, 
  threshold, 
  format, 
  inverse = false 
}: { 
  label: string
  value: number
  threshold: number
  format: (v: number) => string
  inverse?: boolean
}) {
  const isHealthy = inverse ? value < threshold : value >= threshold
  
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-gray-600">{label}</span>
        <span className="text-sm font-medium text-gray-900">{format(value)}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${
            isHealthy ? 'bg-green-500' : 'bg-red-500'
          }`}
          style={{ width: `${Math.min(100, (value / threshold) * 100)}%` }}
        />
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const config = {
    running: { bg: 'bg-blue-100', text: 'text-blue-800', icon: Activity },
    completed: { bg: 'bg-green-100', text: 'text-green-800', icon: CheckCircle },
    failed: { bg: 'bg-red-100', text: 'text-red-800', icon: XCircle },
    cancelled: { bg: 'bg-gray-100', text: 'text-gray-800', icon: XCircle },
    uploaded: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: Clock },
  }[status] || { bg: 'bg-gray-100', text: 'text-gray-800', icon: Clock }

  const Icon = config.icon

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      <Icon className="h-3 w-3 mr-1" />
      {status}
    </span>
  )
}

// Helper Functions
function calculateAverageExecutionTime(scripts: Script[]): number {
  const completed = scripts.filter(s => s.completed_at && s.started_at)
  if (completed.length === 0) return 0

  const total = completed.reduce((acc, s) => {
    const duration = new Date(s.completed_at!).getTime() - new Date(s.started_at!).getTime()
    return acc + duration
  }, 0)

  return total / completed.length
}

function calculateTotalExecutionTime(scripts: Script[]): number {
  return scripts
    .filter(s => s.completed_at && s.started_at)
    .reduce((acc, s) => {
      const duration = new Date(s.completed_at!).getTime() - new Date(s.started_at!).getTime()
      return acc + duration
    }, 0)
}

function formatDuration(ms: number): string {
  if (ms === 0) return '0s'
  
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) return `${hours}h ${minutes % 60}m`
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`
  return `${seconds}s`
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

function getExecutionDuration(script: Script): string {
  if (!script.started_at) return '-'
  
  const end = script.completed_at ? new Date(script.completed_at) : new Date()
  const start = new Date(script.started_at)
  const duration = end.getTime() - start.getTime()
  
  return formatDuration(duration)
}

function getSystemStatus(metrics: PerformanceMetrics, stats: ScriptStats): 'healthy' | 'warning' | 'critical' {
  if (metrics.successRate < 50 || stats.failed > 5) return 'critical'
  if (metrics.successRate < 80 || stats.failed > 2) return 'warning'
  return 'healthy'
}

export default Monitor

