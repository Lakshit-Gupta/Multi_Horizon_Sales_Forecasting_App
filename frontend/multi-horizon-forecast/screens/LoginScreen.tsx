import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, Alert, Platform } from 'react-native';
import { signInWithEmail } from '../services/auth';
import { configureGoogleSignIn, signInWithGoogle } from '../services/googleAuth';
import { StackNavigationProp } from '@react-navigation/stack';
import * as WebBrowser from 'expo-web-browser';
import { auth } from '../firebase.config';
import {
  FIREBASE_AUTH_DOMAIN,
  GOOGLE_WEB_CLIENT_ID
} from '@env';
// Register for redirects
WebBrowser.maybeCompleteAuthSession();

// Define the type for your navigation routes
type RootStackParamList = {
  LoginScreen: undefined;
  HomeScreen: undefined;
  TemplateScreen: undefined;
  ForecastScreen: undefined;
  InsightsScreen: undefined;
};

// Define the navigation prop type
type LoginScreenNavigationProp = StackNavigationProp<RootStackParamList, 'LoginScreen'>;

// Props interface
interface LoginScreenProps {
  navigation: LoginScreenNavigationProp;
}

const LoginScreen = ({ navigation }: LoginScreenProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Initialize Google Sign-In
  useEffect(() => {
    configureGoogleSignIn();
  }, []);
  
  // Handle Google sign in using the native Google Sign-In SDK
  const handleGoogleLogin = async () => {
    try {
      setIsLoading(true);
      const userCredential = await signInWithGoogle();
      console.log('Google sign in successful:', userCredential.user);
      // The auth state listener in App.tsx will handle navigation
    } catch (error) {
      console.error('Google sign in error:', error);
      Alert.alert('Login Failed', 'Failed to sign in with Google. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleEmailLogin = async () => {
    if (!email || !password) {
      Alert.alert('Input Error', 'Please enter both email and password');
      return;
    }

    try {
      setIsLoading(true);
      console.log("Attempting login with:", email); // Add this log
      const userCredential = await signInWithEmail(email, password);
      console.log("Login successful:", userCredential?.user?.uid); // Add this log
      
      // Fix the screen name to match what's in your navigator
      navigation.replace('HomeScreen'); // Change from 'Home' to 'HomeScreen'
      
    } catch (error: any) {
      console.error("Login error:", error.code, error.message); // Add this log
      let errorMessage = "Login failed. Please check your credentials.";
      if (error.code === 'auth/user-not-found') {
        errorMessage = "No account found with this email.";
      } else if (error.code === 'auth/wrong-password') {
        errorMessage = "Incorrect password.";
      } else if (error.code === 'auth/invalid-email') {
        errorMessage = "Invalid email format.";
      }
      Alert.alert('Login Failed', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Log the redirect URI for debugging
  useEffect(() => {
    try {
      // Using native Google Sign-In now, no need for redirect URI
      console.log('Auth Redirect URI: Using native Google Sign-In');
    } catch (error) {
      console.log('Error getting redirect URI:', error);
    }
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Log In</Text>
      
      <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
        placeholderTextColor="#97FEED99"
      />
      
      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        placeholderTextColor="#97FEED99"
      />
      
      <TouchableOpacity 
        style={styles.button}
        onPress={handleEmailLogin}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#050A30" />
        ) : (
          <Text style={styles.buttonText}>Log In</Text>
        )}
      </TouchableOpacity>
      
      {/* Fixed: Removed the logical OR in the style prop */}
      <TouchableOpacity 
        style={styles.googleButton}
        onPress={handleGoogleLogin}
        disabled={isLoading}
      >
        <Text style={styles.buttonText}>Sign in with Google</Text>
      </TouchableOpacity>
    </View>
  );
};

function isErrorResponse(response: any): response is { error: { message: string } } {
  return response && 'error' in response && response.error && 'message' in response.error;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#050A30',
  },
  gradient: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    color: '#97FEED',
    fontSize: 36,
    fontWeight: 'bold',
    marginBottom: 30,
  },
  input: {
    width: '100%',
    backgroundColor: '#050A30AA',
    color: '#97FEED',
    borderWidth: 1,
    borderColor: '#97FEED66',
    borderRadius: 5,
    padding: 12,
    marginBottom: 20,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#97FEED',
    borderRadius: 25,
    paddingVertical: 12,
    paddingHorizontal: 20,
    alignItems: 'center',
    width: '60%',
    marginBottom: 15,
  },
  googleButton: {
    backgroundColor: '#97FEED',
    borderRadius: 25,
    paddingVertical: 12,
    paddingHorizontal: 20,
    alignItems: 'center',
    width: '60%',
    marginBottom: 15,
  },
  buttonText: {
    color: '#050A30',
    fontSize: 16,
    fontWeight: '600',
  },
  registerLink: {
    marginTop: 20,
  },
  registerText: {
    color: '#97FEED',
    fontSize: 14,
  },
});

export default LoginScreen;