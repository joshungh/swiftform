import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { CloudUpload, CheckCircle, Error as ErrorIcon, Info } from '@mui/icons-material'
import { toast } from 'react-toastify'
import { uploadDocument } from '../services/api'

interface ProgressEvent {
  timestamp: string
  event_type: string
  message: string
  data: Record<string, any>
}

export default function UploadWithAudit() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [events, setEvents] = useState<ProgressEvent[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const navigate = useNavigate()
  const eventSourceRef = useRef<EventSource | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setEvents([])
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setEvents([])

    // Generate a session ID upfront
    const fileId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    setSessionId(fileId)

    try {
      // Connect to SSE BEFORE uploading so we can track progress
      console.log(`Connecting to SSE: http://localhost:8000/api/progress/${fileId}`)
      const eventSource = new EventSource(`http://localhost:8000/api/progress/${fileId}`)
      eventSourceRef.current = eventSource

      eventSource.onopen = () => {
        console.log('SSE connection opened')
      }

      eventSource.onmessage = (event) => {
        console.log('SSE event received:', event.data)
        try {
          const progressEvent: ProgressEvent = JSON.parse(event.data)
          console.log('Parsed event:', progressEvent)

          // Update events state
          setEvents((prev) => {
            const newEvents = [...prev, progressEvent]
            console.log('Total events now:', newEvents.length)
            return newEvents
          })

          // If we receive success event with schema, save and show success
          if (progressEvent.event_type === 'success' && progressEvent.data?.schema) {
            sessionStorage.setItem(`schema_${fileId}`, JSON.stringify(progressEvent.data.schema))
            setUploading(false)
            eventSource.close()
            toast.success('🎉 Schema generated successfully! View the audit trail below.')
          }

          // If we receive error event, stop processing
          if (progressEvent.event_type === 'error') {
            setUploading(false)
            eventSource.close()
            toast.error('Processing failed. Check the audit trail for details.')
          }
        } catch (e) {
          console.error('Error parsing SSE event:', e)
        }
      }

      eventSource.onerror = (error) => {
        console.error('SSE error:', error)
        eventSource.close()
      }

      // Upload with session_id so backend can emit events to this session
      const formData = new FormData()
      formData.append('file', file)
      formData.append('session_id', fileId)

      console.log('Uploading file with session_id:', fileId)
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      console.log('Upload response:', result)

    } catch (error) {
      toast.error('Upload failed. Please try again.')
      console.error(error)
      setUploading(false)
      setEvents(prev => [...prev, {
        timestamp: new Date().toISOString(),
        event_type: 'error',
        message: 'Upload failed',
        data: {}
      }])
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'error':
        return <ErrorIcon className="h-5 w-5 text-red-600" />
      case 'upload':
        return <CloudUpload className="h-5 w-5 text-blue-600" />
      default:
        return <Info className="h-5 w-5 text-primary-600" />
    }
  }

  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case 'success':
        return 'bg-green-50 border-green-200'
      case 'error':
        return 'bg-red-50 border-red-200'
      case 'upload':
        return 'bg-blue-50 border-blue-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-blue-50 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Upload PDF Form</h1>
          <p className="text-gray-600">Upload a PDF and see real-time processing details from GPT-5</p>
        </div>

        {/* Upload Card */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-500 transition-colors">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
              disabled={uploading}
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <CloudUpload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              {file ? (
                <div>
                  <p className="text-lg font-semibold text-gray-900">{file.name}</p>
                  <p className="text-sm text-gray-500 mt-1">{(file.size / 1024).toFixed(2)} KB</p>
                </div>
              ) : (
                <div>
                  <p className="text-lg font-semibold text-gray-900">Drop your PDF here</p>
                  <p className="text-sm text-gray-500 mt-1">or click to browse</p>
                </div>
              )}
            </label>
          </div>

          {file && !uploading && (
            <button
              onClick={handleUpload}
              className="mt-6 w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-primary-700 transition-colors flex items-center justify-center"
            >
              <CloudUpload className="mr-2 h-5 w-5" />
              Upload & Process with GPT-5
            </button>
          )}
        </div>

        {/* Processing Indicator */}
        {uploading && events.length === 0 && (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="flex flex-col items-center space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              <p className="text-lg font-semibold text-gray-900">Connecting to GPT-5...</p>
              <p className="text-sm text-gray-600">Please wait while we establish the connection</p>
            </div>
          </div>
        )}

        {/* Audit Trail */}
        {events.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                Processing Audit Trail ({events.length} events)
                {uploading && (
                  <div className="ml-3 animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
                )}
              </h2>
              {!uploading && sessionId && sessionStorage.getItem(`schema_${sessionId}`) && (
                <button
                  onClick={() => navigate(`/result/${sessionId}`)}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-green-700 transition-colors flex items-center"
                >
                  <CheckCircle className="mr-2 h-5 w-5" />
                  View Generated Form
                </button>
              )}
            </div>
            <div className="space-y-4">
              {events.map((event, index) => (
                <div
                  key={index}
                  className={`border rounded-lg p-4 ${getEventColor(event.event_type)}`}
                >
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-0.5">
                      {getEventIcon(event.event_type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="font-semibold text-gray-900">{event.message}</p>
                        <span className="text-xs text-gray-500">
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      {Object.keys(event.data).length > 0 && (
                        <div className="mt-2 text-sm text-gray-700">
                          {/* Special handling for success event with schema */}
                          {event.event_type === 'success' && event.data.schema ? (
                            <div className="space-y-3">
                              {/* Token Usage Summary */}
                              {event.data.token_usage && (
                                <div className="flex flex-wrap gap-4 text-xs text-gray-600">
                                  <span>📊 Prompt: {event.data.token_usage.prompt_tokens?.toLocaleString()} tokens</span>
                                  <span>📝 Completion: {event.data.token_usage.completion_tokens?.toLocaleString()} tokens</span>
                                  <span>💰 Total: {event.data.token_usage.total_tokens?.toLocaleString()} tokens</span>
                                </div>
                              )}

                              {/* XF:JSON Schema */}
                              <details className="cursor-pointer" open>
                                <summary className="font-medium text-green-700 flex items-center">
                                  ✅ Generated XF:JSON Schema
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      navigator.clipboard.writeText(JSON.stringify(event.data.schema, null, 2))
                                      toast.success('Schema copied to clipboard!')
                                    }}
                                    className="ml-3 text-xs bg-green-100 hover:bg-green-200 text-green-700 px-2 py-1 rounded"
                                  >
                                    📋 Copy
                                  </button>
                                </summary>
                                <pre className="mt-2 p-4 bg-gray-50 rounded border border-gray-200 text-xs overflow-x-auto max-h-96">
                                  {JSON.stringify(event.data.schema, null, 2)}
                                </pre>
                              </details>
                            </div>
                          ) : (
                            /* Regular details for non-success events */
                            <details className="cursor-pointer">
                              <summary className="font-medium">View Details</summary>
                              <pre className="mt-2 p-3 bg-white rounded border border-gray-200 text-xs overflow-x-auto">
                                {JSON.stringify(event.data, null, 2)}
                              </pre>
                            </details>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
