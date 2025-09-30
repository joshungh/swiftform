import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  IconButton,
  Tooltip
} from '@mui/material'
import {
  Download,
  ContentCopy,
  ArrowBack,
  CheckCircle,
  Error,
  Refresh
} from '@mui/icons-material'
// import ReactJson from 'react-json-view'
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter'
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json'
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs'
import { toast } from 'react-toastify'
import { getJobStatus } from '../services/api'

SyntaxHighlighter.registerLanguage('json', json)

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

const ResultPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState<string>('processing')
  const [formSchema, setFormSchema] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [processingTime, setProcessingTime] = useState<number | null>(null)
  const [tabValue, setTabValue] = useState(0)

  useEffect(() => {
    if (jobId) {
      checkJobStatus()
      const interval = setInterval(checkJobStatus, 2000)
      return () => clearInterval(interval)
    }
  }, [jobId])

  const checkJobStatus = async () => {
    if (!jobId) return

    try {
      const result = await getJobStatus(jobId)
      setStatus(result.status)

      if (result.status === 'completed') {
        setFormSchema(result.form_schema)
        setProcessingTime(result.processing_time)
        setLoading(false)
      } else if (result.status === 'failed') {
        setError(result.error || 'Processing failed')
        setLoading(false)
      } else if (result.status === 'processing') {
        // Continue polling
      }
    } catch (err) {
      console.error('Error checking job status:', err)
    }
  }

  const handleCopyJson = () => {
    if (formSchema) {
      navigator.clipboard.writeText(JSON.stringify(formSchema, null, 2))
      toast.success('JSON copied to clipboard!')
    }
  }

  const handleDownloadJson = () => {
    if (formSchema) {
      const blob = new Blob([JSON.stringify(formSchema, null, 2)], {
        type: 'application/json'
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `form-schema-${jobId}.json`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('JSON downloaded!')
    }
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '50vh'
        }}
      >
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 3 }}>
          Processing Document...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          This may take 10-30 seconds
        </Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="h6">Processing Failed</Typography>
          <Typography>{error}</Typography>
        </Alert>
        <Button
          variant="contained"
          startIcon={<ArrowBack />}
          onClick={() => navigate('/upload')}
        >
          Try Another Document
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, gap: 2 }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBack />}
          onClick={() => navigate('/upload')}
        >
          Back
        </Button>
        <Typography variant="h4" sx={{ flex: 1 }}>
          Form Generation Result
        </Typography>
        {status === 'completed' && (
          <Tooltip title="Processing completed successfully">
            <CheckCircle color="success" sx={{ fontSize: 32 }} />
          </Tooltip>
        )}
      </Box>

      {processingTime && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Form schema generated successfully in {processingTime.toFixed(2)} seconds!
        </Alert>
      )}

      {formSchema && (
        <Paper sx={{ mb: 3 }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                px: 2
              }}
            >
              <Tabs value={tabValue} onChange={handleTabChange}>
                <Tab label="Interactive View" />
                <Tab label="JSON View" />
                <Tab label="Form Preview" />
              </Tabs>
              <Box>
                <Tooltip title="Copy JSON">
                  <IconButton onClick={handleCopyJson}>
                    <ContentCopy />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Download JSON">
                  <IconButton onClick={handleDownloadJson}>
                    <Download />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <Box sx={{ maxHeight: '600px', overflow: 'auto' }}>
              <pre style={{
                padding: '20px',
                background: '#f4f4f4',
                borderRadius: '8px',
                fontSize: '14px'
              }}>
                {JSON.stringify(formSchema, null, 2)}
              </pre>
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box sx={{ maxHeight: '600px', overflow: 'auto' }}>
              <SyntaxHighlighter
                language="json"
                style={docco}
                customStyle={{
                  padding: '20px',
                  borderRadius: '8px',
                  fontSize: '14px'
                }}
              >
                {JSON.stringify(formSchema, null, 2)}
              </SyntaxHighlighter>
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <FormPreview schema={formSchema} />
          </TabPanel>
        </Paper>
      )}

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<Download />}
          onClick={handleDownloadJson}
        >
          Download JSON
        </Button>
        <Button
          variant="outlined"
          size="large"
          onClick={() => navigate('/upload')}
        >
          Process Another Document
        </Button>
      </Box>
    </Box>
  )
}

const FormPreview: React.FC<{ schema: any }> = ({ schema }) => {
  const renderField = (field: any) => {
    const { name, props } = field

    if (name === 'xf:group') {
      return (
        <Box key={props.xfName} sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            {props.xfLabel}
          </Typography>
          <Box sx={{ pl: 2 }}>
            {props.children?.map((child: any) => renderField(child))}
          </Box>
        </Box>
      )
    }

    return (
      <Box key={props.xfName} sx={{ mb: 2 }}>
        <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
          {props.xfLabel}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Type: {name} | Name: {props.xfName}
        </Typography>
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Form Structure Preview
      </Typography>
      {schema.props?.children?.map((page: any) => (
        <Paper key={page.props.xfName} sx={{ p: 3, mb: 2 }}>
          <Typography variant="h5" gutterBottom color="primary">
            {page.props.xfLabel}
          </Typography>
          {page.props.children?.map((field: any) => renderField(field))}
        </Paper>
      ))}
    </Box>
  )
}

export default ResultPage