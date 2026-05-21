import { useMemo } from 'react'
import {
  Paper,
  Typography,
  Box,
  Chip,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
} from '@mui/material'
import { CheckCircle, Cancel, ExpandMore, LocationOn, Download } from '@mui/icons-material'
import toast from 'react-hot-toast'
import { formatDefectLabel } from '../api/defectsApi'
import { resolveUploadMediaUrl } from '../utils/api'

export default function DetectionResult({ results }) {
  const { defects = [], annotatedImage, annotatedVideo, imageWidth, imageHeight, isVideo } = results
  const videoSrc = useMemo(() => resolveUploadMediaUrl(annotatedVideo), [annotatedVideo])
  const videoDownloadUrl = useMemo(
    () => (videoSrc ? `${videoSrc}${videoSrc.includes('?') ? '&' : '?'}download=1` : null),
    [videoSrc]
  )

  const handleDownloadVideo = async () => {
    if (!videoDownloadUrl) {
      toast.error('No annotated video available to download')
      return
    }
    try {
      const response = await fetch(videoDownloadUrl)
      if (!response.ok) throw new Error(`Download failed (${response.status})`)
      const blob = await response.blob()
      const objectUrl = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = objectUrl
      anchor.download = 'fabriq_annotated_video.mp4'
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      URL.revokeObjectURL(objectUrl)
      toast.success('Annotated video download started')
    } catch (err) {
      toast.error(err.message || 'Could not download annotated video')
    }
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Detection Results
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {isVideo
          ? 'Processed full video; preview shows first annotated frame.'
          : 'Image processed.'}
      </Typography>
      <Divider sx={{ my: 2 }} />
      {annotatedImage && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
            Annotated Image with Bounding Boxes
          </Typography>
          <img
            src={annotatedImage}
            alt="Detection results"
            style={{ width: '100%', borderRadius: 8, border: '2px solid #1976d2' }}
          />
          {imageWidth && imageHeight && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              Image Size: {imageWidth} × {imageHeight} pixels
            </Typography>
          )}
        </Box>
      )}
      {isVideo && videoSrc && (
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
              Annotated Video
            </Typography>
            <Button
              size="small"
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadVideo}
            >
              Download MP4
            </Button>
          </Box>
          <video
            src={videoSrc}
            controls
            preload="metadata"
            style={{ width: '100%', borderRadius: 8, border: '2px solid #1976d2' }}
          />
        </Box>
      )}
      <Divider sx={{ my: 2 }} />
      <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
        Detected Defects ({defects.length})
      </Typography>
      {defects.length > 0 ? (
        defects.map((defect, index) => (
          <Accordion key={index} sx={{ mb: 1 }}>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                <Chip
                  label={formatDefectLabel(defect.class)}
                  size="small"
                  color="error"
                  icon={<Cancel />}
                />
                <Typography variant="body2" sx={{ flexGrow: 1 }}>
                  Confidence: {Math.round(defect.confidence * 100)}%
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <LocationOn sx={{ fontSize: 16, verticalAlign: 'middle', mr: 0.5 }} />
                  Bounding Box Coordinates:
                </Typography>
                {defect.bbox && (
                  <Typography variant="caption" component="div" sx={{ fontFamily: 'monospace' }}>
                    X1: {defect.bbox[0]}, Y1: {defect.bbox[1]}<br />
                    X2: {defect.bbox[2]}, Y2: {defect.bbox[3]}
                  </Typography>
                )}
                {defect.bbox_normalized && (
                  <Typography variant="caption" component="div" sx={{ mt: 1, fontFamily: 'monospace' }}>
                    Normalized: ({defect.bbox_normalized[0].toFixed(3)}, {defect.bbox_normalized[1].toFixed(3)}) 
                    to ({defect.bbox_normalized[2].toFixed(3)}, {defect.bbox_normalized[3].toFixed(3)})
                  </Typography>
                )}
              </Box>
            </AccordionDetails>
          </Accordion>
        ))
      ) : (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
          <CheckCircle color="success" />
          <Typography variant="body2" color="text.secondary">
            No defects detected
          </Typography>
        </Box>
      )}
    </Paper>
  )
}

