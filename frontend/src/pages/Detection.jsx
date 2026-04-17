import { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
} from '@mui/material'
import {
  PlayArrow,
  Stop,
  Upload,
  CameraAlt,
} from '@mui/icons-material'
import { useDropzone } from 'react-dropzone'
import { api } from '../utils/api'
import toast from 'react-hot-toast'
import DetectionResult from '../components/DetectionResult'
import { addDefectRecord, uploadDefectImage } from '../api/defectsApi'

export default function Detection() {
  const [isStreaming, setIsStreaming] = useState(false)
  const [isLiveDetecting, setIsLiveDetecting] = useState(false)
  const [liveStreamUrl, setLiveStreamUrl] = useState('')
  const [detectionResults, setDetectionResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [imagePreview, setImagePreview] = useState(null)
  const [videoPreview, setVideoPreview] = useState(null)
  const [isVideo, setIsVideo] = useState(false)
  const [cameraSources, setCameraSources] = useState([])
  const [selectedCameraIndex, setSelectedCameraIndex] = useState(0)
  const [customCameraIndex, setCustomCameraIndex] = useState('0')
  const [isCustomCamera, setIsCustomCamera] = useState(false)

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png'],
      'video/*': ['.mp4', '.mov', '.avi', '.mkv'],
    },
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        await handleImageUpload(acceptedFiles[0])
      }
    },
  })

  const handleImageUpload = async (file) => {
    setLoading(true)
    const isVideoFile = file.type.startsWith('video/')
    setIsVideo(isVideoFile)
    setImagePreview(isVideoFile ? null : URL.createObjectURL(file))
    setVideoPreview(isVideoFile ? URL.createObjectURL(file) : null)

    const formData = new FormData()
    formData.append('image', file)

    try {
      const response = await api.post('/detection/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setDetectionResults(response.data)
      toast.success('Detection completed!')

      // Persist detection results to Firestore
      try {
        const defects = response.data?.defects || []
        if (defects.length > 0) {
          const fabricId = `FAB-${new Date().getTime()}`
          let imageUrl = ''

          // For image uploads, store image in Firebase Storage once and reuse URL
          if (!isVideoFile) {
            imageUrl = await uploadDefectImage(file, fabricId)
          }

          await Promise.all(
            defects.map((defect) =>
              addDefectRecord({
                fabric_id: fabricId,
                defect_type: defect.class,
                confidence: defect.confidence,
                image_url: imageUrl,
              })
            )
          )
          toast.success('Detection data saved to Firestore')
        }
      } catch (dbError) {
        toast.error(`Detection worked, but DB save failed: ${dbError.message}`)
      }
    } catch (error) {
      toast.error('Detection failed: ' + (error.response?.data?.message || error.message))
    } finally {
      setLoading(false)
    }
  }

  const startStreaming = async () => {
    try {
      setIsLiveDetecting(false)
      const cameraIndexToUse = isCustomCamera
        ? Number.parseInt(customCameraIndex, 10) || 0
        : selectedCameraIndex
      const startResp = await api.post('/live/start', {
        cameraIndex: cameraIndexToUse,
      })
      const token = localStorage.getItem('fabriq_token')
      const baseUrl = api.defaults.baseURL.replace(/\/api\/?$/, '')
      setLiveStreamUrl(`${baseUrl}/api/live/stream?token=${encodeURIComponent(token || '')}&t=${Date.now()}`)
      setIsStreaming(true)
      setIsLiveDetecting(true)
      toast.success(
        `Live stream started${startResp?.data?.cameraIndex !== undefined ? ` (camera ${startResp.data.cameraIndex})` : ''}`
      )
    } catch (error) {
      toast.error('Failed to start live stream: ' + (error.response?.data?.message || error.message))
    }
  }

  const stopStreaming = async () => {
    try {
      await api.post('/live/stop')
    } catch (error) {
      console.error('Stop stream failed:', error?.response?.data || error.message)
    } finally {
      setLiveStreamUrl('')
      setIsLiveDetecting(false)
      setIsStreaming(false)
    }
  }

  useEffect(() => {
    const loadCameraSources = async () => {
      try {
        const response = await api.get('/live/sources')
        const presets = response?.data?.sources || []
        const withCustomOption = [
          ...presets,
          { label: 'Custom Camera Index', cameraIndex: -1 },
        ]
        const uniqueByIndex = withCustomOption.filter(
          (item, idx, arr) => idx === arr.findIndex((x) => x.cameraIndex === item.cameraIndex)
        )
        setCameraSources(uniqueByIndex)
        const activeIdx = response?.data?.activeCameraIndex
        if (typeof activeIdx === 'number') {
          setSelectedCameraIndex(activeIdx)
          setCustomCameraIndex(String(activeIdx))
          setIsCustomCamera(false)
        }
      } catch (error) {
        // fallback when endpoint is unavailable
        setCameraSources([
          { label: 'Laptop Camera (0)', cameraIndex: 0 },
          { label: 'USB/External Camera (1)', cameraIndex: 1 },
          { label: 'Arducam / CSI Camera (2)', cameraIndex: 2 },
          { label: 'Custom Camera', cameraIndex: -1 },
        ])
      }
    }
    loadCameraSources()
  }, [])

  useEffect(() => {
    return () => {
      stopStreaming()
    }
  }, [])

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
          Real-Time Defect Detection
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
        <Grid item xs={12} md={8}>
          <Paper
            sx={{
              p: 3,
              borderRadius: 3,
              boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
              border: '1px solid rgba(0,0,0,0.05)',
            }}
          >
            <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
              <FormControl size="small" sx={{ minWidth: 240 }}>
                <InputLabel>Camera Source</InputLabel>
                <Select
                  value={isCustomCamera ? -1 : selectedCameraIndex}
                  label="Camera Source"
                  onChange={(e) => {
                    const value = Number(e.target.value)
                    if (value === -1) {
                      setIsCustomCamera(true)
                    } else {
                      setIsCustomCamera(false)
                      setSelectedCameraIndex(value)
                      setCustomCameraIndex(String(value))
                    }
                  }}
                  disabled={isStreaming}
                >
                  {(cameraSources.length > 0
                    ? cameraSources
                    : [
                        { label: 'Laptop Camera (0)', cameraIndex: 0 },
                        { label: 'USB/External Camera (1)', cameraIndex: 1 },
                        { label: 'Arducam / CSI Camera (2)', cameraIndex: 2 },
                        { label: 'Custom Camera', cameraIndex: -1 },
                      ]
                  ).map((src) => (
                    <MenuItem key={`${src.label}-${src.cameraIndex}`} value={src.cameraIndex}>
                      {src.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {isCustomCamera && (
                <TextField
                  size="small"
                  label="Custom Index"
                  type="number"
                  value={customCameraIndex}
                  onChange={(e) => {
                    setCustomCameraIndex(e.target.value)
                    const parsed = Number(e.target.value)
                    if (Number.isInteger(parsed)) {
                      setSelectedCameraIndex(parsed)
                    }
                  }}
                  disabled={isStreaming}
                  sx={{ width: 140 }}
                />
              )}
              <Button
                variant="contained"
                startIcon={isStreaming ? <Stop /> : <PlayArrow />}
                onClick={isStreaming ? stopStreaming : startStreaming}
                sx={{
                  borderRadius: 2,
                  textTransform: 'none',
                  px: 3,
                  py: 1,
                  boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)',
                  '&:hover': {
                    boxShadow: '0 6px 16px rgba(25, 118, 210, 0.4)',
                  },
                }}
              >
                {isStreaming ? 'Stop Camera' : 'Start Camera'}
              </Button>
            </Box>
            {isStreaming && (
              <Box
                sx={{
                  position: 'relative',
                  width: '100%',
                  bgcolor: 'black',
                  borderRadius: 2,
                  overflow: 'hidden',
                  mb: 2,
                }}
              >
                <img
                  src={liveStreamUrl}
                  alt="Live annotated stream"
                  style={{ width: '100%', display: 'block' }}
                />
              </Box>
            )}
            <Box
              {...getRootProps()}
              sx={{
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'grey.300',
                borderRadius: 3,
                p: 4,
                textAlign: 'center',
                cursor: 'pointer',
                bgcolor: isDragActive
                  ? 'linear-gradient(135deg, rgba(25, 118, 210, 0.1) 0%, rgba(66, 165, 245, 0.1) 100%)'
                  : 'background.paper',
                background: isDragActive
                  ? 'linear-gradient(135deg, rgba(25, 118, 210, 0.05) 0%, rgba(66, 165, 245, 0.05) 100%)'
                  : 'background.paper',
                transition: 'all 0.3s ease',
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: 'action.hover',
                  transform: 'scale(1.01)',
                },
              }}
            >
              <input {...getInputProps()} />
              <Upload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" sx={{ mb: 1 }}>
                {isDragActive
                  ? 'Drop the image here'
                  : 'Drag & drop an image, or click to select'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Supports JPEG, PNG, MP4, MOV, AVI, MKV
              </Typography>
            </Box>
            {detectionResults?.annotatedImage && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
                  Detection Results with Bounding Boxes
                </Typography>
                <img
                  src={detectionResults.annotatedImage}
                  alt="Annotated with bounding boxes"
                  style={{ width: '100%', borderRadius: 8, border: '2px solid #1976d2' }}
                />
              </Box>
            )}
            {videoPreview && !detectionResults?.annotatedImage && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Original Video
                </Typography>
                <video
                  src={videoPreview}
                  controls
                  style={{ width: '100%', borderRadius: 8 }}
                />
              </Box>
            )}
            {imagePreview && !detectionResults?.annotatedImage && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Original Image
                </Typography>
                <img
                  src={imagePreview}
                  alt="Preview"
                  style={{ width: '100%', borderRadius: 8 }}
                />
              </Box>
            )}
            {isStreaming && (
              <Box sx={{ mt: 2 }}>
                <Chip
                  color={isLiveDetecting ? 'success' : 'default'}
                  icon={<CameraAlt />}
                  label={isLiveDetecting ? 'Live detection running' : 'Starting live detection...'}
                />
              </Box>
            )}
            {loading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                <CircularProgress />
              </Box>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          {detectionResults && (
            <DetectionResult results={detectionResults} />
          )}
          {!detectionResults && (
            <Paper
              sx={{
                p: 3,
                borderRadius: 3,
                boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                border: '1px solid rgba(0,0,0,0.05)',
              }}
            >
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                Detection Results
              </Typography>
              <Alert
                severity="info"
                sx={{
                  borderRadius: 2,
                  '& .MuiAlert-icon': {
                    alignItems: 'center',
                  },
                }}
              >
                Upload an image or start camera to begin detection
              </Alert>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  )
}

