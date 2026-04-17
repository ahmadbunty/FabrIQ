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

### Defect schema

Each document in Firestore `defects`:

- `fabric_id`
- `defect_type` (`hole`, `stain`, `broken_thread`, `misweave`)
- `confidence`
- `image_url`
- `timestamp`

