import { useState, useEffect } from 'react'
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
} from '@mui/material'
import {
  TrendingUp,
  Warning,
  CheckCircle,
  Assessment,
} from '@mui/icons-material'
import toast from 'react-hot-toast'
import StatCard from '../components/StatCard'
import RecentDetections from '../components/RecentDetections'
import DefectDistribution from '../components/DefectDistribution'
import DefectsTable from '../components/DefectsTable'
import { getDashboardStatsFromFirestore } from '../api/defectsApi'

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalInspections: 0,
    defectsDetected: 0,
    qualityScore: 0,
    avgProcessingTime: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const response = await getDashboardStatsFromFirestore()
      setStats(response)
    } catch (error) {
      toast.error(error.message || 'Failed to load dashboard data from Firestore')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LinearProgress />
  }

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
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
          Dashboard Overview
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
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Inspections"
            value={stats.totalInspections}
            icon={<Assessment />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Defects Detected"
            value={stats.defectsDetected}
            icon={<Warning />}
            color="#d32f2f"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Quality Score"
            value={`${stats.qualityScore}%`}
            icon={<CheckCircle />}
            color="#2e7d32"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Processing Time"
            value={`${stats.avgProcessingTime}ms`}
            icon={<TrendingUp />}
            color="#ed6c02"
          />
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper
            sx={{
              p: 3,
              height: 400,
              borderRadius: 3,
              boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
              border: '1px solid rgba(0,0,0,0.05)',
            }}
          >
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Defect Distribution
            </Typography>
            <DefectDistribution />
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 3,
              height: 400,
              borderRadius: 3,
              boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
              border: '1px solid rgba(0,0,0,0.05)',
            }}
          >
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Recent Detections
            </Typography>
            <RecentDetections />
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <DefectsTable />
        </Grid>
      </Grid>
    </Box>
  )
}

