"""
Test script for the mobile app workflow.
This script simulates the API calls that would be made by the mobile app.
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

def simulate_mobile_login():
    """Simulate the login flow for mobile app"""
    print("Simulating mobile app login...")
    
    # Load ID token (in a real app this would be obtained from Firebase Auth)
    id_token = load_id_token()
    if not id_token:
        print("Login failed - no token available")
        return None
        
    # Test the token by calling the auth-test endpoint
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/auth-test", headers=headers)
        
        if response.status_code == 200:
            print("Login successful")
            return id_token
        else:
            print(f"Login failed - invalid token: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error during login: {e}")
        return None

def simulate_mobile_forecast(token):
    """Simulate the mobile app requesting a forecast"""
    print("\nSimulating mobile app forecast request...")
    
    if not token:
        print("Cannot request forecast - not logged in")
        return
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Generate sample data - in mobile app this would come from user input
    # or be loaded from previous entries
    
    # Simple upward trend with weekend patterns
    history_data = []
    base = 1000
    for i in range(28):
        # Add weekend pattern (higher on weekends)
        day_of_week = i % 7
        weekend_factor = 1.2 if day_of_week >= 5 else 1.0
        
        # Add slight upward trend
        trend_factor = 1.0 + (i * 0.01)
        
        # Add some randomness
        random_factor = random.uniform(0.95, 1.05)
        
        value = base * weekend_factor * trend_factor * random_factor
        history_data.append(round(value, 2))
    
    # Generate holiday and promotion flags
    is_holiday = [0] * 28
    onpromotion = [0] * 28
    
    # Mark some random days as holidays or promotions
    for i in range(28):
        if random.random() < 0.1:  # 10% chance for holiday
            is_holiday[i] = 1
        if random.random() < 0.15:  # 15% chance for promotion
            onpromotion[i] = 1
    
    # Future holiday and promotion flags
    # In mobile app, users might set these manually
    future_holidays = [0, 0, 0, 0, 1, 0, 0]  # Holiday on day 5
    future_promotions = [0, 1, 1, 0, 0, 0, 0]  # Promotions on days 2-3
    
    forecast_data = {
        "forecast_days": 7,
        "history_data": history_data,
        "is_holiday": is_holiday,
        "onpromotion": onpromotion,
        "future_is_holiday": future_holidays,
        "future_onpromotion": future_promotions
    }
    
    try:
        print("Sending forecast request to API...")
        response = requests.post(f"{BASE_URL}/forecast", headers=headers, json=forecast_data)
        
        if response.status_code == 200:
            result = response.json()
            
            print("Forecast received successfully")
            
            # Mobile app would display this forecast to the user
            forecast = result.get("forecast", {})
            prediction_id = result.get("prediction_id", "unknown")
            
            print(f"Prediction ID: {prediction_id}")
            
            if "p50" in forecast:
                p50 = forecast["p50"]
                p10 = forecast.get("p10", [])
                p90 = forecast.get("p90", [])
                
                print("\nForecast for next 7 days:")
                print(f"Median forecast (P50): {p50}")
                
                if p10 and p90:
                    print(f"Low forecast (P10): {p10}")
                    print(f"High forecast (P90): {p90}")
                
                # Calculate total forecast
                total = sum(p50)
                print(f"\nTotal forecasted sales: {total:.2f}")
                
                # Check impact of holidays and promotions
                if future_holidays[4] == 1:  # Holiday on day 5
                    relative_to_prev = p50[4] / p50[3] if p50[3] > 0 else 0
                    print(f"Holiday impact on day 5: {relative_to_prev:.2f}x compared to previous day")
                
                if future_promotions[1] == 1 and future_promotions[2] == 1:  # Promotions on days 2-3
                    promo_avg = (p50[1] + p50[2]) / 2
                    non_promo_avg = (p50[0] + p50[3]) / 2 if p50[0] > 0 and p50[3] > 0 else 0
                    if non_promo_avg > 0:
                        print(f"Promotion impact on days 2-3: {promo_avg/non_promo_avg:.2f}x compared to non-promotion days")
            else:
                print("No forecast data in response")
                
            return prediction_id
            
        else:
            print(f"Forecast request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error requesting forecast: {e}")
        return None

def simulate_mobile_update_forecast(token, previous_prediction_id):
    """Simulate the mobile app updating a previous forecast"""
    print("\nSimulating mobile app forecast update...")
    
    if not token:
        print("Cannot update forecast - not logged in")
        return
        
    if not previous_prediction_id:
        print("Cannot update forecast - no previous prediction ID")
        return
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # In a real mobile app, this data would be loaded from the previous forecast
    # and modified by the user
    history_data = []
    base = 1000
    for i in range(28):
        # Similar to before but with slightly different pattern
        day_of_week = i % 7
        weekend_factor = 1.3 if day_of_week >= 5 else 1.0  # Stronger weekend effect
        trend_factor = 1.0 + (i * 0.015)  # Stronger upward trend
        random_factor = random.uniform(0.97, 1.03)
        
        value = base * weekend_factor * trend_factor * random_factor
        history_data.append(round(value, 2))
    
    # Generate holiday and promotion flags
    is_holiday = [0] * 28
    onpromotion = [0] * 28
    
    # Mark some specific days as holidays or promotions
    for i in range(28):
        if i % 7 == 6:  # Every Sunday is a holiday
            is_holiday[i] = 1
        if i % 14 < 3:  # First 3 days of every two weeks have promotions
            onpromotion[i] = 1
    
    # Future flags - user has updated these
    future_holidays = [0, 0, 1, 1, 0, 0, 0]  # Holidays on days 3-4
    future_promotions = [1, 1, 0, 0, 0, 1, 1]  # Promotions on days 1-2 and 6-7
    
    forecast_data = {
        "forecast_days": 7,
        "history_data": history_data,
        "is_holiday": is_holiday,
        "onpromotion": onpromotion,
        "future_is_holiday": future_holidays,
        "future_onpromotion": future_promotions,
        "previous_prediction_id": previous_prediction_id  # Reference to previous prediction
    }
    
    try:
        print("Sending updated forecast request to API...")
        response = requests.post(f"{BASE_URL}/forecast", headers=headers, json=forecast_data)
        
        if response.status_code == 200:
            result = response.json()
            
            print("Updated forecast received successfully")
            
            # Mobile app would display this forecast to the user
            forecast = result.get("forecast", {})
            new_prediction_id = result.get("prediction_id", "unknown")
            
            print(f"New prediction ID: {new_prediction_id}")
            
            if "p50" in forecast:
                p50 = forecast["p50"]
                
                print("\nUpdated forecast for next 7 days:")
                print(f"Median forecast (P50): {p50}")
                
                # Calculate total forecast
                total = sum(p50)
                print(f"\nTotal forecasted sales: {total:.2f}")
                
                # Check holiday impact
                holiday_days = [p50[2], p50[3]]
                non_holiday_days = [p50[0], p50[1], p50[4], p50[5], p50[6]]
                
                holiday_avg = sum(holiday_days) / len(holiday_days)
                non_holiday_avg = sum(non_holiday_days) / len(non_holiday_days)
                
                print(f"Holiday impact: {holiday_avg/non_holiday_avg:.2f}x compared to non-holiday days")
            else:
                print("No forecast data in response")
                
            return new_prediction_id
            
        else:
            print(f"Forecast update failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error updating forecast: {e}")
        return None

def simulate_mobile_offline_scenario():
    """Simulate the mobile app handling offline scenario"""
    print("\nSimulating mobile app offline scenario...")
    
    print("In a real mobile app, offline functionality would:")
    print("1. Cache the most recent forecast locally")
    print("2. Store pending requests to be sent when online")
    print("3. Use local data for temporary forecasting if possible")
    
    # This is a simulation - in a real app we would implement the above
    
    # Example of cached data that would be stored locally
    cached_forecast = {
        "p50": [1105.23, 1132.45, 1097.18, 1203.56, 1187.92, 1299.45, 1325.78],
        "p10": [987.34, 1002.56, 978.45, 1078.23, 1043.67, 1145.78, 1167.34],
        "p90": [1223.45, 1262.34, 1215.89, 1328.67, 1332.18, 1453.23, 1484.12]
    }
    
    print("\nUsing cached forecast data:")
    print(f"Median forecast (P50): {cached_forecast['p50']}")
    
    # Simulate reconnection
    print("\nReconnecting to network...")
    time.sleep(1)  # Simulate reconnection delay
    
    # In a real app, we would now sync with the server
    print("Syncing pending requests with server...")
    
    return True

def simulate_mobile_app_workflow():
    """Run a complete mobile app workflow simulation"""
    print("Starting mobile app workflow simulation...")
    print("-" * 50)
    
    # Step 1: Login
    token = simulate_mobile_login()
    if not token:
        return
        
    # Step 2: Get initial forecast
    prediction_id = simulate_mobile_forecast(token)
    if not prediction_id:
        return
        
    # Step 3: Wait a bit (simulating user interaction)
    print("\nUser reviewing forecast...")
    time.sleep(2)
    
    # Step 4: Update forecast with new parameters
    new_prediction_id = simulate_mobile_update_forecast(token, prediction_id)
    if not new_prediction_id:
        return
        
    # Step 5: Simulate offline scenario
    simulate_mobile_offline_scenario()
    
    print("\nMobile app workflow simulation completed successfully")

if __name__ == "__main__":
    print("Testing mobile app workflow with the sales prediction API...")
    simulate_mobile_app_workflow()
