import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { api } from '../services/api'
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
  X
} from 'lucide-react'
import { useDropzone } from 'react-dropzone'

interface Script {
  id: number
  filename: string
  original_filename: string
  file_size: number
  status: 'uploaded' | 'running' | 'completed' | 'failed' | 'cancelled'
  execution_logs?: string
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
}

export function ScriptsPage() {
  const [selectedScript, setSelectedScript] = useState<Script | null>(null)
  const [showLogs, setShowLogs] = useState(false)
  const queryClient = useQueryClient()

  const { data: scriptsData, isLoading } = useQuery(
    'scripts',
    async () => {
      const response = await api.get('/scripts/list')
      return response.data
    },
    {
      refetchInterval: 5000, // Refetch every 5 seconds
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
      const response = await api.post(`/scripts/${scriptId}/execute`)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('scripts')
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

  const handleViewLogs = (script: Script) => {
    setSelectedScript(script)
    setShowLogs(true)
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      {script.status === 'running' ? (
                        <button
                          onClick={() => handleCancel(script)}
                          className="text-red-600 hover:text-red-900"
                          disabled={cancelMutation.isLoading}
                        >
                          <Square className="h-4 w-4" />
                        </button>
                      ) : (
                        <button
                          onClick={() => handleExecute(script)}
                          className="text-green-600 hover:text-green-900"
                          disabled={executeMutation.isLoading || script.status === 'running'}
                        >
                          <Play className="h-4 w-4" />
                        </button>
                      )}
                      
                      <button
                        onClick={() => handleViewLogs(script)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => handleDelete(script)}
                        className="text-red-600 hover:text-red-900"
                        disabled={script.status === 'running'}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
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
                  <h3 className="text-lg font-medium text-gray-900">
                    Execution Logs - {selectedScript.original_filename}
                  </h3>
                  <button
                    onClick={() => setShowLogs(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>
                
                <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap">
                    {selectedScript.execution_logs || 'No logs available'}
                  </pre>
                </div>
                
                {selectedScript.error_message && (
                  <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-red-800">Error Message:</h4>
                    <p className="text-sm text-red-700 mt-1">{selectedScript.error_message}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
