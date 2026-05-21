import { initializeApp } from 'firebase/app'
import { getFirestore } from 'firebase/firestore'
import { getStorage } from 'firebase/storage'
import { getAuth, onAuthStateChanged, signInAnonymously } from 'firebase/auth'

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
const auth = getAuth(app)

let authReadyPromise = null

export async function ensureFirebaseAuth() {
  if (auth.currentUser) return auth.currentUser
  if (!authReadyPromise) {
    authReadyPromise = new Promise((resolve, reject) => {
      const unsubscribe = onAuthStateChanged(
        auth,
        async (user) => {
          try {
            if (user) {
              unsubscribe()
              resolve(user)
              return
            }
            const cred = await signInAnonymously(auth)
            unsubscribe()
            resolve(cred.user)
          } catch (err) {
            unsubscribe()
            reject(err)
          }
        },
        (err) => {
          unsubscribe()
          reject(err)
        }
      )
    }).finally(() => {
      authReadyPromise = null
    })
  }
  return authReadyPromise
}

export { app, db, storage, auth }