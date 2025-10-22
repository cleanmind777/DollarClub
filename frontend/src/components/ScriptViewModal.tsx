import { X, Copy, Check, Download } from 'lucide-react'
import { useState } from 'react'

interface ScriptViewModalProps {
  isOpen: boolean
  onClose: () => void
  filename: string
  content: string
  scriptId: number
  onDownload: (scriptId: number) => void
}

export function ScriptViewModal({ 
  isOpen, 
  onClose, 
  filename, 
  content, 
  scriptId,
  onDownload 
}: ScriptViewModalProps) {
  const [copied, setCopied] = useState(false)

  if (!isOpen) return null

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const getLanguage = (filename: string) => {
    if (filename.endsWith('.py')) return 'python'
    if (filename.endsWith('.js')) return 'javascript'
    if (filename.endsWith('.ts')) return 'typescript'
    return 'text'
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" 
          onClick={onClose}
        />
        
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-5xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <h3 className="text-lg font-medium text-gray-900">
                  {filename}
                </h3>
                <span className="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {getLanguage(filename)}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => onDownload(scriptId)}
                  className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  title="Download script"
                >
                  <Download className="h-4 w-4 mr-1" />
                  Download
                </button>
                <button
                  onClick={handleCopy}
                  className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  title="Copy to clipboard"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4 mr-1 text-green-600" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 mr-1" />
                      Copy
                    </>
                  )}
                </button>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
            </div>
            
            <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm max-h-[600px] overflow-y-auto">
              <pre className="whitespace-pre-wrap">
                <code>{content}</code>
              </pre>
            </div>
            
            <div className="mt-4 flex justify-end">
              <button
                onClick={onClose}
                className="btn btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ScriptViewModal

