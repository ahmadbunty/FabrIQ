import { useEffect, useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material'
import { Download, MoreVert } from '@mui/icons-material'
import toast from 'react-hot-toast'
import jsPDF from 'jspdf'
import 'jspdf-autotable'
import { getDailyReportsFromFirestore } from '../api/defectsApi'

export default function Reports() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [anchorEl, setAnchorEl] = useState(null)
  const [selectedReport, setSelectedReport] = useState(null)

  const handleMenuOpen = (event, report) => {
    setAnchorEl(event.currentTarget)
    setSelectedReport(report)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
    setSelectedReport(null)
  }

  useEffect(() => {
    const loadReports = async () => {
      try {
        const rows = await getDailyReportsFromFirestore()
        setReports(rows)
      } catch (err) {
        toast.error(err.message || 'Failed to load reports from Firestore')
      } finally {
        setLoading(false)
      }
    }
    loadReports()
  }, [])

  const exportPDF = (report) => {
    if (!report) return
    const doc = new jsPDF()
    doc.text('FabrIQ Inspection Report', 14, 20)
    doc.text(`Date: ${report.date}`, 14, 30)
    doc.text(`Total Inspections: ${report.totalInspections}`, 14, 40)
    doc.text(`Defects Found: ${report.defectsFound}`, 14, 50)
    doc.text(`Quality Score: ${report.qualityScore}%`, 14, 60)
    doc.save(`fabriq-report-${report.date}.pdf`)
    toast.success('Report exported successfully!')
  }

  const exportCSV = (report) => {
    if (!report) return
    const csv = `Date,Total Inspections,Defects Found,Quality Score\n${report.date},${report.totalInspections},${report.defectsFound},${report.qualityScore}`
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `fabriq-report-${report.date}.csv`
    a.click()
    toast.success('Report exported successfully!')
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4, alignItems: 'center' }}>
        <Box>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1,
            }}
          >
            Inspection Reports
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Download />}
          sx={{
            borderRadius: 2,
            textTransform: 'none',
            px: 3,
            py: 1,
            boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)',
          }}
        >
          {loading ? 'Loading...' : 'Export All'}
        </Button>
      </Box>
      <TableContainer
        component={Paper}
        sx={{
          borderRadius: 3,
          boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
          border: '1px solid rgba(0,0,0,0.05)',
        }}
      >
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Total Inspections</TableCell>
              <TableCell>Defects Found</TableCell>
              <TableCell>Quality Score</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {reports.map((report) => (
              <TableRow
                key={report.id}
                sx={{
                  '&:hover': {
                    bgcolor: 'action.hover',
                  },
                  transition: 'background-color 0.2s',
                }}
              >
                <TableCell sx={{ fontWeight: 500 }}>{formatDate(report.date)}</TableCell>
                <TableCell>{report.totalInspections}</TableCell>
                <TableCell>{report.defectsFound}</TableCell>
                <TableCell>{report.qualityScore}%</TableCell>
                <TableCell align="right">
                  <IconButton
                    onClick={(e) => handleMenuOpen(e, report)}
                    size="small"
                  >
                    <MoreVert />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {!loading && reports.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No report data available in Firestore.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem
          onClick={() => {
            exportPDF(selectedReport)
            handleMenuClose()
          }}
        >
          Export as PDF
        </MenuItem>
        <MenuItem
          onClick={() => {
            exportCSV(selectedReport)
            handleMenuClose()
          }}
        >
          Export as CSV
        </MenuItem>
      </Menu>
    </Box>
  )
}

