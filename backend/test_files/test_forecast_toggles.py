#!/usr/bin/env python3
"""
Test script to verify that the forecast toggles are working properly.
These toggles include the ability to:
1. Toggle between 7-day and single-day forecasts
2. Toggle saving of forecasts to Firestore
3. Toggle the use of real historical data vs. sample data
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

def test_forecast_days_toggle():
    """Test toggling between 7-day and single-day forecasts"""
    
    # Load the Firebase ID token
    id_token = load_id_token()
    if not id_token:
        print("Cannot test forecast toggles without a token.")
        return
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing forecast days toggle...")
    
    # Test data
    base_data = {
        "history_data": [100, 110, 120, 130, 140, 150, 160],
        "is_holiday": [0, 0, 0, 0, 0, 0, 0],
        "onpromotion": [0, 0, 0, 0, 0, 0, 0]
    }
    
    # Test case 1: 7-day forecast
    print("\nTest case 1: 7-day forecast")
    data_7day = base_data.copy()
    data_7day["forecast_days"] = 7
    
    try:
        response = requests.post(f"{BASE_URL}/forecast", headers=headers, json=data_7day)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            forecast = result.get('forecast', {})
            if forecast and 'p50' in forecast:
                p50 = forecast['p50']
                print(f"7-day forecast length: {len(p50)}")
                print(f"P50 values: {p50}")
                
                if len(p50) == 7:
                    print("✓ 7-day forecast returned correct number of days")
                else:
                    print(f"✗ 7-day forecast returned {len(p50)} days instead of 7")
                    
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing 7-day forecast: {e}")
    
    # Test case 2: 1-day forecast
    print("\nTest case 2: 1-day forecast")
    data_1day = base_data.copy()
    data_1day["forecast_days"] = 1
    
    try:
        response = requests.post(f"{BASE_URL}/forecast", headers=headers, json=data_1day)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            forecast = result.get('forecast', {})
            if forecast and 'p50' in forecast:
                p50 = forecast['p50']
                print(f"1-day forecast length: {len(p50)}")
                print(f"P50 values: {p50}")
                
                if len(p50) == 1:
                    print("✓ 1-day forecast returned correct number of days")
                else:
                    print(f"✗ 1-day forecast returned {len(p50)} days instead of 1")
                    
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing 1-day forecast: {e}")

def test_save_toggle():
    """Test toggling whether forecasts are saved to Firestore"""
    
    # Load the Firebase ID token
    id_token = load_id_token()
    if not id_token:
        print("Cannot test save toggle without a token.")
        return
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    print("\nTesting save toggle...")
    
    # Test data
    base_data = {
        "forecast_days": 7,
        "history_data": [100, 110, 120, 130, 140, 150, 160],
        "is_holiday": [0, 0, 0, 0, 0, 0, 0],
        "onpromotion": [0, 0, 0, 0, 0, 0, 0]
    }
    
    # Test case 1: Save forecast (default behavior)
    print("\nTest case 1: Save forecast (default)")
    data_save = base_data.copy()
    # No save_forecast parameter means it will use the default (True)
    
    try:
        response = requests.post(f"{BASE_URL}/forecast", headers=headers, json=data_save)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if prediction_id is present (indicates it was saved)
            prediction_id = result.get('prediction_id')
            if prediction_id:
                print(f"✓ Forecast saved with prediction_id: {prediction_id}")
            else:
                print("✗ No prediction_id in response, forecast may not have been saved")
                
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing save forecast: {e}")
    
    # Test case 2: Don't save forecast
    print("\nTest case 2: Don't save forecast")
    data_no_save = base_data.copy()
    data_no_save["save_forecast"] = False
    
    try:
        response = requests.post(f"{BASE_URL}/forecast", headers=headers, json=data_no_save)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if prediction_id is present
            prediction_id = result.get('prediction_id')
            if prediction_id:
                print(f"✗ Forecast saved despite save_forecast=False: {prediction_id}")
            else:
                print("✓ No prediction_id in response, forecast was not saved as requested")
                
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing no save forecast: {e}")

def test_real_data_toggle():
    """Test toggling between real historical data and sample data"""
    
    # Load the Firebase ID token
    id_token = load_id_token()
    if not id_token:
        print("Cannot test real data toggle without a token.")
        return
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    print("\nTesting real data toggle...")
    
    # Test case 1: Use real data (default behavior)
    print("\nTest case 1: Use real data (default)")
    
    data_real = {
        "forecast_days": 7,
        "history_data": [100, 110, 120, 130, 140, 150, 160],
        "is_holiday": [0, 0, 0, 0, 0, 0, 0],
        "onpromotion": [0, 0, 0, 0, 0, 0, 0]
        # No use_real_data parameter means it will use the default (True)
    }
    
    try:
        response = requests.post(f"{BASE_URL}/forecast", headers=headers, json=data_real)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if used_real_data flag is present and true
            used_real = result.get('used_real_data')
            if used_real is True:
                print("✓ API used real data as expected")
            elif used_real is False:
                print("✗ API did not use real data despite default setting")
            else:
                print("? Could not determine if real data was used")
                
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing real data: {e}")
    
    # Test case 2: Don't use real data
    print("\nTest case 2: Don't use real data")
    
    data_sample = {
        "forecast_days": 7,
        "history_data": [100, 110, 120, 130, 140, 150, 160],
        "is_holiday": [0, 0, 0, 0, 0, 0, 0],
        "onpromotion": [0, 0, 0, 0, 0, 0, 0],
        "use_real_data": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/forecast", headers=headers, json=data_sample)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if used_real_data flag is present and false
            used_real = result.get('used_real_data')
            if used_real is False:
                print("✓ API did not use real data as requested")
            elif used_real is True:
                print("✗ API used real data despite being told not to")
            else:
                print("? Could not determine if real data was used")
                
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing sample data: {e}")

def test_all_toggles_combined():
    """Test multiple toggles combined"""
    
    # Load the Firebase ID token
    id_token = load_id_token()
    if not id_token:
        print("Cannot test combined toggles without a token.")
        return
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    print("\nTesting all toggles combined...")
    
    # Test case: Single-day forecast, no save, no real data
    print("\nTest case: Single-day forecast, no save, no real data")
    
    data_combined = {
        "forecast_days": 1,
        "history_data": [100, 110, 120, 130, 140, 150, 160],
        "is_holiday": [0, 0, 0, 0, 0, 0, 0],
        "onpromotion": [0, 0, 0, 0, 0, 0, 0],
        "save_forecast": False,
        "use_real_data": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/forecast", headers=headers, json=data_combined)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check forecast length
            forecast = result.get('forecast', {})
            if forecast and 'p50' in forecast:
                p50 = forecast['p50']
                if len(p50) == 1:
                    print("✓ Single-day forecast returned correct number of days")
                else:
                    print(f"✗ Single-day forecast returned {len(p50)} days instead of 1")
            
            # Check if prediction_id is absent (not saved)
            prediction_id = result.get('prediction_id')
            if prediction_id:
                print(f"✗ Forecast was saved despite save_forecast=False: {prediction_id}")
            else:
                print("✓ Forecast was not saved as requested")
            
            # Check if real data was not used
            used_real = result.get('used_real_data')
            if used_real is False:
                print("✓ Real data was not used as requested")
            elif used_real is True:
                print("✗ Real data was used despite being told not to")
            else:
                print("? Could not determine if real data was used")
                
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing combined toggles: {e}")

if __name__ == "__main__":
    print("Testing forecast toggles...")
    
    test_forecast_days_toggle()
    print("\n" + "-"*50)
    
    test_save_toggle()
    print("\n" + "-"*50)
    
    test_real_data_toggle()
    print("\n" + "-"*50)
    
    test_all_toggles_combined()
