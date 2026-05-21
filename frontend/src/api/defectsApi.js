import {
  addDoc,
  collection,
  getDocs,
  orderBy,
  query,
  serverTimestamp,
} from 'firebase/firestore'
import { getDownloadURL, ref, uploadBytes } from 'firebase/storage'
import { db, ensureFirebaseAuth, storage } from '../database/firebase'

const DEFECTS_COLLECTION = 'defects'

/** Canonical Firestore defect_type slugs (7 classes, same as backend YOLO names). */
export const DEFECT_TYPES = [
  'contamination',
  'selvet',
  'gray_stitch',
  'cut',
  'baekra',
  'color_issue',
  'stain',
]

/**
 * Normalize API / legacy labels to canonical slug.
 */
export function normalizeDefectType(defectType) {
  if (!defectType) return 'contamination'
  const key = String(defectType).trim().toLowerCase().replace(/\s+/g, '_')

  const map = {
    // canonical
    contamination: 'contamination',
    selvet: 'selvet',
    selvedge: 'selvet',
    gray_stitch: 'gray_stitch',
    graystitch: 'gray_stitch',
    cut: 'cut',
    baekra: 'baekra',
    bakra: 'baekra',
    color_issue: 'color_issue',
    color_issues: 'color_issue',
    stain: 'stain',
    // legacy app names → closest new class
    hole: 'cut',
    objects: 'contamination',
    oil_spot: 'stain',
    thread_error: 'gray_stitch',
    misweave: 'selvet',
    broken_thread: 'gray_stitch',
  }
  if (DEFECT_TYPES.includes(key)) return key
  return map[key] || 'contamination'
}

