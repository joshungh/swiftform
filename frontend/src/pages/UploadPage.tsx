import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import {
  CloudUpload,
  InsertDriveFile,
  CheckCircle,
  Info,
  AutoAwesome
} from '@mui/icons-material'
import { toast } from 'react-toastify'
import { uploadDocument, processDocument } from '../services/api'

const UploadPage: React.FC = () => {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [fileId, setFileId] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [aiModel, setAiModel] = useState('ft:gpt-3.5-turbo-0125:swiftcomply:swiftform-20250929-092341:CLA6X3za')
  const [customInstructions, setCustomInstructions] = useState('')

  const availableModels = [
    {
      value: 'ft:gpt-3.5-turbo-0125:swiftcomply:swiftform-20250929-092341:CLA6X3za',
      label: '🎯 Custom Trained Model (Recommended)',
      description: 'Fine-tuned on your forms for best accuracy'
    },
    {
      value: 'gpt-4-turbo-preview',
      label: 'GPT-4 Turbo',
      description: 'Most capable, slower processing'
    },
    {
      value: 'gpt-4',
      label: 'GPT-4',
      description: 'High accuracy, slower processing'
    },
    {
      value: 'gpt-3.5-turbo',
      label: 'GPT-3.5 Turbo',
      description: 'Fast and cost-effective'
    },
    {
      value: 'basic',
      label: 'Basic Parser',
      description: 'Rule-based, no AI'
    }
  ]

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
      setFileId(null)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    maxFiles: 1
  })

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    try {
      const response = await uploadDocument(file)
      setFileId(response.file_id)
      toast.success('File uploaded successfully!')
    } catch (error) {
      toast.error('Upload failed. Please try again.')
      console.error(error)
    } finally {
      setUploading(false)
    }
  }

  const handleProcess = async () => {
    if (!fileId) return

    setProcessing(true)
    try {
      const response = await processDocument({
        file_id: fileId,
        ai_model: aiModel,
        custom_instructions: customInstructions || undefined
      })

      toast.success('Processing started! Redirecting...')
      setTimeout(() => {
        navigate(`/result/${response.job_id}`)
      }, 1500)
    } catch (error) {
      toast.error('Processing failed. Please try again.')
      console.error(error)
    } finally {
      setProcessing(false)
    }
  }

  const getFileIcon = () => {
    if (!file) return <CloudUpload className="h-12 w-12 text-gray-400" />

    const ext = file.name.split('.').pop()?.toLowerCase()
    const colorClass = {
      pdf: 'text-red-600',
      doc: 'text-blue-600',
      docx: 'text-blue-600',
      xls: 'text-green-600',
      xlsx: 'text-green-600'
    }[ext || ''] || 'text-gray-600'

    return <InsertDriveFile className={`h-12 w-12 ${colorClass}`} />
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Upload Document</h1>

      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 mb-6 cursor-pointer
          transition-all duration-200 text-center
          ${isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center">
          {getFileIcon()}
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            {isDragActive
              ? 'Drop the file here'
              : 'Drag & drop a document here, or click to select'}
          </h3>
          <p className="mt-2 text-sm text-gray-500">
            Supported: PDF, DOC, DOCX, XLS, XLSX (Max 10MB)
          </p>
        </div>
      </div>

      {/* Selected File */}
      {file && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Selected File</h2>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <InsertDriveFile className="h-10 w-10 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            {fileId ? (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                <CheckCircle className="mr-1.5 h-4 w-4" />
                Uploaded
              </span>
            ) : (
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700
                  disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors
                  inline-flex items-center"
              >
                <CloudUpload className="mr-2 h-5 w-5" />
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            )}
          </div>
          {uploading && (
            <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
              <div className="bg-primary-600 h-2 rounded-full animate-pulse" style={{ width: '50%' }}></div>
            </div>
          )}
        </div>
      )}

      {/* Processing Options */}
      {fileId && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Processing Options</h2>

          {/* Model Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AI Model
            </label>
            <div className="space-y-2">
              {availableModels.map((model) => (
                <label
                  key={model.value}
                  className={`
                    relative flex items-start p-4 border rounded-lg cursor-pointer
                    transition-all duration-200
                    ${aiModel === model.value
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-primary-300'
                    }
                  `}
                >
                  <input
                    type="radio"
                    className="sr-only"
                    value={model.value}
                    checked={aiModel === model.value}
                    onChange={(e) => setAiModel(e.target.value)}
                  />
                  <div className="flex-1">
                    <div className="flex items-center">
                      {model.label.includes('Custom') && (
                        <AutoAwesome className="mr-2 h-5 w-5 text-yellow-500" />
                      )}
                      <span className="font-medium text-gray-900">{model.label}</span>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">{model.description}</p>
                  </div>
                  {aiModel === model.value && (
                    <CheckCircle className="h-5 w-5 text-primary-600 flex-shrink-0 ml-3" />
                  )}
                </label>
              ))}
            </div>
          </div>

          {/* Custom Instructions */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Custom Instructions (Optional)
            </label>
            <textarea
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500
                focus:border-primary-500 resize-none"
              placeholder="E.g., 'Focus on inspection fields', 'Group by sections', 'Include validation rules'"
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
            />
          </div>

          {/* Process Button */}
          <button
            onClick={handleProcess}
            disabled={processing}
            className="w-full py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700
              disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors
              font-medium text-lg"
          >
            {processing ? 'Processing...' : 'Generate Form Schema'}
          </button>
          {processing && (
            <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
              <div className="bg-primary-600 h-2 rounded-full animate-pulse" style={{ width: '75%' }}></div>
            </div>
          )}
        </div>
      )}

      {/* Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex">
          <Info className="h-5 w-5 text-blue-400 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Tips for Best Results</h3>
            <ul className="mt-2 text-sm text-blue-700 space-y-1 list-disc list-inside">
              <li>Use the Custom Trained Model for forms similar to your training data</li>
              <li>GPT-4 provides the best accuracy for complex forms</li>
              <li>Ensure your document has clear field labels and structure</li>
              <li>Tables in documents are automatically converted to form groups</li>
              <li>Processing typically takes 10-30 seconds depending on document size</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UploadPage