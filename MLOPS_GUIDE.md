# FabrIQ MLOps Guide

This guide gives a practical MLOps flow for FabrIQ so you can train, validate, deploy, and monitor updates safely.

## 1) Repository and Branch Strategy

- Use `main` for production-ready code.
- Use short-lived feature branches (`feat/live-stream`, `fix/firebase`).
- Open PRs into `main`.
- Require GitHub Actions (`FabrIQ CI`) to pass before merge.

## 2) Source of Truth

- **Code**: GitHub repository.
- **Experiment output**: local `runs/` (ignored by git) and optionally artifact store.
- **Model registry (recommended next)**:
  - Option A: GitHub Releases (attach `best.pt` with version notes).
  - Option B: DVC + remote storage (S3/GCS/Azure/Drive).

## 3) Data and Labels

- Keep large datasets out of git (`.gitignore` already covers common dataset folders).
- Track dataset versions in a changelog file (`data/CHANGELOG.md`) or DVC.
- Keep `fabriq_detection_data.yaml` versioned in git.

## 4) CI/CD (already added)

Workflow file: `.github/workflows/ci.yml`

It runs:
- Frontend: install, lint, build.
- Backend: install requirements and import smoke check.

## 5) Training Pipeline (recommended runbook)

Use this repeatable sequence:

1. Prepare dataset
   - `python organize_dataset.py`
   - `python create_pseudo_annotations.py` (if needed for detection)
2. Train model
   - `python train_yolo_detection.py`
3. Validate in notebook or inference script
   - `python inference.py ...`
4. Promote best model
   - copy promoted weights to `models/production/best.pt` (ignored in git if large)
5. Deploy backend with model path
   - set env: `FABRIQ_MODEL_PATH=/path/to/best.pt`

## 6) Deployment Environments

- **Dev**: local machine (`python app.py`, `npm run dev`)
- **Staging**: optional VM/container for QA
- **Production**: Jetson Nano + camera hardware

For Jetson:
- Set camera index via env:
  - `FABRIQ_CAMERA_INDEX=0` (or 1/2 based on detected source)
- Keep fallback camera options in UI selector.

## 7) Monitoring and Ops Checklist

- Track:
  - average confidence
  - defect distribution shift
  - camera stream uptime
  - inference FPS
- Add periodic checks:
  - `/api/health` for uptime
  - sample prediction sanity checks after deployment
- Log model version in backend startup logs.

## 8) Suggested Next MLOps Upgrades

- Add automated backend tests (`pytest`) for `/api/health`, `/api/live/start`, `/api/detection/analyze`.
- Add model version endpoint (`/api/model/info`) with commit hash and model id.
- Add dataset version file and enforce in training scripts.
- Add scheduled retraining workflow (weekly/manual trigger) with artifact upload.

