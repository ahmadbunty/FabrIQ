# Firebase Setup for FabrIQ

This project now supports Firebase Firestore + Firebase Storage in the frontend.

## 1) Install dependency

From project root:

```bash
cd frontend
npm install
```

(`firebase` dependency is already added in `frontend/package.json`)

## 2) Create Firebase project

1. Open [Firebase Console](https://console.firebase.google.com/)
2. Create/select your project (e.g., `FabrIQ`)
3. Add a **Web App**
4. Copy the Firebase config values

## 3) Enable Firestore

1. Firebase Console -> **Firestore Database**
2. Create database (start in test mode for development)
3. Region: choose nearest region
4. Collection name: `defects`

## 4) Enable Storage

1. Firebase Console -> **Storage**
2. Get started (test mode for development)
3. Same region as Firestore

## 5) Add credentials to frontend

Create file: `frontend/.env`

```env
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

## 6) Firestore data model

Collection: `defects`

Each document:

```json
{
  "fabric_id": "FABRIC-001",
  "defect_type": "hole",
  "confidence": 0.92,
  "image_url": "https://...",
  "timestamp": "<serverTimestamp>"
}
```

Supported `defect_type` values:
- `hole`
- `stain`
- `broken_thread`
- `misweave`

## 7) Where code is placed

- Firebase initialization: `frontend/src/database/firebase.js`
- Database/storage API: `frontend/src/api/defectsApi.js`
- UI table component: `frontend/src/components/DefectsTable.jsx`
- Dashboard integration: `frontend/src/pages/Dashboard.jsx`

## 8) Run app

```bash
cd frontend
npm run dev
```

Open dashboard and you will see **Defects (Firestore)** table.

## 9) Security rules (recommended)

For development only (open access):

### Firestore rules
```txt
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /defects/{document=**} {
      allow read, write: if true;
    }
  }
}
```

### Storage rules
```txt
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /defects/{allPaths=**} {
      allow read, write: if true;
    }
  }
}
```

For production, lock these rules with Firebase Auth/roles.

