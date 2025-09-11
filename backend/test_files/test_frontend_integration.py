"""
Test script for frontend integration with the sales prediction API.
This script simulates frontend calls to the API endpoints.
"""
import requests
import json
import os
import time
import random
from datetime import datetime, timedelta

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

def get_headers(token=None):
    """Get headers for API requests"""
    headers = {
        "Content-Type": "application/json"
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    return headers

def test_public_endpoints():
    """Test public endpoints that don't require authentication"""
    
    endpoints = [
        "/health",
        "/docs",
    ]
    
    print("Testing public endpoints...")
    
    for endpoint in endpoints:
        try:
            print(f"\nTesting {endpoint}...")
            response = requests.get(f"{BASE_URL}{endpoint}")
            
            print(f"Status code: {response.status_code}")
            
            if endpoint == "/health" and response.status_code == 200:
                try:
                    print(f"Response: {response.json()}")
                except:
                    print("Response is not JSON")
                    
        except Exception as e:
            print(f"Error testing {endpoint}: {e}")
            
    # Test the test-forecast endpoint (no auth required)
    print("\nTesting /test-forecast endpoint...")
    
    forecast_data = {
        "forecast_days": 7,
        "history_data": [100, 110, 120, 130, 140, 150, 160],
        "is_holiday": [0, 0, 0, 0, 0, 0, 0],
        "onpromotion": [0, 0, 0, 0, 0, 0, 0]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/test-forecast", 
                                json=forecast_data,
                                headers=get_headers())
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Successfully received forecast")
            
            # Check if response contains expected fields
            if "forecast" in result and "p50" in result["forecast"]:
                print(f"P50 forecast: {result['forecast']['p50']}")
                
    except Exception as e:
        print(f"Error testing /test-forecast: {e}")

def test_authenticated_endpoints():
    """Test endpoints that require authentication"""
    
    # Load the Firebase ID token
    id_token = load_id_token()
    if not id_token:
        print("Cannot test authenticated endpoints without a token.")
        return
    
    # Get headers with token
    headers = get_headers(id_token)
    
    # Test the authenticated endpoints
    endpoints = [
        "/auth-test",
        "/user",
    ]
    
    print("\nTesting authenticated endpoints...")
    
    for endpoint in endpoints:
        try:
            print(f"\nTesting {endpoint}...")
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"Response: {response.json()}")
                
        except Exception as e:
            print(f"Error testing {endpoint}: {e}")
    
    # Test the authenticated forecast endpoint
    print("\nTesting authenticated /forecast endpoint...")
    
    forecast_data = {
        "forecast_days": 7,
        "history_data": [100, 110, 120, 130, 140, 150, 160],
        "is_holiday": [0, 0, 0, 0, 0, 0, 0],
        "onpromotion": [0, 0, 0, 0, 0, 0, 0]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/forecast", 
                                json=forecast_data,
                                headers=headers)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Successfully received forecast")
            
            # Check if response contains expected fields
            if "forecast" in result and "prediction_id" in result:
                print(f"Prediction ID: {result['prediction_id']}")
                print(f"P50 forecast: {result['forecast']['p50']}")
                
    except Exception as e:
        print(f"Error testing /forecast: {e}")

