"""
Test script for uploading forecast data through the authenticated endpoint.
This script tests the /upload-forecast endpoint for uploading Excel files with sales data.
"""
import requests
import json
import os
from datetime import datetime
import pandas as pd
import numpy as np
import io

# Base URL for the API
BASE_URL = "https://sales-prediction-api-minimal-qmp76ddexq-el.a.run.app"

def load_id_token():
    """Load Firebase ID token from file"""
    try:
        # Check if token file exists
        if not os.path.exists("firebase_id_token.txt"):
            print("Token file not found. Please run test_auth_endpoint.py first.")
            return None
            
        # Read token from file
        with open("firebase_id_token.txt", "r") as f:
            token = f.read().strip()
            
        return token
    except Exception as e:
        print(f"Error loading token: {e}")
        return None

def create_sample_excel():
    """Create a sample Excel file for testing uploads"""
    
    # Create a DataFrame with sample data
    # Format: Date | Sales | Is Holiday | On Promotion
    
    # Generate dates for the last 28 days
    today = datetime.today()
    dates = pd.date_range(end=today, periods=28).tolist()
    dates_str = [d.strftime("%Y-%m-%d") for d in dates]
    
    # Generate sample sales data with some variability
    base_sales = 100
    # Add a trend and some randomness
    sales = [base_sales + i*2 + np.random.normal(0, 10) for i in range(28)]
    sales = [max(0, round(s, 2)) for s in sales]  # Ensure no negative values
    
    # Generate holiday flags (randomly mark 3 days as holidays)
    is_holiday = [0] * 28
    holiday_indices = np.random.choice(range(28), 3, replace=False)
    for idx in holiday_indices:
        is_holiday[idx] = 1
    
    # Generate promotion flags (randomly mark 5 days as promotions)
    on_promotion = [0] * 28
    promo_indices = np.random.choice(range(28), 5, replace=False)
    for idx in promo_indices:
        on_promotion[idx] = 1
    
    # Create DataFrame
    df = pd.DataFrame({
        "Date": dates_str,
        "Sales": sales,
        "Is_Holiday": is_holiday,
        "On_Promotion": on_promotion
    })
    
    # Save to Excel file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_upload_{timestamp}.xlsx"
    df.to_excel(filename, index=False)
    
    print(f"Created sample Excel file: {filename}")
    return filename

def test_upload_forecast():
    """Test uploading forecast data"""
    
    # Load the Firebase ID token
    id_token = load_id_token()
    if not id_token:
        return
    
    # Create a sample Excel file
    excel_filename = create_sample_excel()
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {id_token}"
        # Don't set Content-Type here - it will be set by the requests library for multipart/form-data
    }
    
    # Test the upload-forecast endpoint
    print("\nTesting upload-forecast endpoint...")
    try:
        # Open the Excel file for upload
        with open(excel_filename, "rb") as file:
            files = {"file": (excel_filename, file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            
            # Send the request
            response = requests.post(f"{BASE_URL}/upload-forecast", headers=headers, files=files)
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                upload_response = response.json()
                
                # Print detailed response
                print("\nUpload Response:")
                print(f"Success: {upload_response.get('success')}")
                print(f"User: {upload_response.get('user')}")
                print(f"Filename: {upload_response.get('filename')}")
                
                # Check if forecast was generated
                forecast = upload_response.get('forecast', {})
                if forecast:
                    print("\nForecast Generated:")
                    print(f"P50 (first 3 days): {forecast.get('p50', [])[:3]}...")
                    
                    # Check forecast length
                    p50_length = len(forecast.get('p50', []))
                    print(f"Forecast length: {p50_length} days")
                    
                # Check if the file was saved
                saved_path = upload_response.get('saved_path')
                if saved_path:
                    print(f"\nFile saved at: {saved_path}")
                
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing upload-forecast endpoint: {e}")
    
    # Clean up - remove the test Excel file
    try:
        os.remove(excel_filename)
        print(f"\nRemoved test file: {excel_filename}")
    except Exception as e:
        print(f"Error removing test file: {e}")

def test_invalid_upload():
    """Test uploading invalid data formats"""
    
    # Load the Firebase ID token
    id_token = load_id_token()
    if not id_token:
        return
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {id_token}"
    }
    
    # Test cases with invalid uploads
    
    # Test case 1: Empty file
    print("\nTesting upload with empty file...")
    try:
        # Create an empty file
        empty_file = io.BytesIO()
        files = {"file": ("empty.xlsx", empty_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        
        response = requests.post(f"{BASE_URL}/upload-forecast", headers=headers, files=files)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test case 2: Wrong file format (txt instead of xlsx)
    print("\nTesting upload with wrong file format...")
    try:
        # Create a text file
        text_file = io.BytesIO(b"This is not an Excel file")
        files = {"file": ("not_excel.txt", text_file, "text/plain")}
        
        response = requests.post(f"{BASE_URL}/upload-forecast", headers=headers, files=files)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test case 3: Missing authorization
    print("\nTesting upload without authorization...")
    try:
        # Create a valid Excel file but don't send auth headers
        df = pd.DataFrame({"test": [1, 2, 3]})
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        
        files = {"file": ("test.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        
        # Send request without auth headers
        response = requests.post(f"{BASE_URL}/upload-forecast", files=files)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Running upload forecast tests...")
    test_upload_forecast()
    
    print("\n" + "-"*50)
    print("Testing invalid uploads...")
    test_invalid_upload()
