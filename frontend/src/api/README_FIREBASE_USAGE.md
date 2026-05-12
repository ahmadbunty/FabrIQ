## Firebase Usage (FabrIQ)

This frontend now includes Firebase integration for:

- Firestore collection: `defects`
- Firebase Storage folder: `defects/<fabric_id>/...`

### Available functions

From `src/api/defectsApi.js`:

- `uploadDefectImage(file, fabricId)`
- `addDefectRecord({ fabric_id, defect_type, confidence, image_url })`
- `createDefectWithImage({ fabric_id, defect_type, confidence, imageFile })`
- `getAllDefects()`
- `formatDefectLabel(slug)` — human-readable label from stored slug

### Defect schema

Each document in Firestore `defects`:

- `fabric_id`
- `defect_type` — one of: `contamination`, `selvet`, `gray_stitch`, `cut`, `baekra`, `color_issue`, `stain` (must match backend YOLO class names / indices 0–6)
- `confidence`
- `image_url`
- `timestamp`