def test_frontend_workflow():
    """Test a complete frontend workflow"""
    
    # Load the Firebase ID token
    id_token = load_id_token()
    if not id_token:
        print("Cannot test frontend workflow without a token.")
        return
    
    # Get headers with token
    headers = get_headers(id_token)
    
    print("\nTesting complete frontend workflow...")
    
    # Step 1: Check if user is authenticated
    print("\nStep 1: Check authentication...")
    try:
        response = requests.get(f"{BASE_URL}/user", headers=headers)
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"User authenticated: {user_info}")
        else:
            print(f"Authentication failed: {response.status_code}")
            return
    except Exception as e:
        print(f"Error checking authentication: {e}")
        return
    
    # Step 2: Generate a forecast
    print("\nStep 2: Generate a forecast...")
    
    # Generate some realistic sales data
    base_sales = 1000
    # Add trend, weekly seasonality and noise
    history_days = 28
    history_data = []
    is_holiday = [0] * history_days
    onpromotion = [0] * history_days
    
    for i in range(history_days):
        trend = i * 5  # Upward trend
        weekly = 100 * (1 if i % 7 in [5, 6] else 0)  # Weekend uplift
        noise = random.normalvariate(0, 30)  # Random noise
        
        # Mark some random days as holidays
        if random.random() < 0.1:  # 10% chance of being a holiday
            is_holiday[i] = 1
        
        # Mark some random days as promotions
        if random.random() < 0.15:  # 15% chance of having a promotion
            onpromotion[i] = 1
            
        sales = max(0, base_sales + trend + weekly + noise)
        history_data.append(round(sales, 2))
    
    forecast_data = {
        "forecast_days": 7,
        "history_data": history_data,
        "is_holiday": is_holiday,
        "onpromotion": onpromotion
    }
    
    try:
        response = requests.post(f"{BASE_URL}/forecast", 
                                json=forecast_data,
                                headers=headers)
        
        if response.status_code == 200:
            forecast_result = response.json()
            print("Forecast generated successfully")
            
            prediction_id = forecast_result.get('prediction_id')
            print(f"Prediction ID: {prediction_id}")
            
            # Extract forecast data
            forecast = forecast_result.get('forecast', {})
            if forecast and 'p50' in forecast:
                p50 = forecast['p50']
                print(f"Forecast (next 7 days): {p50}")
                
                # Calculate percent change from last historical value
                if history_data and p50:
                    last_history = history_data[-1]
                    first_forecast = p50[0]
                    percent_change = ((first_forecast - last_history) / last_history) * 100
                    print(f"Day 1 forecast vs last history: {percent_change:.2f}%")
            else:
                print("No forecast data in response")
                
        else:
            print(f"Forecast generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"Error generating forecast: {e}")
        return
    
    # Step 3: Simulate viewing forecast history
    # In a real frontend, this would be done via Firebase directly
    print("\nStep 3: Simulating viewing forecast history...")
    print("In a real frontend, forecast history would be fetched from Firebase directly")
    print(f"Most recent prediction ID: {prediction_id}")
    
    # Step 4: Generate a new forecast with different parameters
    print("\nStep 4: Generate a new forecast with different parameters...")
    
    # Modify some of the history data to simulate a change
    modified_history = history_data.copy()
    # Add a 20% boost to the last few days
    for i in range(-5, 0):
        modified_history[i] = modified_history[i] * 1.2
    
    # Add some holidays for the forecast period
    forecast_holidays = [0, 0, 1, 0, 0, 0, 0]  # Holiday on day 3
    forecast_promotions = [0, 0, 0, 1, 1, 0, 0]  # Promotions on days 4-5
    
    new_forecast_data = {
        "forecast_days": 7,
        "history_data": modified_history,
        "is_holiday": is_holiday,
        "onpromotion": onpromotion,
        "future_is_holiday": forecast_holidays,
        "future_onpromotion": forecast_promotions
    }
    
    try:
        response = requests.post(f"{BASE_URL}/forecast", 
                                json=new_forecast_data,
                                headers=headers)
        
        if response.status_code == 200:
            new_forecast = response.json()
            print("New forecast generated successfully")
            
            new_prediction_id = new_forecast.get('prediction_id')
            print(f"New prediction ID: {new_prediction_id}")
            
            # Extract forecast data
            forecast = new_forecast.get('forecast', {})
            if forecast and 'p50' in forecast:
                p50 = forecast['p50']
                print(f"New forecast (next 7 days): {p50}")
                
                # Look for impact of holiday and promotions
                holiday_impact = "Higher" if p50[2] > p50[1] else "Lower"
                print(f"Holiday impact on day 3: {holiday_impact} sales")
                
                promo_impact = "Higher" if (p50[3] + p50[4])/2 > (p50[1] + p50[2])/2 else "Lower"
                print(f"Promotion impact on days 4-5: {promo_impact} sales")
        else:
            print(f"New forecast generation failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error generating new forecast: {e}")

if __name__ == "__main__":
    print("Testing frontend integration with the sales prediction API...")
    
    test_public_endpoints()
    print("\n" + "-"*50)
    
    test_authenticated_endpoints()
    print("\n" + "-"*50)
    
    test_frontend_workflow()