export function formatDefectLabel(slug) {
  if (!slug) return 'Unknown'
  return String(slug)
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

/**
 * Uploads defect image to Firebase Storage and returns public URL.
 */
export async function uploadDefectImage(file, fabricId) {
  if (!storage) {
    throw new Error('Firebase Storage not initialized. Check frontend/.env Firebase keys.')
  }
  await ensureFirebaseAuth()
  const safeFabricId = fabricId || 'unknown_fabric'
  const fileName = `${Date.now()}_${file.name}`
  const filePath = `defects/${safeFabricId}/${fileName}`
  const storageRef = ref(storage, filePath)

  await uploadBytes(storageRef, file)
  const imageUrl = await getDownloadURL(storageRef)
  return imageUrl
}

/**
 * Adds a new defect record to Firestore.
 */
export async function addDefectRecord({
  fabric_id,
  defect_type,
  confidence,
  image_url,
  tracking_id,
  distance_meters,
  tracking_event,
}) {
  if (!db) {
    throw new Error('Firebase Firestore not initialized. Check frontend/.env Firebase keys.')
  }
  await ensureFirebaseAuth()
  const normalizedType = normalizeDefectType(defect_type)
  if (!DEFECT_TYPES.includes(normalizedType)) {
    throw new Error(
      `Invalid defect_type "${defect_type}". Allowed: ${DEFECT_TYPES.join(', ')}`
    )
  }

  const payload = {
    fabric_id: fabric_id || 'N/A',
    defect_type: normalizedType,
    confidence: Number(confidence ?? 0),
    image_url: image_url || '',
    timestamp: serverTimestamp(),
  }
  if (tracking_id != null && tracking_id !== '') {
    payload.tracking_id = Number(tracking_id)
  }
  if (distance_meters != null && !Number.isNaN(Number(distance_meters))) {
    payload.distance_meters = Number(distance_meters)
  }
  if (tracking_event) {
    payload.tracking_event = String(tracking_event)
  }

  const docRef = await addDoc(collection(db, DEFECTS_COLLECTION), payload)
  return docRef.id
}

/**
 * Convenience method: upload image then create defect document.
 */
export async function createDefectWithImage({
  fabric_id,
  defect_type,
  confidence,
  imageFile,
}) {
  const image_url = await uploadDefectImage(imageFile, fabric_id)
  const id = await addDefectRecord({
    fabric_id,
    defect_type,
    confidence,
    image_url,
  })
  return { id, image_url }
}

/**
 * Fetches all defect records from Firestore ordered by timestamp desc.
 */
export async function getAllDefects() {
  if (!db) {
    throw new Error('Firebase Firestore not initialized. Check frontend/.env Firebase keys.')
  }
  await ensureFirebaseAuth()
  let snap
  try {
    // Preferred path: server-side ordering when index/rules allow it.
    const q = query(collection(db, DEFECTS_COLLECTION), orderBy('timestamp', 'desc'))
    snap = await getDocs(q)
  } catch (err) {
    // Fallback: read without ordering, then sort client-side.
    // This keeps dashboard widgets functional even when timestamp ordering fails.
    const message = String(err?.message || '')
    const isQueryConfigIssue =
      message.includes('index') ||
      message.includes('order by') ||
      message.includes('FAILED_PRECONDITION')
    if (!isQueryConfigIssue) throw err
    snap = await getDocs(collection(db, DEFECTS_COLLECTION))
  }

  return snap.docs
    .map((doc) => ({
      id: doc.id,
      ...doc.data(),
    }))
    .sort((a, b) => (toDate(b.timestamp)?.getTime() || 0) - (toDate(a.timestamp)?.getTime() || 0))
}

function toDate(ts) {
  if (!ts) return null
  if (typeof ts.toDate === 'function') return ts.toDate()
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? null : d
}

function startDateForRange(range) {
  const now = new Date()
  const start = new Date(now)
  if (range === '24h') {
    start.setHours(now.getHours() - 24)
  } else if (range === '7d') {
    start.setDate(now.getDate() - 7)
  } else if (range === '30d') {
    start.setDate(now.getDate() - 30)
  } else if (range === '90d') {
    start.setDate(now.getDate() - 90)
  } else {
    start.setDate(now.getDate() - 7)
  }
  return start
}

export async function getDashboardStatsFromFirestore() {
  const defects = await getAllDefects()
  const totalInspections = defects.length
  const defectsDetected = defects.length
  const avgConfidence =
    defects.length > 0
      ? defects.reduce((sum, d) => sum + Number(d.confidence || 0), 0) / defects.length
      : 0
  const qualityScore = Math.round(avgConfidence * 100)
  const avgProcessingTime = 245

  return {
    totalInspections,
    defectsDetected,
    qualityScore,
    avgProcessingTime,
  }
}

export async function getRecentDetectionsFromFirestore(limit = 10) {
  const defects = await getAllDefects()
  return defects
    .sort((a, b) => (toDate(b.timestamp)?.getTime() || 0) - (toDate(a.timestamp)?.getTime() || 0))
    .slice(0, limit)
    .map((d) => ({
      class: d.defect_type || 'unknown',
      timestamp: toDate(d.timestamp)?.toISOString() || new Date().toISOString(),
      confidence: Number(d.confidence || 0),
      fabric_id: d.fabric_id || 'N/A',
    }))
}

export async function getDefectDistributionFromFirestore() {
  const defects = await getAllDefects()
  const counts = defects.reduce((acc, d) => {
    const key = d.defect_type || 'unknown'
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})
  return Object.entries(counts).map(([name, value]) => ({ name, value }))
}

export async function getDefectTrendsFromFirestore(range = '7d') {
  const defects = await getAllDefects()
  const start = startDateForRange(range)

  const perDay = {}
  defects.forEach((d) => {
    const date = toDate(d.timestamp)
    if (!date || date < start) return
    const key = date.toISOString().split('T')[0]
    perDay[key] = (perDay[key] || 0) + 1
  })

  return Object.entries(perDay)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({ date, count }))
}

export async function getQualityTrendsFromFirestore(range = '7d') {
  const defects = await getAllDefects()
  const start = startDateForRange(range)

  const perDay = {}
  defects.forEach((d) => {
    const date = toDate(d.timestamp)
    if (!date || date < start) return
    const key = date.toISOString().split('T')[0]
    const confidence = Number(d.confidence || 0)
    if (!perDay[key]) perDay[key] = []
    perDay[key].push(confidence)
  })

  return Object.entries(perDay)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, list]) => {
      const avg = list.reduce((s, x) => s + x, 0) / list.length
      return { date, count: Math.round(avg * 100) }
    })
}

export async function getDailyReportsFromFirestore() {
  const defects = await getAllDefects()
  const grouped = {}

  defects.forEach((d) => {
    const date = toDate(d.timestamp)
    if (!date) return
    const key = date.toISOString().split('T')[0]
    if (!grouped[key]) {
      grouped[key] = {
        date: key,
        totalInspections: 0,
        defectsFound: 0,
        confidenceSum: 0,
      }
    }
    grouped[key].totalInspections += 1
    grouped[key].defectsFound += 1
    grouped[key].confidenceSum += Number(d.confidence || 0)
  })

  return Object.values(grouped)
    .sort((a, b) => b.date.localeCompare(a.date))
    .map((r, idx) => ({
      id: idx + 1,
      date: r.date,
      totalInspections: r.totalInspections,
      defectsFound: r.defectsFound,
      qualityScore:
        r.totalInspections > 0
          ? Math.round((r.confidenceSum / r.totalInspections) * 100)
          : 0,
    }))
}
