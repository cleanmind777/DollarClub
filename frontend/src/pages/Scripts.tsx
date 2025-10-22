import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { api } from '@/lib/axios'
import type { Script } from '@/types'
import { 
  Upload, 
  Play, 
  Square, 
  Trash2, 
  FileText, 
  Clock,
  CheckCircle,
  XCircle,
  Download,
  X,
  RefreshCw,
  Eye
} from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { LoadingModal } from '@/components/LoadingModal'
import { ScriptViewModal } from '@/components/ScriptViewModal'

export function Scripts() {
  const [selectedScript, setSelectedScript] = useState<Script | null>(null)
  const [showLogs, setShowLogs] = useState(false)
  const [isRefreshingLogs, setIsRefreshingLogs] = useState(false)
  const [showScriptView, setShowScriptView] = useState(false)
  const [scriptContent, setScriptContent] = useState('')
  const [viewedScriptName, setViewedScriptName] = useState('')
  const [viewedScriptId, setViewedScriptId] = useState<number>(0)
  const [isActionLoading, setIsActionLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('')
  const queryClient = useQueryClient()

  // Auto-refresh logs for running scripts
  useEffect(() => {
    if (!showLogs || !selectedScript || selectedScript.status !== 'running') {
      return
    }

    const refreshLogs = async () => {
      try {
        setIsRefreshingLogs(true)
        const response = await api.get(`/scripts/${selectedScript.id}/status`)
        setSelectedScript(prev => prev ? {
          ...prev,
          execution_logs: response.data.logs,
          error_message: response.data.error_message,
          status: response.data.status
        } : null)
        
        // Auto-scroll to bottom of logs
        setTimeout(() => {
          const logsContainer = document.getElementById('logs-container')
          if (logsContainer) {
            logsContainer.scrollTop = logsContainer.scrollHeight
          }
        }, 50)
      } catch (error) {
        console.error('Failed to refresh logs:', error)
      } finally {
        setIsRefreshingLogs(false)
      }
    }

    // Refresh logs every 1 second for real-time trading algorithm monitoring
    const interval = setInterval(refreshLogs, 1000)
    
    return () => clearInterval(interval)
  }, [showLogs, selectedScript?.id, selectedScript?.status])

  const { data: scriptsData, isLoading } = useQuery(
    'scripts',
    async () => {
      const response = await api.get('/scripts/list')
      return response.data
    },
    {
      refetchInterval: 30000, // Refetch every 30 seconds (less frequent)
      refetchOnWindowFocus: false, // Don't refetch on window focus
      staleTime: 10000, // Consider data fresh for 10 seconds
    }
  )

  const uploadMutation = useMutation(
    async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await api.post('/scripts/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('scripts')
      }
    }
  )

  const executeMutation = useMutation(
    async (scriptId: number) => {
      console.log('Executing script:', scriptId)
      const response = await api.post(`/scripts/${scriptId}/execute`)
      console.log('Execute response:', response.data)
      return response.data
    },
    {
      onSuccess: (data) => {
        console.log('Execute success:', data)
        queryClient.invalidateQueries('scripts')
        // Reload page to show updated status
        window.location.reload()
      },
      onError: (error: any) => {
        console.error('Execute failed:', error)
        alert(`Failed to execute script: ${error.response?.data?.detail || error.message}`)
      }
    }
  )

  const cancelMutation = useMutation(
    async (scriptId: number) => {
      const response = await api.post(`/scripts/${scriptId}/cancel`)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('scripts')
        // Reload page to show updated status
        setTimeout(() => window.location.reload(), 500)
      }
    }
  )

  const deleteMutation = useMutation(
    async (scriptId: number) => {
      await api.delete(`/scripts/${scriptId}`)
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('scripts')
        setSelectedScript(null)
      }
    }
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'text/x-python': ['.py'],
      'application/javascript': ['.js'],
      'text/x-typescript': ['.ts']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        uploadMutation.mutate(acceptedFiles[0])
      }
    }
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <FileText className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'cancelled':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-yellow-100 text-yellow-800'
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const handleExecute = (script: Script) => {
    if (script.status === 'running') return
    executeMutation.mutate(script.id)
  }

  const handleCancel = (script: Script) => {
    if (script.status !== 'running') return
    cancelMutation.mutate(script.id)
  }

  const handleDelete = (script: Script) => {
    if (script.status === 'running') return
    if (window.confirm('Are you sure you want to delete this script?')) {
      deleteMutation.mutate(script.id)
    }
  }

  const handleViewLogs = async (script: Script) => {
    // Fetch latest logs (especially important for running scripts)
    try {
      const response = await api.get(`/scripts/${script.id}/status`)
      setSelectedScript({
        ...script,
        execution_logs: response.data.logs,
        error_message: response.data.error_message
      })
    } catch (error) {
      setSelectedScript(script)
    }
    setShowLogs(true)
  }

  const handleViewScript = async (script: Script) => {
    try {
      setIsActionLoading(true)
      setLoadingMessage('Loading script content...')
      const response = await api.get(`/scripts/${script.id}/content`)
      setScriptContent(response.data.content)
      setViewedScriptName(response.data.filename)
      setViewedScriptId(script.id)
      setShowScriptView(true)
    } catch (error: any) {
      alert(`Failed to load script: ${error.response?.data?.detail || error.message}`)
    } finally {
      setIsActionLoading(false)
    }
  }

  const handleDownloadScript = async (scriptId: number) => {
    try {
      setIsActionLoading(true)
      setLoadingMessage('Preparing download...')
      
      // Find the script to get its name
      const script = scripts.find((s: Script) => s.id === scriptId)
      if (!script) return
      
      const response = await api.get(`/scripts/${scriptId}/download`, {
        responseType: 'blob'
      })
      
      // Create a blob URL and trigger download
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = script.original_filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error: any) {
      alert(`Failed to download script: ${error.response?.data?.detail || error.message}`)
    } finally {
      setIsActionLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const scripts = scriptsData?.scripts || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scripts</h1>
          <p className="text-gray-600">Manage and execute your trading strategies</p>
        </div>
      </div>

      {/* Upload Area */}
      <div className="card">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive 
              ? 'border-primary-500 bg-primary-50' 
              : 'border-gray-300 hover:border-primary-400'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">
            {isDragActive
              ? 'Drop your script file here'
              : 'Drag & drop your script file here, or click to select'
            }
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Supports Python (.py), JavaScript (.js), and TypeScript (.ts) files up to 10MB
          </p>
        </div>
        
        {/* Package Information */}
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="text-sm font-medium text-blue-900 mb-2">📦 Package Requirements</h4>
          <p className="text-xs text-blue-800 mb-2">
            Scripts are automatically validated for package dependencies before execution.
          </p>
          <div className="text-xs text-blue-700 space-y-1">
            <div>✓ <strong>Pre-installed:</strong> pandas, numpy, requests, and more</div>
            <div>✓ <strong>Auto-detected:</strong> Missing packages are identified automatically</div>
            <div>✓ <strong>Clear errors:</strong> See exact installation commands if packages are missing</div>
          </div>
        </div>
      </div>

      {/* Scripts List */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Your Scripts</h3>
        
        {scripts.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No scripts uploaded</h3>
            <p className="mt-1 text-sm text-gray-500">
              Upload your first trading script to get started.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Script
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Size
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {scripts.map((script: Script) => (
                  <tr key={script.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <FileText className="h-5 w-5 text-gray-400 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {script.original_filename}
                          </div>
                          <div className="text-sm text-gray-500">
                            {script.filename}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(script.status)}
                        <span className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(script.status)}`}>
                          {script.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatFileSize(script.file_size)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(script.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center gap-2">
                        {script.status === 'running' ? (
                          <button
                            onClick={() => handleCancel(script)}
                            className="inline-flex items-center px-3 py-1.5 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500"
                            disabled={cancelMutation.isLoading}
                            title="Stop script execution"
                          >
                            <Square className="h-4 w-4 mr-1" />
                            Stop
                          </button>
                        ) : (
                          <button
                            onClick={() => handleExecute(script)}
                            className="inline-flex items-center px-3 py-1.5 border border-green-300 text-sm font-medium rounded-md text-green-700 bg-green-50 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-green-500"
                            disabled={executeMutation.isLoading}
                            title="Execute script"
                          >
                            <Play className="h-4 w-4 mr-1" />
                            Run
                          </button>
                        )}
                        
                        <button
                          onClick={() => handleViewScript(script)}
                          className="inline-flex items-center px-2 py-1.5 text-blue-600 hover:text-blue-900"
                          title="View script code"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        
                        <button
                          onClick={() => handleDownloadScript(script.id)}
                          className="inline-flex items-center px-2 py-1.5 text-purple-600 hover:text-purple-900"
                          title="Download script"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        
                        <button
                          onClick={() => handleViewLogs(script)}
                          className="inline-flex items-center px-2 py-1.5 text-gray-600 hover:text-gray-900"
                          title="View execution logs"
                        >
                          <FileText className="h-4 w-4" />
                        </button>
                        
                        <button
                          onClick={() => handleDelete(script)}
                          className="inline-flex items-center px-2 py-1.5 text-red-600 hover:text-red-900 disabled:opacity-50 disabled:cursor-not-allowed"
                          disabled={script.status === 'running'}
                          title={script.status === 'running' ? 'Cannot delete running script' : 'Delete script'}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Logs Modal */}
      {showLogs && selectedScript && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowLogs(false)} />
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <h3 className="text-lg font-medium text-gray-900">
                      Execution Logs - {selectedScript.original_filename}
                    </h3>
                    {selectedScript.status === 'running' && (
                      <span className="ml-3 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        <RefreshCw className={`h-3 w-3 mr-1 ${isRefreshingLogs ? 'animate-spin' : ''}`} />
                        Live
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    {selectedScript.status === 'running' && (
                      <button
                        onClick={() => {
                          handleCancel(selectedScript)
                          setShowLogs(false)
                        }}
                        className="btn btn-danger text-sm flex items-center"
                        disabled={cancelMutation.isLoading}
                      >
                        <Square className="h-4 w-4 mr-1" />
                        Stop Script
                      </button>
                    )}
                    <button
                      onClick={() => setShowLogs(false)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="h-6 w-6" />
                    </button>
                  </div>
                </div>
                
                <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto" id="logs-container">
                  {selectedScript.status === 'running' && (
                    <div className="flex items-center mb-3 text-yellow-400 bg-yellow-900/20 border border-yellow-700/30 rounded px-3 py-2">
                      <Clock className="h-4 w-4 mr-2 animate-pulse" />
                      <span className="text-xs font-semibold">RUNNING - Logs auto-refresh every 1 second</span>
                      {isRefreshingLogs && (
                        <RefreshCw className="h-3 w-3 ml-2 animate-spin" />
                      )}
                    </div>
                  )}
                  <pre className="whitespace-pre-wrap">
                    {selectedScript.execution_logs || (selectedScript.status === 'running' ? 'Script started, waiting for output...' : 'No logs available')}
                  </pre>
                </div>
                
                {selectedScript.error_message && (
                  <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-red-800 flex items-center">
                      <XCircle className="h-4 w-4 mr-2" />
                      Error Message:
                    </h4>
                    <pre className="text-sm text-red-700 mt-2 whitespace-pre-wrap font-mono bg-red-100 p-3 rounded">
                      {selectedScript.error_message}
                    </pre>
                    {selectedScript.error_message.includes('pip install') && (
                      <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded">
                        <p className="text-xs text-blue-800">
                          💡 <strong>Tip:</strong> Copy the installation command above and share it with your administrator.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading Modal */}
      <LoadingModal isOpen={isActionLoading} message={loadingMessage} />

      {/* Script View Modal */}
      <ScriptViewModal
        isOpen={showScriptView}
        onClose={() => setShowScriptView(false)}
        filename={viewedScriptName}
        content={scriptContent}
        scriptId={viewedScriptId}
        onDownload={handleDownloadScript}
      />
    </div>
  )
}

export default Scripts

