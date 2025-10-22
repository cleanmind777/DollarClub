import { Loader2 } from 'lucide-react'

interface LoadingModalProps {
  isOpen: boolean
  message?: string
}

export function LoadingModal({ isOpen, message = 'Loading...' }: LoadingModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        
        <div className="inline-block align-middle bg-white rounded-lg px-8 py-6 text-center overflow-hidden shadow-xl transform transition-all sm:my-8">
          <div className="flex flex-col items-center">
            <Loader2 className="h-12 w-12 text-primary-600 animate-spin" />
            <p className="mt-4 text-sm font-medium text-gray-900">{message}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoadingModal

