import * as WebBrowser from 'expo-web-browser';
import * as Google from 'expo-auth-session/providers/google';
import { makeRedirectUri } from 'expo-auth-session';
import { 
  GoogleAuthProvider, 
  signInWithCredential,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged 
} from 'firebase/auth';
import { auth } from '../firebase.config';
import { Platform } from 'react-native';

// Required for Expo auth redirects
WebBrowser.maybeCompleteAuthSession();

// Google Sign In hook
export const useGoogleSignIn = () => {
  const redirectUri = makeRedirectUri({
    scheme: 'multihorizonforecast'
  });
  
  console.log('Auth Redirect URI:', redirectUri);
  
  const [request, response, promptAsync] = Google.useIdTokenAuthRequest({
    webClientId: process.env.GOOGLE_WEB_CLIENT_ID,
    androidClientId: process.env.GOOGLE_ANDROID_CLIENT_ID,
    // Important: Always use proxy in Expo Go
    useProxy: Platform.OS !== 'web',
    redirectUri: redirectUri
  });

  const handleGoogleSignIn = async () => {
    if (response?.type === 'success') {
      try {
        const { id_token } = response.params;
        const credential = GoogleAuthProvider.credential(id_token);
        return await signInWithCredential(auth, credential);
      } catch (error) {
        console.error('Error during Google sign in:', error);
        throw error;
      }
    }
    return null;
  };

  return {
    request,
    response,
    promptAsync,
    handleGoogleSignIn
  };
};

// Sign in with email/password
export const signInWithEmail = async (email, password) => {
  try {
    console.log("Auth service: Attempting email login");
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    console.log("Auth service: Login successful");
    return userCredential;
  } catch (error) {
    console.error("Auth service: Login failed", error);
    throw error;
  }
};

// Register with email/password
export const registerWithEmail = async (email, password) => {
  try {
    const result = await createUserWithEmailAndPassword(auth, email, password);
    return result.user;
  } catch (error) {
    console.error('Error registering with email/password:', error);
    throw error;
  }
};

// Sign out
export const logOut = async () => {
  try {
    await signOut(auth);
  } catch (error) {
    console.error('Error signing out:', error);
    throw error;
  }
};

// Logout user
export const logoutUser = async () => {
  try {
    await signOut(auth);
    console.log('User signed out successfully');
    return true;
  } catch (error) {
    console.error('Logout error:', error);
    throw error;
  }
};

// Get current user
export const getCurrentUser = () => {
  return auth.currentUser;
};

// Get auth token for API calls
export const getAuthToken = async () => {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }
  return await user.getIdToken();
};

// Listen to auth changes
export const onAuthChange = (callback) => {
  return onAuthStateChanged(auth, callback);
};