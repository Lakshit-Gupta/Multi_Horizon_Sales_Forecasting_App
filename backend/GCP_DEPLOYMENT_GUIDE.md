# Google Cloud Deployment Guide

This document provides detailed instructions for deploying the Sales Prediction API to Google Cloud Run.

## Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured
- Docker installed (for local testing)
- Python 3.10 or later
- Firebase project with service account key
- ONNX model file (tft_model_cpu.onnx)

## Step 1: Initial Setup

### Configure Google Cloud SDK

Make sure your Google Cloud SDK is configured with the correct project:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Enable Required APIs

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

## Step 2: Prepare Your Application

1. **Clone the repository (if using version control):**

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Make sure you have the following files in your project directory:**

   - `app_minimal.py`: The main FastAPI application
   - `requirements_minimal.txt`: Python dependencies
   - `Dockerfile`: Docker configuration
   - `cloudbuild.yaml`: Google Cloud Build configuration
   - `firebase-key.json`: Firebase service account key
   - `tft_model_cpu.onnx`: ONNX model file

3. **Verify your Dockerfile:**

   The Dockerfile should look similar to this:

   ```dockerfile
   FROM python:3.10-slim

   WORKDIR /app

   COPY requirements_minimal.txt .
   COPY app_minimal.py .
   COPY tft_model_cpu.onnx .
   COPY firebase-key.json .

   RUN pip install --no-cache-dir -r requirements_minimal.txt

   EXPOSE 8080

   CMD ["uvicorn", "app_minimal:app", "--host", "0.0.0.0", "--port", "8080"]
   ```

## Step 3: Local Testing (Optional)

Before deploying to Google Cloud, you can test your application locally:

1. **Build the Docker image:**

   ```bash
   docker build -t sales-prediction-api .
   ```

2. **Run the container locally:**

   ```bash
   docker run -p 8080:8080 sales-prediction-api
   ```

3. **Test the application:**

   Open a web browser and go to http://localhost:8080/health to verify the application is running.

## Step 4: Deployment to Google Cloud Run

### Option 1: Using the Deployment Script

Simply run the deployment script:

```powershell
./deploy_to_gcp.ps1
```

The script will:
1. Check for required files
2. Build the container image using Cloud Build
3. Deploy the image to Cloud Run
4. Test the health endpoint
5. Save the service URL to a file

### Option 2: Manual Deployment

1. **Build the container image using Cloud Build:**

   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

   This will build the container and push it to Google Container Registry (GCR).

2. **Deploy the image to Cloud Run:**

   ```bash
   gcloud run deploy sales-prediction-api \
     --image gcr.io/YOUR_PROJECT_ID/sales-prediction-api \
     --platform managed \
     --region asia-south1 \
     --allow-unauthenticated \
     --memory 1Gi \
     --port 8080 \
     --cpu 1 \
     --timeout 3600
   ```

   Adjust parameters as needed:
   - `--region`: Choose a region close to your users
   - `--memory`: Increase if needed for model inference
   - `--cpu`: CPU allocation for your service
   - `--timeout`: Request timeout in seconds
   - `--no-allow-unauthenticated`: Add this flag if you want to restrict access

3. **Get the service URL:**

   ```bash
   gcloud run services describe sales-prediction-api \
     --platform managed \
     --region asia-south1 \
     --format="value(status.url)"
   ```

## Step 5: Verify the Deployment

1. **Check the health endpoint:**

   ```bash
   curl <SERVICE_URL>/health
   ```

   You should see a response like:
   ```json
   {"status":"healthy","timestamp":"2025-08-15T15:30:00.000000"}
   ```

2. **Test the authentication endpoint:**

   ```bash
   curl <SERVICE_URL>/auth-test -H "Authorization: Bearer <FIREBASE_ID_TOKEN>"
   ```

## Step 6: Set Up Custom Domain (Optional)

To use a custom domain with your Cloud Run service:

1. **Add your domain to Cloud Run:**

   ```bash
   gcloud beta run domain-mappings create \
     --service sales-prediction-api \
     --domain api.yourdomain.com \
     --platform managed \
     --region asia-south1
   ```

2. **Update your DNS records** with the verification records and CNAME entries provided by Google Cloud.

## Step 7: Monitoring and Logging

### View Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sales-prediction-api" --limit=50
```

### Set Up Alerts

Consider setting up Cloud Monitoring alerts for:
- Error rates
- Response latency
- Instance count

## Continuous Deployment (Optional)

For continuous deployment, you can:

1. **Set up Cloud Build triggers** connected to your source repository

2. **Create a cloudbuild.yaml file** that includes both build and deploy steps:

   ```yaml
   steps:
     - name: 'gcr.io/cloud-builders/docker'
       args: ['build', '-t', 'gcr.io/$PROJECT_ID/sales-prediction-api', '.']
     - name: 'gcr.io/cloud-builders/docker'
       args: ['push', 'gcr.io/$PROJECT_ID/sales-prediction-api']
     - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
       entrypoint: 'gcloud'
       args: [
         'run', 'deploy', 'sales-prediction-api',
         '--image', 'gcr.io/$PROJECT_ID/sales-prediction-api',
         '--platform', 'managed',
         '--region', 'asia-south1',
         '--allow-unauthenticated'
       ]
   ```

## Troubleshooting

### Common Issues

1. **ONNX model loading errors**:
   - Make sure the model file is included in the container
   - Check that onnxruntime version matches the one used for model conversion

2. **Firebase authentication issues**:
   - Verify the service account key is correct and has sufficient permissions
   - Check that your Firebase project is properly set up for authentication

3. **Memory or CPU limitations**:
   - If your service is crashing, try increasing the memory allocation
   - For slow responses, consider increasing CPU allocation

4. **Container build failures**:
   - Check that all required files are present
   - Verify that your Python dependencies are compatible

5. **Request timeouts**:
   - Adjust the timeout parameter if your model inference takes longer than expected

### Getting Help

- Review logs for detailed error information
- Check the [Cloud Run documentation](https://cloud.google.com/run/docs)
- Refer to the [FastAPI documentation](https://fastapi.tiangolo.com/)
