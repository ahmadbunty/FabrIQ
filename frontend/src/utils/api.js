import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('fabriq_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('fabriq_user')
      localStorage.removeItem('fabriq_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

function backendOrigin() {
  return (import.meta.env.VITE_API_URL || 'http://localhost:5000/api').replace(/\/api\/?$/, '')
}

/**
 * Turn backend upload paths into a URL the browser can load (Vite proxies /api in dev).
 */
export function resolveUploadMediaUrl(pathOrUrl) {
  if (!pathOrUrl) return null
  if (pathOrUrl.startsWith('data:') || pathOrUrl.startsWith('blob:')) return pathOrUrl

  let path = pathOrUrl
  if (pathOrUrl.startsWith('http://') || pathOrUrl.startsWith('https://')) {
    try {
      const u = new URL(pathOrUrl)
      if (u.pathname.startsWith('/uploads/') || u.pathname.startsWith('/api/uploads/')) {
        path = u.pathname.startsWith('/api/') ? u.pathname : `/api${u.pathname}`
      } else {
        return pathOrUrl
      }
    } catch {
      return pathOrUrl
    }
  } else if (path.startsWith('/uploads/')) {
    path = `/api${path}`
  } else if (!path.startsWith('/api/uploads/')) {
    path = `/api/uploads/${path.replace(/^\/+/, '')}`
  }

  if (import.meta.env.DEV) {
    return path
  }
  return `${backendOrigin()}${path}`
}

export default api

