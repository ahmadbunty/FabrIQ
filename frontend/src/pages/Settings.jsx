import { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Grid,
} from '@mui/material'
import { Save } from '@mui/icons-material'
import toast from 'react-hot-toast'

export default function Settings() {
  const [settings, setSettings] = useState({
    detectionThreshold: 0.5,
    enableNotifications: true,
    autoExport: false,
    qualityThreshold: 80,
  })

  const handleChange = (field, value) => {
    setSettings((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = () => {
    // Save settings to backend
    toast.success('Settings saved successfully!')
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
        Settings
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Detection Settings
            </Typography>
            <TextField
              fullWidth
              label="Detection Threshold"
              type="number"
              value={settings.detectionThreshold}
              onChange={(e) =>
                handleChange('detectionThreshold', parseFloat(e.target.value))
              }
              inputProps={{ min: 0, max: 1, step: 0.1 }}
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Quality Threshold (%)"
              type="number"
              value={settings.qualityThreshold}
              onChange={(e) =>
                handleChange('qualityThreshold', parseInt(e.target.value))
              }
              inputProps={{ min: 0, max: 100 }}
            />
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Preferences
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableNotifications}
                  onChange={(e) =>
                    handleChange('enableNotifications', e.target.checked)
                  }
                />
              }
              label="Enable Notifications"
              sx={{ mb: 2, display: 'block' }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={settings.autoExport}
                  onChange={(e) =>
                    handleChange('autoExport', e.target.checked)
                  }
                />
              }
              label="Auto Export Reports"
            />
            <Divider sx={{ my: 3 }} />
            <Button
              variant="contained"
              startIcon={<Save />}
              onClick={handleSave}
            >
              Save Settings
            </Button>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

