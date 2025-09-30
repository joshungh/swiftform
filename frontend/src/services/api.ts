import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export interface UploadResponse {
  file_id: string
  filename: string
  file_type: string
  status: string
  message: string
}

export interface ProcessRequest {
  file_id: string
  ai_model?: string
  custom_instructions?: string
}

export interface ProcessResponse {
  job_id: string
  status: string
  message: string
}

export interface JobStatusResponse {
  job_id: string
  status: string
  form_schema?: any
  error?: string
  processing_time?: number
}

export const uploadDocument = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })

  return response.data
}

export const processDocument = async (
  request: ProcessRequest
): Promise<ProcessResponse> => {
  const response = await api.post<ProcessResponse>('/process', request)
  return response.data
}

export const getJobStatus = async (
  jobId: string
): Promise<JobStatusResponse> => {
  const response = await api.get<JobStatusResponse>(`/status/${jobId}`)
  return response.data
}

export const validateSchema = async (schema: any): Promise<any> => {
  const response = await api.post('/validate', schema)
  return response.data
}

export const getExamples = async (): Promise<any> => {
  const response = await api.get('/examples')
  return response.data
}

export default api