"""
Test script for Firebase authentication integration with the forecast endpoint.
This script tests authenticated forecast requests using a Firebase ID token.
"""
import requests
import json
import os
import time
from datetime import datetime

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

def test_authenticated_forecast():
    """Test the forecast endpoint with authentication"""
    
    # Load the Firebase ID token
    id_token = load_id_token()
    if not id_token:
        return
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    # Sample forecast data
    forecast_data = {
        "forecast_days": 7,
        "history_data": [100, 110, 120, 130, 140, 150, 160],
        "is_holiday": [0, 0, 0, 0, 0, 0, 0],
        "onpromotion": [0, 0, 0, 0, 0, 0, 0]
    }
    
    # Test the forecast endpoint
    print("Testing authenticated forecast endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/forecast", headers=headers, json=forecast_data)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            forecast_response = response.json()
            
            # Print detailed response
            print("\nForecast Response:")
            print(f"Success: {forecast_response.get('success')}")
            print(f"User: {forecast_response.get('user')}")
            print(f"Prediction ID: {forecast_response.get('prediction_id')}")
            
            # Print forecast values
            forecast = forecast_response.get('forecast', {})
            if forecast:
                print("\nForecast Values:")
                print(f"P50: {forecast.get('p50')}")
                print(f"P10: {forecast.get('p10')}")
                print(f"P90: {forecast.get('p90')}")
                
                # Calculate average prediction
                if 'p50' in forecast and forecast['p50']:
                    avg = sum(forecast['p50']) / len(forecast['p50'])
                    print(f"\nAverage P50 prediction: {avg:.2f}")
                
            # Test if prediction was saved in Firestore
            prediction_id = forecast_response.get('prediction_id')
            if prediction_id:
                print(f"\nPrediction saved with ID: {prediction_id}")
                # Could add additional test to verify the prediction in Firestore
                
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing forecast endpoint: {e}")

def test_forecast_with_different_days():
    """Test forecasts with different forecast days"""
    
    # Load the Firebase ID token
    id_token = load_id_token()
    if not id_token:
        return
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    # Test different forecast days
    days_to_test = [1, 3, 7]  # The API supports up to 7 days forecast
    
    for days in days_to_test:
        # Sample forecast data
        forecast_data = {
            "forecast_days": days,
            "history_data": [100, 110, 120, 130, 140, 150, 160],
            "is_holiday": [0, 0, 0, 0, 0, 0, 0],
            "onpromotion": [0, 0, 0, 0, 0, 0, 0]
        }
        
        print(f"\nTesting {days}-day forecast...")
        try:
            response = requests.post(f"{BASE_URL}/forecast", headers=headers, json=forecast_data)
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                forecast_response = response.json()
                
                # Check if forecast length matches requested days
                forecast = forecast_response.get('forecast', {})
                if forecast and 'p50' in forecast:
                    actual_days = len(forecast['p50'])
                    print(f"Requested {days} days, received {actual_days} days")
                    
                    # Print forecast values
                    print(f"P50 values: {forecast.get('p50')}")
                    
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Error testing {days}-day forecast: {e}")

if __name__ == "__main__":
    print("Running authenticated forecast tests...")
    test_authenticated_forecast()
    print("\n" + "-" * 50)
    test_forecast_with_different_days()
