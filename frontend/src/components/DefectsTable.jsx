import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import { getAllDefects } from '../api/defectsApi'

function formatTimestamp(ts) {
  if (!ts) return 'Pending...'
  // Firestore Timestamp
  if (typeof ts.toDate === 'function') return ts.toDate().toLocaleString()
  // ISO string fallback
  return new Date(ts).toLocaleString()
}

function confidenceLabel(value) {
  if (value === undefined || value === null) return '0.00'
  return Number(value).toFixed(2)
}

export default function DefectsTable() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadDefects = async () => {
    try {
      setLoading(true)
      setError('')
      const data = await getAllDefects()
      setRows(data)
    } catch (err) {
      setError(err.message || 'Failed to load defects from Firestore')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDefects()
  }, [])

  return (
    <Paper
      sx={{
        p: 3,
        borderRadius: 3,
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
        border: '1px solid rgba(0,0,0,0.05)',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Defects (Firestore)
        </Typography>
        <Box>
          <Button
            variant="outlined"
            size="small"
            startIcon={<RefreshIcon />}
            onClick={loadDefects}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 5 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : rows.length === 0 ? (
        <Alert severity="info">No defects found in Firestore.</Alert>
      ) : (
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Image</TableCell>
                <TableCell>Fabric ID</TableCell>
                <TableCell>Defect Type</TableCell>
                <TableCell>Confidence</TableCell>
                <TableCell>Timestamp</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.id} hover>
                  <TableCell>
                    {row.image_url ? (
                      <img
                        src={row.image_url}
                        alt={row.defect_type}
                        style={{
                          width: 72,
                          height: 48,
                          objectFit: 'cover',
                          borderRadius: 8,
                          border: '1px solid #ddd',
                        }}
                      />
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        No Image
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>{row.fabric_id || 'N/A'}</TableCell>
                  <TableCell>
                    <Chip label={row.defect_type || 'unknown'} size="small" color="error" />
                  </TableCell>
                  <TableCell>{confidenceLabel(row.confidence)}</TableCell>
                  <TableCell>{formatTimestamp(row.timestamp)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  )
}
