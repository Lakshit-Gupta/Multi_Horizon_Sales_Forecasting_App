"""
Test script for multi-day forecast functionality.
This script tests the API's ability to generate forecasts for multiple days.
"""
import requests
import json
import matplotlib.pyplot as plt
import numpy as np
import os

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

def test_multi_day_forecast():
    """Test the forecast endpoint with varying forecast days"""
    
    # Days to test (1-7 days supported by the model)
    days_to_test = [1, 3, 5, 7]
    
    # Sample history data - 28 days of increasing sales
    history_data = [100 + i*5 for i in range(28)]
    is_holiday = [0] * 28
    onpromotion = [0] * 28
    
    # Store results for each forecast length
    results = {}
    
    # Test with auth
    id_token = load_id_token()
    if id_token:
        print("Testing with authentication...")
        headers = {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json"
        }
    else:
        print("Testing without authentication (using test-forecast endpoint)...")
        headers = {"Content-Type": "application/json"}
    
    # Test each forecast length
    for days in days_to_test:
        forecast_data = {
            "forecast_days": days,
            "history_data": history_data,
            "is_holiday": is_holiday,
            "onpromotion": onpromotion
        }
        
        print(f"\nTesting {days}-day forecast...")
        
        try:
            # Determine endpoint based on auth availability
            if id_token:
                endpoint = f"{BASE_URL}/forecast"
            else:
                endpoint = f"{BASE_URL}/test-forecast"
            
            response = requests.post(endpoint, headers=headers, json=forecast_data)
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if forecast was generated
                forecast = result.get('forecast', {})
                if forecast and 'p50' in forecast:
                    p50 = forecast['p50']
                    p10 = forecast.get('p10', [])
                    p90 = forecast.get('p90', [])
                    
                    print(f"P50 forecast: {p50}")
                    
                    # Verify forecast length
                    actual_length = len(p50)
                    print(f"Requested {days} days, received {actual_length} days")
                    
                    if actual_length == days:
                        print("✓ Forecast length matches requested days")
                    else:
                        print("✗ Forecast length doesn't match requested days")
                    
                    # Store results for later visualization
                    results[days] = {
                        'p50': p50,
                        'p10': p10,
                        'p90': p90
                    }
                    
                else:
                    print("No forecast data in response")
                    print(f"Response: {result}")
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Error testing {days}-day forecast: {e}")
    
    # Return results for visualization
    return results

def test_forecast_consistency():
    """Test if the model maintains consistency between different forecast horizons"""
    
    # Generate consistent test data
    history_data = [100 + i*5 for i in range(28)]
    is_holiday = [0] * 28
    onpromotion = [0] * 28
    
    print("\nTesting forecast consistency across different horizons...")
    
    # Make two requests: one for 7 days and one for 3 days
    forecast_data_7days = {
        "forecast_days": 7,
        "history_data": history_data,
        "is_holiday": is_holiday,
        "onpromotion": onpromotion
    }
    
    forecast_data_3days = {
        "forecast_days": 3,
        "history_data": history_data,
        "is_holiday": is_holiday,
        "onpromotion": onpromotion
    }
    
    try:
        # Use test-forecast endpoint (no auth required)
        response_7days = requests.post(f"{BASE_URL}/test-forecast", json=forecast_data_7days)
        response_3days = requests.post(f"{BASE_URL}/test-forecast", json=forecast_data_3days)
        
        if response_7days.status_code == 200 and response_3days.status_code == 200:
            result_7days = response_7days.json()
            result_3days = response_3days.json()
            
            forecast_7days = result_7days.get('forecast', {}).get('p50', [])
            forecast_3days = result_3days.get('forecast', {}).get('p50', [])
            
            # Check if first 3 days of 7-day forecast match the 3-day forecast
            if len(forecast_7days) >= 3 and len(forecast_3days) == 3:
                first_3_of_7day = forecast_7days[:3]
                
                print("\nComparing forecasts:")
                print(f"First 3 days of 7-day forecast: {first_3_of_7day}")
                print(f"3-day forecast: {forecast_3days}")
                
                # Check if forecasts are exactly the same
                if first_3_of_7day == forecast_3days:
                    print("✓ Forecasts are identical - perfect consistency")
                else:
                    # Calculate differences
                    diffs = [abs(a - b) for a, b in zip(first_3_of_7day, forecast_3days)]
                    avg_diff = sum(diffs) / len(diffs)
                    max_diff = max(diffs)
                    
                    print(f"Differences: {diffs}")
                    print(f"Average difference: {avg_diff:.2f}")
                    print(f"Maximum difference: {max_diff:.2f}")
                    
                    # Calculate relative difference
                    avg_val = sum(forecast_3days) / len(forecast_3days)
                    rel_diff = (avg_diff / avg_val) * 100
                    
                    print(f"Relative difference: {rel_diff:.2f}%")
                    
                    if rel_diff < 5:
                        print("✓ Forecasts are consistent (relative difference < 5%)")
                    else:
                        print("✗ Forecasts show inconsistency")
            else:
                print("Could not compare forecasts - insufficient data")
        else:
            print(f"Error getting forecasts - status codes: {response_7days.status_code}, {response_3days.status_code}")
            
    except Exception as e:
        print(f"Error testing forecast consistency: {e}")

def visualize_forecasts(results):
    """Visualize the forecasts for different horizons"""
    try:
        if not results:
            print("No forecast results to visualize")
            return
            
        plt.figure(figsize=(12, 8))
        
        # Plot each forecast length
        for days, forecast in results.items():
            p50 = forecast['p50']
            p10 = forecast.get('p10', [])
            p90 = forecast.get('p90', [])
            
            x = list(range(1, len(p50) + 1))
            plt.plot(x, p50, marker='o', label=f"{days}-day forecast")
            
            # If we have p10 and p90, show the confidence interval
            if p10 and p90 and len(p10) == len(p50) and len(p90) == len(p50):
                plt.fill_between(x, p10, p90, alpha=0.2)
        
        # Add labels and title
        plt.title("Multi-Day Sales Forecasts")
        plt.xlabel("Days")
        plt.ylabel("Sales")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # Save the figure
        plt.savefig("multi_day_forecasts.png")
        print("\nForecast visualization saved to 'multi_day_forecasts.png'")
        
    except Exception as e:
        print(f"Error visualizing forecasts: {e}")

if __name__ == "__main__":
    print("Testing multi-day forecasts...")
    forecast_results = test_multi_day_forecast()
    
    print("\n" + "-"*50)
    test_forecast_consistency()
    
    # Visualize if matplotlib is available
    try:
        visualize_forecasts(forecast_results)
    except Exception as e:
        print(f"\nVisualization failed: {e}")
        print("You may need to install matplotlib with 'pip install matplotlib'")
