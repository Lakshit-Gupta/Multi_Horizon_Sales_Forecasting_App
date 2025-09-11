# Deployment script for Sales Prediction API (Source-based deployment)
$PROJECT_ID = (gcloud config get-value project)
$REGION = "asia-south1"
$SERVICE_NAME = "sales-prediction-api-minimal"

Write-Output "Deploying Sales Prediction API to Google Cloud Run using source-based deployment..."
Write-Output "Project ID: $PROJECT_ID"
Write-Output "Region: $REGION"
Write-Output "Service name: $SERVICE_NAME"

# Check for required files
$requiredFiles = @("app_minimal.py", "requirements_minimal.txt", "Dockerfile", "cloudbuild.yaml")
$missingFiles = $requiredFiles | Where-Object { -not (Test-Path $_) }

if ($missingFiles.Count -gt 0) {
    Write-Error "Missing required files: $($missingFiles -join ', ')"
    exit 1
}

# Check for model file
if (-not (Test-Path "tft_model_cpu.onnx")) {
    Write-Warning "ONNX model file not found. The API will use mock predictions."
    
    $response = Read-Host "Do you want to continue without the ONNX model? (y/n)"
    if ($response.ToLower() -ne "y") {
        Write-Output "Deployment canceled."
        exit 0
    }
}

# Check for Firebase key
if (-not (Test-Path "firebase-key.json")) {
    Write-Warning "Firebase key file not found. Please make sure you have firebase-key.json in the current directory."
    
    if (Test-Path "firebase-key.json.example") {
        Write-Output "A template file 'firebase-key.json.example' was found."
        Write-Output "Please rename it to 'firebase-key.json' and update it with your Firebase credentials."
    }
    
    $response = Read-Host "Do you want to continue without the Firebase key? (y/n)"
    if ($response.ToLower() -ne "y") {
        Write-Output "Deployment canceled."
        exit 0
    }
}

# Create uploads directory if it doesn't exist
if (-not (Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" -Force | Out-Null
    Write-Output "Created uploads directory"
}

# Deploy to Cloud Run using source-based deployment
Write-Output "Deploying to Cloud Run using source-based deployment..."
gcloud run deploy $SERVICE_NAME `
  --source . `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --memory 1Gi `
  --port 8000 `
  --cpu 1 `
  --timeout 300 `
  --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/workspace/firebase-key.json"

# Get the URL of the deployed service
$serviceUrl = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format="value(status.url)"
Write-Output "Service deployed to: $serviceUrl"

# Save the URL to a file for reference
$serviceUrl | Out-File -FilePath "service_url.txt"
Write-Output "Service URL saved to service_url.txt"

Write-Output "Testing service health endpoint..."
try {
    $response = Invoke-RestMethod -Uri "$serviceUrl/health" -Method Get
    Write-Output "Health check response: $($response | ConvertTo-Json -Depth 1)"
    Write-Output "Deployment successful!"
} catch {
    Write-Warning "Health check failed: $_"
    Write-Output "Service may still be starting up. Please check the logs in the Google Cloud Console."
}

Write-Output "Done!"
