#!/usr/bin/env pwsh
# Run the FastAPI app locally for testing

# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found. Please install Python 3.8 or later."
    exit 1
}

# Check if required files exist
if (-not (Test-Path "app_minimal.py")) {
    Write-Error "app_minimal.py not found."
    exit 1
}

if (-not (Test-Path "requirements_minimal.txt")) {
    Write-Error "requirements_minimal.txt not found."
    exit 1
}

# Create uploads directory if it doesn't exist
if (-not (Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" -Force | Out-Null
    Write-Output "Created uploads directory"
}

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Output "Creating virtual environment..."
    python -m venv .venv
    
    if (-not $?) {
        Write-Error "Failed to create virtual environment."
        exit 1
    }
}

# Activate virtual environment
Write-Output "Activating virtual environment..."
if ($IsWindows) {
    & .\.venv\Scripts\Activate.ps1
} else {
    & ./.venv/bin/Activate.ps1
}

# Install dependencies
Write-Output "Installing dependencies..."
pip install -r requirements_minimal.txt
pip install uvicorn

# Run the app
Write-Output "Starting the FastAPI app..."
uvicorn app_minimal:app --reload --host 0.0.0.0 --port 8000
