# Sales Prediction API

A FastAPI application for sales prediction using a Temporal Fusion Transformer (TFT) model in ONNX format. This API is designed to be deployed on Google Cloud Run.

## Features

- 7-day sales forecasting with percentile predictions (p10, p50, p90)
- Firebase authentication
- Excel file uploads for historical data
- Holiday and promotion toggle support
- ONNX model integration for efficient inference

## Prerequisites

- Python 3.10
- Firebase project with authentication enabled
- Google Cloud Platform account
- ONNX model file (tft_model_cpu.onnx)

## Local Setup

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements_minimal.txt
   ```

4. **Add required files:**

   - Place `tft_model_cpu.onnx` in the root directory
   - Add your Firebase service account key as `firebase-key.json`

5. **Run the server locally:**

   ```bash
   uvicorn app_minimal:app --reload
   ```

   The API will be available at http://localhost:8000

## API Endpoints

### Authentication

- `GET /auth-test` - Test Firebase authentication
- `GET /user` - Get current user information

### Forecasting

- `POST /forecast` - Generate forecast with user data and parameters
- `GET /forecast` - Get latest forecast for current user
- `POST /holiday-promotion` - Update holiday and promotion data

### Data Management

- `POST /upload` - Upload Excel file with sales history
- `GET /download-template` - Download Excel template
- `GET /template-url` - Get template download URL
- `GET /historical-data` - Get historical sales data

### System

- `GET /health` - Health check endpoint

## Deployment to Google Cloud Run

### Using the Deployment Script

1. **Make sure you have the Google Cloud SDK installed and configured**

2. **Run the deployment script:**

   ```powershell
   ./deploy_to_gcp.ps1
   ```

### Manual Deployment

1. **Build the Docker image:**

   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

2. **Deploy to Cloud Run:**

   ```bash
   gcloud run deploy sales-prediction-api \
     --image gcr.io/YOUR-PROJECT-ID/sales-prediction-api \
     --platform managed \
     --region asia-south1 \
     --allow-unauthenticated \
     --memory 1Gi \
     --port 8080 \
     --cpu 1 \
     --timeout 3600
   ```

## Model Constraints

The TFT model used in this API has the following constraints:

- **max_encoder_length=30**: The model uses 30 days of historical data as input
- **max_prediction_length=7**: The model can only predict up to 7 days into the future
- **Forecast features**: holiday status (is_holiday) and promotion status (onpromotion)

## File Structure

- `app_minimal.py` - Main FastAPI application
- `requirements_minimal.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `cloudbuild.yaml` - Google Cloud Build configuration
- `deploy_to_gcp.ps1` - Deployment script
- `firebase-key.json` - Firebase credentials (not included in repo)
- `tft_model_cpu.onnx` - ONNX model file (not included in repo)

## License

[Add your license information here]
