import { GoogleSignin } from '@react-native-google-signin/google-signin';
import { auth } from '../firebase.config';
import { GoogleAuthProvider, signInWithCredential } from 'firebase/auth';
import { GOOGLE_WEB_CLIENT_ID } from '@env';
import { Platform } from 'react-native';

/**
 * Configure Google Sign-In
 * Should be called once during app initialization
 */
export const configureGoogleSignIn = () => {
  GoogleSignin.configure({
    webClientId: GOOGLE_WEB_CLIENT_ID,
    offlineAccess: true,
    // androidClientId is not needed when using Firebase with webClientId
  });
};

/**
 * Sign in with Google
 * @returns {Promise<UserCredential>} Firebase user credential
 */
export const signInWithGoogle = async () => {
  try {
    console.log("Starting Google sign-in process...");
    
    // Check if user is already signed in with Google
    await GoogleSignin.signOut();
    
    // Check if device supports Google Play
    await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
    console.log("Play Services check passed");
    
    // Perform Google sign in
    console.log("Calling GoogleSignin.signIn()");
    const signInResult = await GoogleSignin.signIn();
    console.log("Google Sign in response type:", typeof signInResult);
    
    // Extract token based on response format
    let idToken = null;
    
    if (signInResult && typeof signInResult === 'object') {
      if (signInResult.idToken) {
        idToken = signInResult.idToken;
      } else if (signInResult.data && signInResult.data.idToken) {
        idToken = signInResult.data.idToken;
      }
    }
    
    if (!idToken) {
      console.error("No ID token found in response. Response structure:", 
        JSON.stringify(Object.keys(signInResult || {})));
      throw new Error('No ID token returned from Google Sign-In');
    }
    
    // Create a Firebase credential from the token
    console.log("Creating Firebase credential with token (first 20 chars):", idToken.substring(0, 20));
    const googleCredential = GoogleAuthProvider.credential(idToken);
    
    // Sign in to Firebase with the Google credential
    console.log("Signing in with Firebase");
    return await signInWithCredential(auth, googleCredential);
  } catch (error) {
    console.error('Google sign in error:', error);
    throw error;
  }
};

/**
 * Sign out from Google
 */
export const googleSignOut = async () => {
  try {
    await GoogleSignin.revokeAccess();
    await GoogleSignin.signOut();
  } catch (error) {
    console.error('Google sign out error:', error);
    throw error;
  }
};
