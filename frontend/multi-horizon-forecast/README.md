# Multi-Horizon Forecast

A robust forecasting application for retail analytics that provides multi-horizon sales predictions with confidence intervals. This tool helps businesses make data-driven decisions about inventory management, staffing, and promotions.

## Project Overview

Multi-Horizon Forecast is a React Native mobile application that allows retailers to:

- Upload historical sales data through a standardized template
- Generate machine learning-based sales forecasts with various confidence levels (P10, P50, P90)
- Visualize predictions with interactive charts
- Simulate "what-if" scenarios by adjusting promotion status and holiday settings
- Save and revisit previous forecasts for comparison
- Export and share forecast results

The application uses Firebase for authentication and Google Cloud Platform for backend processing of forecasting models.

## Features

- **User Authentication**: Secure login with email/password through Firebase Auth
- **Data Upload**: Excel/CSV template-based data upload system
- **Forecast Generation**: Machine learning models providing accurate sales predictions
- **Confidence Intervals**: Three prediction levels (pessimistic, expected, optimistic)
- **Interactive Controls**: Adjust promotion status and holiday flags to see changing predictions
- **Responsive Design**: Works on various Android devices
- **Offline Access**: View previously generated forecasts without an internet connection

## Technical Stack

- **Frontend**: React Native, Expo
- **Authentication**: Firebase Authentication
- **Backend**: Google Cloud Platform (GCP)
- **Data Visualization**: React Native Chart libraries
- **File Handling**: Expo Document Picker, File System

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- npm or yarn
- Java Development Kit (JDK) 11
- Android Studio (for Android development)
- Firebase account
- Google Cloud Platform account

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/Lakshit-Gupta/multi-horizon-forecast.git
   cd multi-horizon-forecast
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Set up your environment variables in a `.env` file:
   ```
   FIREBASE_API_KEY=your_firebase_api_key
   FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain
   FIREBASE_PROJECT_ID=your_firebase_project_id
   FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket
   FIREBASE_MESSAGING_SENDER_ID=your_firebase_messaging_sender_id
   FIREBASE_APP_ID=your_firebase_app_id
   FIREBASE_MEASUREMENT_ID=your_firebase_measurement_id
   API_URL=your_api_url
   ```

### Running the App

#### Option 1: Download the Release APK

The easiest way to use the app is to download the pre-built APK from the [Releases](https://github.com/Lakshit-Gupta/multi-horizon-forecast/releases) section of this GitHub repository.

#### Option 2: Development Mode (For Developers)

If you want to run the app in development mode:

1. Install development dependencies:
   ```
   npm install expo-dev-client
   ```

2. Build and run a development client:
   ```
   npx expo run:android
   ```
   
   This creates a special development build with native modules that can connect to your local development server.

3. Once installed on your device/emulator, start the development server:
   ```
   npx expo start --dev-client
   ```

Note: Unlike Expo Go, the development client build includes all native modules and can work with custom native code modifications.

### Building a Production Release APK

1. Navigate to the Android directory:
   ```
   cd android
   ```

2. Clean the build folder:
   ```
   ./gradlew clean
   ```

3. Build the release APK:
   ```
   ./gradlew assembleRelease
   ```

4. The APK will be available at:
   ```
   android/app/build/outputs/apk/release/app-release.apk
   ```

### Using the App

1. Log in using your Firebase credentials
2. Download the template from the Template screen
3. Fill the template with your historical sales data
4. Upload the completed template
5. Enter item and store details if prompted
6. View and interact with the generated forecast
7. Save important forecasts for future reference

## Troubleshooting

- **Build Failures**: Try cleaning the project with `./gradlew clean` and rebuilding
- **Login Issues**: Verify Firebase credentials in the console
- **Template Errors**: Ensure your data matches the exact format of the template
- **File Upload Problems**: Check your internet connection and file permissions
- **Blank Screens**: Verify API connections and Firebase configuration

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or support, please contact: [Your contact information]
