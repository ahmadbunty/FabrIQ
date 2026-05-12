import { useState, useEffect } from 'react'
import { List, ListItem, ListItemText, Typography } from '@mui/material'
import { getRecentDetectionsFromFirestore, formatDefectLabel } from '../api/defectsApi'

export default function RecentDetections() {
  const [detections, setDetections] = useState([])

  useEffect(() => {
    fetchRecentDetections()
  }, [])

  const fetchRecentDetections = async () => {
    try {
      const response = await getRecentDetectionsFromFirestore(12)
      setDetections(response)
    } catch (error) {
      console.error('Failed to fetch recent detections:', error)
    }
  }

  if (detections.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No recent detections
      </Typography>
    )
  }

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    if (date.toDateString() === today.toDateString()) {
      return `Today at ${date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`
    } else if (date.toDateString() === yesterday.toDateString()) {
      return `Yesterday at ${date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`
    } else {
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    }
  }

  return (
    <List sx={{ maxHeight: 320, overflow: 'auto' }}>
      {detections.map((detection, index) => (
        <ListItem
          key={index}
          sx={{
            px: 0,
            py: 1.5,
            mb: 1,
            borderRadius: 2,
            bgcolor: 'action.hover',
            transition: 'all 0.2s',
            '&:hover': {
              bgcolor: 'action.selected',
              transform: 'translateX(4px)',
            },
          }}
        >
          <ListItemText
            primary={
              <Typography variant="body1" sx={{ fontWeight: 600 }}>
                {formatDefectLabel(detection.class)}
              </Typography>
            }
            secondary={
              <Typography variant="caption" color="text.secondary">
                {formatTimestamp(detection.timestamp)}
              </Typography>
            }
          />
        </ListItem>
      ))}
    </List>
  )
}

