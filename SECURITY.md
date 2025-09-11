# Security and Configuration Setup

## Required Configuration Files

Before using this application, you need to set up the following configuration files with your own credentials:

### Backend Configuration

1. **Firebase Service Account (`firebase-key.json`)**
   - Replace with your own Firebase service account credentials
   - Format should match the provided template with your own values

2. **Environment Variables**
   - Configure any needed environment variables for your deployment environment

### Frontend Configuration

1. **Google Auth Credentials**
   - Replace placeholder values in the following files with your own credentials:
     - `android_app_client_secret_*.json` 
     - `Web_app_client_secret_*.json`
     - `google-services.json`

2. **Firebase Configuration**
   - Update `firebase.config.ts` and `firebase.config.js` with your own Firebase project details

3. **Environment Variables (.env)**
   - Create a `.env` file with your configuration:
     ```
     # Firebase Configuration
     FIREBASE_API_KEY="your_api_key_here"
     FIREBASE_AUTH_DOMAIN="your_auth_domain_here"
     FIREBASE_PROJECT_ID="your_project_id_here"
     FIREBASE_STORAGE_BUCKET="your_storage_bucket_here"
     FIREBASE_MESSAGING_SENDER_ID="your_messaging_sender_id_here"
     FIREBASE_APP_ID="your_app_id_here"
     FIREBASE_MEASUREMENT_ID="your_measurement_id_here"
     
     # Google Auth Client IDs
     GOOGLE_WEB_CLIENT_ID="your_web_client_id_here"
     GOOGLE_ANDROID_CLIENT_ID="your_android_client_id_here"
     
     # API URL
     API_URL="your_cloud_run_url_here"
     ```

4. **Expo Configuration**
   - Update `app.json` with your own Expo project details:
     - Update `slug`, `scheme`, `owner`, and `projectId`
     - Update Android package name

5. **Android Configuration**
   - Update Android-specific files:
     - `android/app/build.gradle`: Replace package name, application ID, and keystore credentials
     - `android/app/src/main/AndroidManifest.xml`: Update Expo project ID and URL scheme
     - Update Java package path in:
       - `android/app/src/main/java/com/yourusername/yourappname/MainActivity.kt`
       - `android/app/src/main/java/com/yourusername/yourappname/MainApplication.kt`
     - Note: You'll need to create the appropriate directory structure for your package name

## Security Checklist

- [ ] Replace all API keys and secrets with your own values
- [ ] Update all project IDs with your own project IDs
- [ ] Replace all package names and bundle identifiers
- [ ] Update all OAuth client IDs and secrets
- [ ] Set up proper Firebase security rules for your project
- [ ] Configure proper authentication and authorization
