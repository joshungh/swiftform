import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Button,
  TextField,
  InputAdornment,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Tooltip
} from '@mui/material'
import {
  Download,
  Delete,
  Visibility,
  Search,
  Refresh,
  Clear,
  ContentCopy,
  Description
} from '@mui/icons-material'
import { toast } from 'react-toastify'
import axios from 'axios'

const API_URL = 'http://localhost:8000/api'

interface HistoryEntry {
  id: string
  filename: string
  file_type: string
  created_at: string
  processing_time: number
  pages_count: number
  fields_count: number
  form_schema?: any
}

const HistoryPage: React.FC = () => {
  const navigate = useNavigate()
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedEntry, setSelectedEntry] = useState<HistoryEntry | null>(null)
  const [viewDialogOpen, setViewDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [entryToDelete, setEntryToDelete] = useState<string | null>(null)

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_URL}/history`)
      setHistory(response.data.history)
    } catch (error) {
      toast.error('Failed to load history')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadHistory()
      return
    }

    setLoading(true)
    try {
      const response = await axios.get(`${API_URL}/history/search/${searchQuery}`)
      setHistory(response.data.results)
    } catch (error) {
      toast.error('Search failed')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleView = async (entryId: string) => {
    try {
      const response = await axios.get(`${API_URL}/history/${entryId}`)
      setSelectedEntry(response.data)
      setViewDialogOpen(true)
    } catch (error) {
      toast.error('Failed to load entry')
      console.error(error)
    }
  }

  const handleDownload = async (entryId: string, filename: string) => {
    try {
      const response = await axios.get(`${API_URL}/history/${entryId}`)
      const formSchema = response.data.form_schema

      const blob = new Blob([JSON.stringify(formSchema, null, 2)], {
        type: 'application/json'
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${filename.replace(/\.[^/.]+$/, '')}_form.json`
      a.click()
      URL.revokeObjectURL(url)

      toast.success('Form downloaded successfully')
    } catch (error) {
      toast.error('Failed to download form')
      console.error(error)
    }
  }

  const handleDelete = async () => {
    if (!entryToDelete) return

    try {
      await axios.delete(`${API_URL}/history/${entryToDelete}`)
      toast.success('Entry deleted successfully')
      setDeleteDialogOpen(false)
      setEntryToDelete(null)
      loadHistory()
    } catch (error) {
      toast.error('Failed to delete entry')
      console.error(error)
    }
  }

  const handleClearHistory = async () => {
    if (!window.confirm('Are you sure you want to clear all history? This cannot be undone.')) {
      return
    }

    try {
      await axios.delete(`${API_URL}/history`)
      toast.success('History cleared successfully')
      loadHistory()
    } catch (error) {
      toast.error('Failed to clear history')
      console.error(error)
    }
  }

  const handleCopyJson = (formSchema: any) => {
    navigator.clipboard.writeText(JSON.stringify(formSchema, null, 2))
      .then(() => {
        toast.success('JSON copied to clipboard')
      })
      .catch(() => {
        toast.error('Failed to copy JSON')
      })
  }

  const formatDate = (isoDate: string) => {
    const date = new Date(isoDate)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
  }

  const getFileTypeColor = (fileType: string) => {
    const colors: { [key: string]: string } = {
      '.pdf': 'error',
      '.doc': 'primary',
      '.docx': 'primary',
      '.xls': 'success',
      '.xlsx': 'success'
    }
    return colors[fileType] || 'default'
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Form Generation History</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadHistory}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<Clear />}
            onClick={handleClearHistory}
            disabled={history.length === 0}
          >
            Clear All
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search by filename..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
            endAdornment: searchQuery && (
              <InputAdornment position="end">
                <IconButton size="small" onClick={() => { setSearchQuery(''); loadHistory(); }}>
                  <Clear />
                </IconButton>
              </InputAdornment>
            )
          }}
        />
      </Paper>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : history.length === 0 ? (
        <Alert severity="info">
          No history found. Upload and process documents to see them here.
        </Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>File Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Date Created</TableCell>
                <TableCell align="center">Pages</TableCell>
                <TableCell align="center">Fields</TableCell>
                <TableCell align="center">Processing Time</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {history.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Description color="action" />
                      {entry.filename}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={entry.file_type}
                      size="small"
                      color={getFileTypeColor(entry.file_type) as any}
                    />
                  </TableCell>
                  <TableCell>{formatDate(entry.created_at)}</TableCell>
                  <TableCell align="center">{entry.pages_count}</TableCell>
                  <TableCell align="center">{entry.fields_count}</TableCell>
                  <TableCell align="center">{entry.processing_time.toFixed(1)}s</TableCell>
                  <TableCell align="right">
                    <Tooltip title="View">
                      <IconButton size="small" onClick={() => handleView(entry.id)}>
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Download">
                      <IconButton
                        size="small"
                        onClick={() => handleDownload(entry.id, entry.filename)}
                      >
                        <Download />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => {
                          setEntryToDelete(entry.id)
                          setDeleteDialogOpen(true)
                        }}
                      >
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* View Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedEntry?.filename}
          <IconButton
            onClick={() => selectedEntry && handleCopyJson(selectedEntry.form_schema)}
            sx={{ float: 'right' }}
          >
            <ContentCopy />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Created: {selectedEntry && formatDate(selectedEntry.created_at)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Pages: {selectedEntry?.pages_count} | Fields: {selectedEntry?.fields_count}
            </Typography>
          </Box>
          <Paper sx={{ p: 2, bgcolor: 'grey.100', maxHeight: 400, overflow: 'auto' }}>
            <pre style={{ margin: 0, fontSize: '12px' }}>
              {selectedEntry && JSON.stringify(selectedEntry.form_schema, null, 2)}
            </pre>
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          <Button
            variant="contained"
            startIcon={<Download />}
            onClick={() => {
              if (selectedEntry) {
                handleDownload(selectedEntry.id, selectedEntry.filename)
              }
            }}
          >
            Download
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this entry? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDelete}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default HistoryPage