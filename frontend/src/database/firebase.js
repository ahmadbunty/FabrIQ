import { initializeApp } from 'firebase/app'
import { getFirestore } from 'firebase/firestore'
import { getStorage } from 'firebase/storage'

// Firebase credentials provided by user
const firebaseConfig = {
  apiKey: 'AIzaSyBZrJrSI__6qqOsx20E5xAYURg6TmOB1uA',
  authDomain: 'fabriq-aaa9c.firebaseapp.com',
  projectId: 'fabriq-aaa9c',
  storageBucket: 'fabriq-aaa9c.firebasestorage.app',
  messagingSenderId: '721813596434',
  appId: '1:721813596434:web:4ceba3861ea6f0629c2bcb',
  measurementId: 'G-H9E74JTL8B',
}

const app = initializeApp(firebaseConfig)
const db = getFirestore(app)
const storage = getStorage(app)

export { app, db, storage }