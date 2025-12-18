# 📈 Multi-Horizon Sales Prediction Platform

This comprehensive platform utilizes the **Temporal Fusion Transformer (TFT)** model for accurate sales forecasting. The solution includes a **backend API**, **mobile application**, and **data preprocessing pipeline**. By leveraging **multi-horizon forecasting**, attention mechanisms, and advanced feature engineering, the platform provides precise predictions across different stores and products. This project was initially inspired by the **Microsoft Hackathon**.

![Sales Prediction Platform](https://img.shields.io/badge/Sales%20Prediction-Platform-blue)
![TFT Model](https://img.shields.io/badge/Model-Temporal%20Fusion%20Transformer-orange)
![Mobile](https://img.shields.io/badge/Platform-Mobile%20%26%20Web-green)

## 🎥 Demo
▶️ Watch the working demo here:
[Watch Demo on YouTube](https://youtu.be/toQsleM4aBQ)
## 🏗️ Project Structure

The project consists of three main components:

- **AI**: Data preprocessing notebooks and model training references
- **Backend**: FastAPI server with ONNX model deployment and Firebase authentication
- **Frontend**: React Native mobile application with Firebase integration

---

## ⚠️ Important: Before Using This Repository

This repository contains placeholder configurations for various services. Before using:

1. See the [SECURITY.md](./SECURITY.md) file for instructions on setting up your own credentials
2. Replace all placeholder API keys and configuration values with your own
3. Set up your own Firebase project and update the configuration files

---

## 💻 Run Locally

Clone the project:

```bash
git clone https://github.com/Lakshit-Gupta/Sales_Prediction.git
```

Go to the project directory:

```bash
cd Sales_Prediction
```

## 📥 Downloads and Releases
Check out the **[Releases](https://github.com/Lakshit-Gupta/Sales_Prediction/releases)** section for the following resources:

- **APK File**: Install and test the Android app directly on your device
- **ONNX Model**: The optimized TFT model for CPU inference
- **Sample Data**: Example datasets for testing the forecasting functionality

### Try the App Yourself!
Simply download the APK file from the releases section and install it on your Android device to experience the full functionality of the sales forecasting platform.

## ⚙️ Setting Up the Project

### Backend API Setup

1. Navigate to the Backend directory:
   ```bash
   cd Backend
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements_minimal.txt
   ```

3. Configure Firebase authentication:
   - Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
   - Generate a service account key and save it as `firebase-key.json` in the Backend directory
   - Update the project ID in `app_minimal.py`

4. Run the API locally:
   ```bash
   python -m uvicorn app_minimal:app --reload
   ```

### Mobile App Setup

1. Navigate to the Frontend directory:
   ```bash
   cd Frontend/multi-horizon-forecast
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   - Create a `.env` file with your Firebase and API configurations (see SECURITY.md)

4. Start the Expo development server:
   ```bash
   npm start
   ```

5. Follow the instructions to run on Android, iOS, or web

---

## 🐳 **Deployment Options**

### Backend API Deployment

#### Local Docker Deployment

1. Build the Docker image from the Backend directory:
   ```bash
   cd Backend
   docker build -t sales-prediction-api .
   ```

2. Run the Docker container:
   ```bash
   docker run -p 8000:8000 sales-prediction-api
   ```

3. Access the API at `http://localhost:8000`

#### Google Cloud Run Deployment

The Backend includes scripts for deploying to Google Cloud Run:

```bash
cd Backend
./deploy_to_gcp.ps1
```

See [GCP_DEPLOYMENT_GUIDE.md](./Backend/GCP_DEPLOYMENT_GUIDE.md) for detailed instructions.

### Mobile App Deployment

#### Ready to Use APK

For quick testing, download the pre-built APK from the [Releases](https://github.com/Lakshit-Gupta/Sales_Prediction/releases) section and install directly on your Android device.

#### Expo Build

Build the app for production using EAS:

```bash
cd Frontend/multi-horizon-forecast
npm install -g eas-cli
eas build --platform android  # or ios
```

For detailed mobile app deployment instructions, refer to the [Frontend README](./Frontend/multi-horizon-forecast/README.md).

---

## 📂 Platform Architecture

### Data Flow

```
[Historical Data] → [Data Preprocessing] → [TFT Model] → [ONNX Runtime] → [FastAPI Backend] → [Mobile App]
```

### Backend API Features

- **RESTful API**: Built with FastAPI for high performance
- **ONNX Runtime**: Optimized model inference
- **Firebase Authentication**: Secure access to forecast endpoints
- **User Data Storage**: Saves user forecasts to Firestore
- **Customizable Forecasting**: Adjustable parameters for different scenarios

### Mobile App Features

- **React Native & Expo**: Cross-platform mobile and web support
- **Firebase Auth**: Email and Google Sign-in options
- **Interactive Charts**: Visualize forecast results
- **Forecast Management**: Save, view, and analyze forecasts
- **Template System**: Quick access to common forecast scenarios

---

## 🏗️ Model Architecture

This project implements the **Temporal Fusion Transformer (TFT)**, which is a state-of-the-art deep learning model for time-series forecasting.

- **Multi-Horizon Forecasting**: Predicts future sales for multiple time periods simultaneously
- **Attention Mechanisms**: Identifies key patterns and relationships in the time series data
- **Feature Engineering**: Processes categorical and continuous variables through specialized networks
- **Variable Selection**: Dynamically selects the most important features for each prediction
- **Interpretability**: Provides attention scores to explain which inputs influenced the forecasts

### 🔹 Dataset Structure

The model is trained on historical sales data, including:

- **Store ID**: Unique identifier for each retail location
- **Item ID**: Unique identifier for each product
- **Time Index**: Temporal order of sales data
- **Sales**: Target variable to be predicted
- **Additional Features**: Promotional flags, holiday indicators, and other covariates

---

## 🔐 Security Considerations

This repository includes placeholder configurations for various services. Before deploying:

1. **Replace API Keys**: Update all placeholder keys and secrets with your own
2. **Firebase Setup**: Create your own Firebase project and update configurations
3. **Authentication**: Configure proper auth rules in Firebase console
4. **Secure Storage**: Set up Firestore security rules to protect user data

See [SECURITY.md](./SECURITY.md) for detailed instructions on securing the application.

---

## 📊 Mobile App Screenshots

<table>
  <tr>
    <td><img src="https://via.placeholder.com/200x400?text=Login+Screen" alt="Login Screen"/></td>
    <td><img src="https://via.placeholder.com/200x400?text=Forecast+Input" alt="Forecast Input"/></td>
    <td><img src="https://via.placeholder.com/200x400?text=Results+Screen" alt="Results Screen"/></td>
  </tr>
  <tr>
    <td align="center">Login Screen</td>
    <td align="center">Forecast Input</td>
    <td align="center">Results Screen</td>
  </tr>
</table>

> Note: Replace placeholder images with actual screenshots of your application

---

## � Features Roadmap

- [x] **Backend API with ONNX runtime**
- [x] **Mobile app with Firebase integration**
- [x] **Authentication and user data storage**
- [ ] **Advanced visualization options**
- [ ] **Batch forecasting capability**
- [ ] **User-defined model parameters**
- [ ] **Integration with external data sources**
- [ ] **Notification system for forecast alerts**

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🏆 Acknowledgments

- **Microsoft Hackathon** for the initial inspiration
- **Google Firebase** for authentication and data storage solutions
- **Huggingface** for the transformers architecture inspiration
- **Research papers on time-series forecasting**
- **React Native and Expo** communities for mobile development tools

