import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// Firebase Config
const firebaseConfig = {
  apiKey: "ENTER_YOUR_API_KEY",
  authDomain: "ENTER_YOUR_AUTH_DOMAIN",
  projectId: "ENTER_YOUR_PROJECT_ID",
  storageBucket: "ENTER_YOUR_STORAGE_BUCKET",
  messagingSenderId: "ENTER_YOUR_MESSAGING_SENDER_ID",
  appId: "ENTER_YOUR_APP_ID",
  measurementId: "ENTER_YOUR_MEASUREMENT_ID"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export { app, auth };