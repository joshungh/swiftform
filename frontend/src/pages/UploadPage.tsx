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
  const [aiModel, setAiModel] = useState('gpt-5')
  const [customInstructions, setCustomInstructions] = useState('')

  const availableModels = [
    {
      value: 'gpt-5',
      label: 'GPT-5 (Recommended)',
      description: 'Latest model with best accuracy and comprehensive extraction'
    },
    {
      value: 'gpt-4',
      label: 'GPT-4',
      description: 'Previous generation - highly accurate'
    },
    {
      value: 'gpt-3.5-turbo',
      label: 'GPT-3.5 Turbo',
      description: 'Faster and more cost-effective'
    },
    {
      value: 'ft:gpt-3.5-turbo-0125:swiftcomply:swiftform-20250929-092341:CLA6X3za',
      label: 'Custom Trained Model',
      description: 'Fine-tuned on your specific forms'
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

      // Log the full API response
      console.log('=== API Response ===')
      console.log(JSON.stringify(response, null, 2))
      console.log('===================')

      // If schema was generated, navigate directly to result page
      if (response.xf_schema) {
        toast.success('Schema generated successfully!')
        // Store the schema temporarily and navigate
        sessionStorage.setItem(`schema_${response.file_id}`, JSON.stringify(response.xf_schema))
        navigate(`/result/upload_${response.file_id}`)
      } else {
        toast.success('File uploaded successfully!')
      }
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
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700
                disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors
                inline-flex items-center"
            >
              <CloudUpload className="mr-2 h-5 w-5" />
              {uploading ? 'Processing with GPT-5...' : 'Upload & Generate'}
            </button>
          </div>
          {uploading && (
            <div className="mt-6 bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg p-6 border border-primary-200">
              <div className="flex items-center justify-center space-x-3 mb-4">
                <AutoAwesome className="h-6 w-6 text-primary-600 animate-pulse" />
                <h3 className="text-lg font-semibold text-gray-900">GPT-5 Processing</h3>
              </div>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    <div className="h-2 w-2 bg-primary-600 rounded-full animate-pulse"></div>
                  </div>
                  <p className="text-sm text-gray-700">Uploading document...</p>
                  <CheckCircle className="h-5 w-5 text-green-600 ml-auto" />
                </div>
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    <div className="h-2 w-2 bg-primary-600 rounded-full animate-pulse"></div>
                  </div>
                  <p className="text-sm text-gray-700">Extracting text from PDF...</p>
                  <div className="ml-auto">
                    <svg className="animate-spin h-5 w-5 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    <div className="h-2 w-2 bg-primary-600 rounded-full animate-pulse"></div>
                  </div>
                  <p className="text-sm text-gray-700">GPT-5 analyzing structure & fields...</p>
                  <div className="ml-auto">
                    <svg className="animate-spin h-5 w-5 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                </div>
                <div className="flex items-center space-x-3 opacity-60">
                  <div className="flex-shrink-0">
                    <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
                  </div>
                  <p className="text-sm text-gray-600">Generating xf:json schema...</p>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-primary-200">
                <div className="flex items-center justify-between text-xs text-gray-600">
                  <span className="flex items-center space-x-1">
                    <Info className="h-4 w-4" />
                    <span>This typically takes 20-30 seconds</span>
                  </span>
                  <span className="font-medium text-primary-700">Please wait...</span>
                </div>
              </div>
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
              <li>Upload your PDF and GPT-5 will automatically parse the entire document</li>
              <li>All fields, checkboxes, text areas, and form elements are extracted</li>
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