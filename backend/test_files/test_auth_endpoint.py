#!/usr/bin/env python3
"""
Test script to generate a fresh Firebase token and test authentication endpoints
"""
import requests
import firebase_admin
from firebase_admin import auth, credentials
import json
import os

# Initialize Firebase with service account
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate('firebase-key.json')
        firebase_admin.initialize_app(cred)

def create_custom_token(uid="test_user"):
    """Create a custom token for testing"""
    try:
        # Add additional claims including email
        additional_claims = {
            'email': 'test@example.com',
            'name': 'Test User'
        }
        custom_token = auth.create_custom_token(uid, additional_claims)
        return custom_token.decode('utf-8')
    except Exception as e:
        print(f"Error creating custom token: {e}")
        return None

def exchange_custom_token_for_id_token(custom_token):
    """Exchange custom token for ID token using Firebase REST API"""
    try:
        # Firebase Auth REST API endpoint for token exchange
        url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
        
        # Get API key from environment or config
        api_key = "ENTER_YOUR_API_KEY"  # This is the web API key for the project
        
        payload = {
            "token": custom_token,
            "returnSecureToken": True
        }
        
        response = requests.post(f"{url}?key={api_key}", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('idToken')
        else:
            print(f"Token exchange failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error exchanging token: {e}")
        return None

def test_endpoints():
    """Test the authentication endpoints"""
    
    # Initialize Firebase
    init_firebase()
    
    # Base URL for the main API (or minimal for testing)
    base_url = "https://sales-prediction-api-qmp76ddexq-el.a.run.app"  # Main API
    # base_url = "https://sales-prediction-api-minimal-1073252424641.asia-south1.run.app"  # Minimal API for testing
    
    # Test health endpoint (no auth required)
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health endpoint status: {response.status_code}")
        print(f"Health response: {response.json()}")
    except Exception as e:
        print(f"Health endpoint error: {e}")
    
    # Create a custom token for testing
    print("\nCreating custom token...")
    custom_token = create_custom_token("test_user_12345")
    if not custom_token:
        print("Failed to create custom token")
        return
    
    print(f"Custom token created: {custom_token[:50]}...")
    
    # Exchange custom token for ID token
    print("\nExchanging custom token for ID token...")
    id_token = exchange_custom_token_for_id_token(custom_token)
    if not id_token:
        print("Failed to exchange custom token for ID token")
        return
    
    print(f"ID token created: {id_token[:50]}...")
    
    # Test protected endpoints with ID token
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    # Test auth-test endpoint
    print("\nTesting auth-test endpoint...")
    try:
        response = requests.get(f"{base_url}/auth-test", headers=headers)
        print(f"Auth-test status: {response.status_code}")
        print(f"Auth-test response: {response.json()}")
    except Exception as e:
        print(f"Auth-test error: {e}")
    
    # Test user endpoint
    print("\nTesting user endpoint...")
    try:
        response = requests.get(f"{base_url}/user", headers=headers)
        print(f"User endpoint status: {response.status_code}")
        print(f"User response: {response.json()}")
    except Exception as e:
        print(f"User endpoint error: {e}")
    
    # Test forecast endpoint
    print("\nTesting forecast endpoint...")
    forecast_data = {
        "forecast_days": 7,
        "history_data": [100, 110, 120, 130, 140, 150, 160],
        "is_holiday": [0, 0, 0, 0, 0, 0, 0],
        "onpromotion": [0, 0, 0, 0, 0, 0, 0]
    }
    
    try:
        response = requests.post(f"{base_url}/forecast", headers=headers, json=forecast_data)
        print(f"Forecast endpoint status: {response.status_code}")
        
        # Print the forecast data in a more readable format
        if response.status_code == 200:
            forecast_response = response.json()
            print("Forecast response summary:")
            print(f"  Success: {forecast_response.get('success')}")
            print(f"  User: {forecast_response.get('user')}")
            print(f"  Prediction ID: {forecast_response.get('prediction_id')}")
            print(f"  Used real data: {forecast_response.get('used_real_data')}")
            
            forecast = forecast_response.get('forecast', {})
            if forecast:
                p50 = forecast.get('p50', [])
                print(f"  P50 forecast (first few days): {p50[:3]}...")
        else:
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"Forecast endpoint error: {e}")
    
    return id_token  # Return the token for other tests

if __name__ == "__main__":
    token = test_endpoints()
    
    # Save token to file for other tests
    if token:
        with open("firebase_id_token.txt", "w") as f:
            f.write(token)
        print("\nToken saved to firebase_id_token.txt")
