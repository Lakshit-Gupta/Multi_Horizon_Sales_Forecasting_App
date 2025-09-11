"""
Test script for forecast endpoint without authentication.
This script tests the basic functionality of the test-forecast endpoint.
"""
import requests
import json

# URL of the API endpoint
BASE_URL = "https://sales-prediction-api-minimal-qmp76ddexq-el.a.run.app"

def test_forecast():
    """Test the test-forecast endpoint (no auth required)"""
    
    # Test data
    test_data = {
        "forecast_days": 7,
        "history_data": [100, 110, 120, 130, 140, 150, 160],
        "is_holiday": [0, 0, 0, 0, 0, 0, 0],
        "onpromotion": [0, 0, 0, 0, 0, 0, 0]
    }
    
    # Send request to the endpoint
    print("Testing forecast endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/test-forecast", json=test_data)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if response contains expected fields
            if "forecast" in result and "success" in result:
                print("Response contains expected fields")
                
                # Print forecast details
                forecast = result["forecast"]
                print("\nForecast details:")
                
                # Check different percentile forecasts
                if "p50" in forecast:
                    print(f"P50 (median forecast): {forecast['p50']}")
                    
                if "p10" in forecast:
                    print(f"P10 (low forecast): {forecast['p10']}")
                    
                if "p90" in forecast:
                    print(f"P90 (high forecast): {forecast['p90']}")
                
                # Check forecast length
                p50_length = len(forecast.get("p50", []))
                print(f"\nRequested forecast for {test_data['forecast_days']} days")
                print(f"Received forecast for {p50_length} days")
                
                if p50_length == test_data["forecast_days"]:
                    print("✓ Forecast days match request")
                else:
                    print("✗ Forecast days don't match request")
                
                # Calculate increase percentage
                first_value = forecast.get("p50", [0])[0]
                last_value = forecast.get("p50", [0])[-1]
                if first_value > 0:
                    increase_percentage = ((last_value - first_value) / first_value) * 100
                    print(f"\nForecast trend: {increase_percentage:.2f}% change from first to last day")
                
            else:
                print("Response missing expected fields")
                print(f"Response: {result}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing forecast endpoint: {e}")

def test_invalid_inputs():
    """Test the forecast endpoint with invalid inputs"""
    
    test_cases = [
        # Missing forecast days
        {
            "history_data": [100, 110, 120, 130, 140, 150, 160],
            "is_holiday": [0, 0, 0, 0, 0, 0, 0],
            "onpromotion": [0, 0, 0, 0, 0, 0, 0]
        },
        # Invalid forecast days (too many)
        {
            "forecast_days": 30,  # Model supports max 7 days
            "history_data": [100, 110, 120, 130, 140, 150, 160],
            "is_holiday": [0, 0, 0, 0, 0, 0, 0],
            "onpromotion": [0, 0, 0, 0, 0, 0, 0]
        },
        # Missing history data
        {
            "forecast_days": 7,
            "is_holiday": [0, 0, 0, 0, 0, 0, 0],
            "onpromotion": [0, 0, 0, 0, 0, 0, 0]
        },
        # Empty history data
        {
            "forecast_days": 7,
            "history_data": [],
            "is_holiday": [0, 0, 0, 0, 0, 0, 0],
            "onpromotion": [0, 0, 0, 0, 0, 0, 0]
        },
        # Negative values in history data
        {
            "forecast_days": 7,
            "history_data": [-100, -110, -120, -130, -140, -150, -160],
            "is_holiday": [0, 0, 0, 0, 0, 0, 0],
            "onpromotion": [0, 0, 0, 0, 0, 0, 0]
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest case {i+1}: {test_case}")
        try:
            response = requests.post(f"{BASE_URL}/test-forecast", json=test_case)
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                print("Unexpected success for invalid input")
                print(f"Response: {response.json()}")
            else:
                print("Expected error for invalid input")
                print(f"Error message: {response.text}")
                
        except Exception as e:
            print(f"Error during test: {e}")

def test_different_history_lengths():
    """Test the forecast endpoint with different history data lengths"""
    
    # Different history lengths to test
    history_lengths = [7, 14, 28]
    
    for length in history_lengths:
        # Generate history data of specified length
        history_data = [100 + i*10 for i in range(length)]
        is_holiday = [0] * length
        onpromotion = [0] * length
        
        test_data = {
            "forecast_days": 7,
            "history_data": history_data,
            "is_holiday": is_holiday,
            "onpromotion": onpromotion
        }
        
        print(f"\nTesting with history length: {length}")
        try:
            response = requests.post(f"{BASE_URL}/test-forecast", json=test_data)
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check forecast
                if "forecast" in result and "p50" in result["forecast"]:
                    p50 = result["forecast"]["p50"]
                    print(f"P50 forecast: {p50}")
                    
                    # Calculate average of forecast
                    avg_forecast = sum(p50) / len(p50)
                    print(f"Average forecast value: {avg_forecast:.2f}")
                    
                    # Calculate average of history
                    avg_history = sum(history_data) / len(history_data)
                    print(f"Average history value: {avg_history:.2f}")
                    
                    # Compare averages
                    diff_percentage = ((avg_forecast - avg_history) / avg_history) * 100
                    print(f"Difference between averages: {diff_percentage:.2f}%")
                    
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Error testing with history length {length}: {e}")

if __name__ == "__main__":
    print("Running forecast tests...\n")
    test_forecast()
    
    print("\n" + "-"*50)
    print("Testing invalid inputs...")
    test_invalid_inputs()
    
    print("\n" + "-"*50)
    print("Testing different history lengths...")
    test_different_history_lengths()
