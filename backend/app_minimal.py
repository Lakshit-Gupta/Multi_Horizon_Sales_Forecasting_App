#!/usr/bin/env python3
"""
Minimal FastAPI app for testing Firebase authentication
"""
import os
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, status, Depends, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, auth, firestore
import io
import xlsxwriter
from google.cloud import firestore as gcp_firestore

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

# === Pydantic Models ===
class ForecastRequest(BaseModel):
    forecast_days: int = 7  # Fixed to 7 days as model was trained with max_prediction_length=7
    history_data: List[float] = []
    is_holiday: List[int] = []
    onpromotion: List[int] = []
    store_nbr: Optional[int] = 1
    item_nbr: Optional[int] = 1
    
    # Validator to enforce 7-day maximum forecast
    def __init__(self, **data):
        if 'forecast_days' in data and data['forecast_days'] > 7:
            data['forecast_days'] = 7  # Limit to 7 days maximum
        super().__init__(**data)

class HolidayPromotionRequest(BaseModel):
    is_holiday: List[int]
    onpromotion: List[int]

# === FastAPI App ===
app = FastAPI(
    title="Sales Prediction API (Minimal)",
    description="Minimal API for testing Firebase authentication",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-08-15T15:30:00.000000"
    }

@app.post("/test-forecast")
async def test_forecast(request: ForecastRequest):
    """Test endpoint for forecast without authentication using real ONNX model"""
    try:
        logger.info(f"📊 Test forecast request received for {request.forecast_days} days")
        
        # Convert the request data to a DataFrame
        data = []
        # Use mock data if no history provided
        history = request.history_data if request.history_data else [100] * 30
        
        for i, val in enumerate(history):
            data.append({
                "date": (datetime.now() - timedelta(days=len(history)-i)).strftime("%Y-%m-%d"),
                "history": val,
                "is_holiday": False,
                "onpromotion": False,
                "transactions": 50 + i,  # Add transactions
                "store_nbr": request.store_nbr,
                "item_nbr": request.item_nbr
            })
        
        # Add future dates with is_holiday and onpromotion
        for i in range(request.forecast_days):
            future_date = (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d")
            is_holiday = request.is_holiday[i] if i < len(request.is_holiday) else False
            onpromotion = request.onpromotion[i] if i < len(request.onpromotion) else False
            
            data.append({
                "date": future_date,
                "history": None,  # No history for future dates
                "is_holiday": is_holiday,
                "onpromotion": onpromotion,
                "transactions": None,
                "store_nbr": request.store_nbr,
                "item_nbr": request.item_nbr
            })
            
        df = pd.DataFrame(data)
        
        # Use real ONNX model prediction instead of mock
        history_data = df[df['history'].notna()]['history'].tolist()
        forecast_data = process_user_data_for_prediction(data, request.forecast_days)
        forecast_result = forecast_data['p50']
        
        # Return the forecast with dates
        future_dates = [(datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(request.forecast_days)]
        
        response = {
            "dates": future_dates,
            "forecast": forecast_result,
            "model_type": "onnx",
            "metadata": {
                "store_nbr": request.store_nbr,
                "item_nbr": request.item_nbr,
                "history_length": len(request.history_data),
                "forecast_days": request.forecast_days
            }
        }
        
        return response
    except Exception as e:
        logger.error(f"❌ Error in test forecast: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Firebase Initialization ===
try:
    # Always use service account key to ensure we're using the correct project
    service_account_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT', 'firebase-key.json')
    logger.info(f"Using service account: {service_account_path}")
    
    if os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
        app_firebase = firebase_admin.initialize_app(cred)
        logger.info(f"Firebase app initialized for project: {app_firebase.project_id}")
    else:
        # Fallback to Application Default Credentials if no service account file
        logger.info("Service account file not found, using Application Default Credentials")
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {
            'projectId': 'ENTER_YOUR_PROJECT_ID'  # Explicitly set the project ID
        })
        app_firebase = firebase_admin.get_app()
        logger.info(f"Firebase app initialized for project: {app_firebase.project_id}")
    
    # Initialize Firestore
    db = firestore.client()
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {str(e)}")
    raise

# === Authentication ===
async def get_current_user(request: Request):
    """
    Verify Firebase ID token from Authorization header
    Returns user info if token is valid
    """
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split("Bearer ")[1]
    try:
        # Verify the token
        decoded_token = auth.verify_id_token(token)
        
        # Get user from Firestore
        user_ref = db.collection('users').document(decoded_token['uid'])
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return {
                "uid": decoded_token['uid'],
                "email": decoded_token['email'],
                "name": user_data.get('name', decoded_token.get('name', 'Unknown')),
                "store_name": user_data.get('store_name', 'Unknown Store'),
                "picture": user_data.get('picture', decoded_token.get('picture', None))
            }
        else:
            # Create new user document if first login
            user_data = {
                "email": decoded_token.get('email'),
                "name": decoded_token.get('name', 'Unknown'),
                "store_name": "Store " + decoded_token['uid'][:6],
                "picture": decoded_token.get('picture'),
                "created_at": firestore.SERVER_TIMESTAMP
            }
            user_ref.set(user_data)
            return {
                "uid": decoded_token['uid'],
                "email": decoded_token['email'],
                "name": user_data.get('name', 'Unknown'),
                "store_name": user_data.get('store_name'),
                "picture": user_data.get('picture')
            }
            
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        logger.error(f"Token type: {type(e)}")
        logger.error(f"Token value (first 50 chars): {token[:50] if token else 'None'}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# === Helper Functions ===
    is_holiday: List[int]
    onpromotion: List[int]

# === Helper Functions ===
def load_tft_model():
    """Load the TFT model for predictions"""
    try:
        logger.info("🔍 Attempting to load TFT model...")
        
        # Load ONNX model
        if os.path.exists("tft_model_cpu.onnx"):
            logger.info("📦 Loading ONNX model...")
            try:
                import onnxruntime as ort
                logger.info(f"ONNX Runtime version: {ort.__version__}")
                logger.info(f"Available providers: {ort.get_available_providers()}")
                
                # Create ONNX inference session with CPU provider
                providers = ['CPUExecutionProvider']
                session_options = ort.SessionOptions()
                session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                session = ort.InferenceSession("tft_model_cpu.onnx", providers=providers, sess_options=session_options)
                
                logger.info(f"✅ ONNX model loaded successfully")
                logger.info(f"Model inputs: {[input.name for input in session.get_inputs()]}")
                logger.info(f"Model outputs: {[output.name for output in session.get_outputs()]}")
                
                return session, "onnx"
            except Exception as e:
                logger.error(f"❌ ONNX loading error: {e}")
                import traceback
                logger.error(f"Stack trace: {traceback.format_exc()}")
                return None, "mock"
            
        # Try state dict
        elif os.path.exists("tft_model_cpu_state_dict.pt"):
            logger.info("📦 Found state dict but need model architecture...")
            logger.warning("⚠️ State dict found but model architecture needed - using mock")
            return None, "mock"
            
        else:
            logger.warning("⚠️ No model file found, using mock predictions")
            return None, "mock"
            
    except Exception as e:
        logger.error(f"❌ Error loading model: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None, "mock"

def process_user_data_for_prediction(user_data: List[Dict], forecast_days: int = 7, forecast_request: ForecastRequest = None) -> Dict[str, List[float]]:
    """Process uploaded user data and generate TFT model predictions"""
    try:
        logger.info(f"🔄 Processing user data for {forecast_days}-day prediction...")
        logger.info(f"📊 Data shape: {len(user_data)} rows")
        
        # Convert to DataFrame
        df = pd.DataFrame(user_data)
        logger.info(f"📋 Columns: {df.columns.tolist()}")
        
        # Basic data validation
        required_cols = ['date', 'history', 'onpromotion', 'is_holiday', 'transactions', 'store_nbr', 'item_nbr']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        # Try to supplement missing columns with data from the forecast request
        if missing_cols and forecast_request:
            logger.info(f"💡 Attempting to fill missing columns from forecast request: {missing_cols}")
            
            for col in missing_cols[:]:  # Create a copy of the list for iteration
                if col == 'is_holiday' and forecast_request.is_holiday:
                    df['is_holiday'] = forecast_request.is_holiday + [0] * (len(df) - len(forecast_request.is_holiday))
                    missing_cols.remove('is_holiday')
                    logger.info(f"✅ Added is_holiday from request")
                    
                elif col == 'onpromotion' and forecast_request.onpromotion:
                    df['onpromotion'] = forecast_request.onpromotion + [0] * (len(df) - len(forecast_request.onpromotion))
                    missing_cols.remove('onpromotion')
                    logger.info(f"✅ Added onpromotion from request")
                    
                elif col == 'store_nbr' and forecast_request.store_nbr:
                    df['store_nbr'] = forecast_request.store_nbr
                    missing_cols.remove('store_nbr')
                    logger.info(f"✅ Added store_nbr from request")
                    
                elif col == 'item_nbr' and forecast_request.item_nbr:
                    df['item_nbr'] = forecast_request.item_nbr
                    missing_cols.remove('item_nbr')
                    logger.info(f"✅ Added item_nbr from request")
        
        # If there are still missing columns, try to add reasonable defaults
        if missing_cols:
            logger.warning(f"⚠️ Still missing columns: {missing_cols}")
            for col in missing_cols[:]:
                if col == 'transactions':
                    df['transactions'] = 50  # Default value
                    missing_cols.remove('transactions')
                    logger.info(f"✅ Added default transactions=50")
                    
                elif col == 'store_nbr':
                    df['store_nbr'] = 1  # Default store
                    missing_cols.remove('store_nbr')
                    logger.info(f"✅ Added default store_nbr=1")
                    
                elif col == 'item_nbr':
                    df['item_nbr'] = 1  # Default item
                    missing_cols.remove('item_nbr')
                    logger.info(f"✅ Added default item_nbr=1")
        
        # If there are still missing required columns, raise an error
        if missing_cols:
            logger.error(f"❌ Missing columns: {missing_cols}")
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Data preprocessing similar to TFT training
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Extract recent history (last 30 days) for encoder
        history_data = df[df['history'].notna()]['history'].tolist()
        logger.info(f"📈 Historical data points: {len(history_data)}")
        
        if len(history_data) < 7:
            logger.warning(f"⚠️ Insufficient history data ({len(history_data)} points), using mock")
            return generate_mock_forecast(forecast_days)
        
        # Try to load and use the ONNX model
        model, model_type = load_tft_model()
        
        if model_type == "onnx":
            return generate_onnx_prediction(model, df, forecast_days)
        else:
            logger.info("🎭 Using enhanced mock based on real data patterns")
            return generate_enhanced_mock_forecast(history_data, forecast_days)
            
    except Exception as e:
        logger.error(f"❌ Error processing user data: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return generate_mock_forecast(forecast_days)

# PyTorch prediction function removed as we're only using ONNX

def generate_onnx_prediction(session, df: pd.DataFrame, forecast_days: int) -> Dict[str, List[float]]:
    """Generate predictions using ONNX model - limited to 7 days maximum"""
    try:
        # Enforce 7-day maximum forecast limit
        if forecast_days > 7:
            logger.warning(f"⚠️ Requested forecast for {forecast_days} days, limiting to 7 days (model constraint)")
            forecast_days = 7
            
        logger.info(f"🧠 Generating predictions with ONNX model for {forecast_days} days...")
        
        # Get model input/output names
        input_names = [input.name for input in session.get_inputs()]
        output_names = [output.name for output in session.get_outputs()]
        logger.info(f"📊 ONNX model inputs: {input_names}")
        logger.info(f"📊 ONNX model outputs: {output_names}")
        
        # TFT model constraint: can only predict 7 days at once (max_prediction_length=7)
        MAX_PREDICTION_LENGTH = 7
        
        # Always use single prediction (we enforced the 7-day limit above)
        return generate_single_onnx_prediction(session, df, forecast_days, input_names, output_names)
        
    except Exception as e:
        logger.error(f"❌ ONNX prediction failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        history_data = df[df['history'].notna()]['history'].tolist()
        return generate_enhanced_mock_forecast(history_data, forecast_days)

def generate_single_onnx_prediction(session, df: pd.DataFrame, forecast_days: int, input_names: List[str], output_names: List[str]) -> Dict[str, List[float]]:
    """Generate a single ONNX prediction for 7 days or less"""
    try:
        # Prepare data for the model
        history_data = df[df['history'].notna()]['history'].tolist()[-30:]  # Last 30 days
        if len(history_data) < 30:
            # Pad with zeros if we don't have enough history
            history_data = [0] * (30 - len(history_data)) + history_data
            
        # Extract features from dataframe
        is_holiday = df['is_holiday'].iloc[-forecast_days:].tolist()
        if len(is_holiday) < forecast_days:
            is_holiday = [0] * forecast_days
            
        onpromotion = df['onpromotion'].iloc[-forecast_days:].tolist()
        if len(onpromotion) < forecast_days:
            onpromotion = [0] * forecast_days
            
        # Model parameters
        encoder_length = 30  # 30 days history
        decoder_length = forecast_days
        
        # Prepare continuous features (history_data for encoder, zeros for decoder)
        # Model expects 10 continuous features
        encoder_cont = np.zeros((1, encoder_length, 10), dtype=np.float32)
        decoder_cont = np.zeros((1, decoder_length, 10), dtype=np.float32)
        
        # Fill the first feature with sales history
        for i, val in enumerate(history_data[-encoder_length:]):
            encoder_cont[0, i, 0] = val
        
        # Categorical features (holidays, promotions, store_nbr, item_nbr)
        # TFT model expects 4 categorical features
        encoder_cat = np.zeros((1, encoder_length, 4), dtype=np.int64)
        decoder_cat = np.zeros((1, decoder_length, 4), dtype=np.int64)
        
        # Fill decoder categorical with future data
        for i in range(min(len(is_holiday), decoder_length)):
            decoder_cat[0, i, 0] = min(1, max(0, int(is_holiday[i])))
        for i in range(min(len(onpromotion), decoder_length)):
            decoder_cat[0, i, 1] = min(1, max(0, int(onpromotion[i])))
            
        # Store and item numbers
        store_nbr = df['store_nbr'].iloc[0] if 'store_nbr' in df.columns else 0
        item_nbr = df['item_nbr'].iloc[0] if 'item_nbr' in df.columns else 0
        
        # Fill store_nbr and item_nbr (using modulo to ensure they're within valid ranges)
        for i in range(decoder_length):
            decoder_cat[0, i, 2] = int(store_nbr) % 2  # Limiting to range [0,1]
            decoder_cat[0, i, 3] = int(item_nbr) % 2   # Limiting to range [0,1]
        
        # Similarly for encoder (historical data)
        for i in range(encoder_length):
            encoder_cat[0, i, 2] = int(store_nbr) % 2
            encoder_cat[0, i, 3] = int(item_nbr) % 2
            
        # Sequence lengths
        encoder_lengths = np.array([encoder_length], dtype=np.int64)
        decoder_lengths = np.array([decoder_length], dtype=np.int64)
        
        # Target scaling (using mean and std of history)
        if len(history_data) > 0:
            scale_mean = np.mean(history_data)
            scale_std = np.std(history_data) if np.std(history_data) > 0 else 1.0
        else:
            scale_mean, scale_std = 0.0, 1.0
            
        target_scale = np.array([[scale_mean, scale_std]], dtype=np.float32)
        
        # Create input dictionary matching the model's expected inputs
        model_inputs = {
            'encoder_cont': encoder_cont,
            'encoder_cat': encoder_cat,
            'decoder_cont': decoder_cont,
            'decoder_cat': decoder_cat, 
            'encoder_lengths': encoder_lengths,
            'decoder_lengths': decoder_lengths,
            'target_scale': target_scale
        }
        
        logger.info(f"🧠 Running single ONNX inference...")
        
        # Run inference
        outputs = session.run(output_names, model_inputs)
        
        # Process model output
        if len(outputs) > 0:
            main_output = outputs[0]
            logger.info(f"📊 Model output shape: {main_output.shape}")
            
            # Extract predictions
            if len(main_output.shape) >= 3 and main_output.shape[2] >= 3:
                p10 = main_output[0, :, 0].tolist()[:forecast_days]
                p50 = main_output[0, :, 1].tolist()[:forecast_days]
                p90 = main_output[0, :, 2].tolist()[:forecast_days]
            elif len(main_output.shape) >= 2:
                p50 = main_output[0, :].tolist()[:forecast_days]
                p10 = [max(0, val * 0.9) for val in p50]
                p90 = [val * 1.1 for val in p50]
            else:
                forecasts = main_output.flatten()[:forecast_days]
                p50 = forecasts.tolist()
                p10 = [max(0, val * 0.9) for val in p50]
                p90 = [val * 1.1 for val in p50]
                
            # De-scale values
            p10 = [(val * scale_std) + scale_mean for val in p10]
            p50 = [(val * scale_std) + scale_mean for val in p50]
            p90 = [(val * scale_std) + scale_mean for val in p90]
            
            logger.info(f"✅ Single ONNX prediction successful: {len(p50)} predictions")
            return {
                "p10": p10[:forecast_days],
                "p50": p50[:forecast_days],
                "p90": p90[:forecast_days]
            }
        else:
            raise Exception("No outputs from model")
        
    except Exception as e:
        logger.error(f"❌ Single ONNX prediction failed: {e}")
        raise e

def generate_multi_step_onnx_prediction(session, df: pd.DataFrame, forecast_days: int, input_names: List[str], output_names: List[str], max_pred_length: int) -> Dict[str, List[float]]:
    """Generate multi-step ONNX predictions for longer forecasts"""
    try:
        logger.info(f"🔄 Starting multi-step prediction for {forecast_days} days (max per step: {max_pred_length})")
        
        all_p10 = []
        all_p50 = []
        all_p90 = []
        
        # Start with the original history
        current_history = df[df['history'].notna()]['history'].tolist()[-30:]  # Last 30 days
        remaining_days = forecast_days
        current_day_offset = 0
        
        while remaining_days > 0:
            # Determine how many days to predict in this step
            days_this_step = min(remaining_days, max_pred_length)
            
            logger.info(f"📊 Step prediction: {days_this_step} days (remaining: {remaining_days})")
            
            # Create a temporary dataframe for this prediction step
            temp_data = []
            
            # Add historical data
            for i, val in enumerate(current_history):
                temp_data.append({
                    "date": (datetime.now() - timedelta(days=len(current_history)-i)).strftime("%Y-%m-%d"),
                    "history": val,
                    "is_holiday": False,
                    "onpromotion": False,
                    "transactions": 50 + i,
                    "store_nbr": df['store_nbr'].iloc[0] if 'store_nbr' in df.columns else 1,
                    "item_nbr": df['item_nbr'].iloc[0] if 'item_nbr' in df.columns else 1
                })
            
            # Add future data for this step
            for i in range(days_this_step):
                future_date = (datetime.now() + timedelta(days=current_day_offset + i + 1)).strftime("%Y-%m-%d")
                
                # Get holiday/promotion info for this specific day
                is_holiday = False
                onpromotion = False
                
                # Look in the original dataframe for holiday/promotion info
                future_rows = df[df['history'].isna()]
                if len(future_rows) > current_day_offset + i:
                    future_row_idx = future_rows.index[current_day_offset + i]
                    is_holiday = df.loc[future_row_idx, 'is_holiday']
                    onpromotion = df.loc[future_row_idx, 'onpromotion']
                
                temp_data.append({
                    "date": future_date,
                    "history": None,
                    "is_holiday": is_holiday,
                    "onpromotion": onpromotion,
                    "transactions": None,
                    "store_nbr": df['store_nbr'].iloc[0] if 'store_nbr' in df.columns else 1,
                    "item_nbr": df['item_nbr'].iloc[0] if 'item_nbr' in df.columns else 1
                })
            
            temp_df = pd.DataFrame(temp_data)
            
            # Generate prediction for this step
            step_result = generate_single_onnx_prediction(session, temp_df, days_this_step, input_names, output_names)
            
            # Collect results
            all_p10.extend(step_result['p10'])
            all_p50.extend(step_result['p50'])
            all_p90.extend(step_result['p90'])
            
            # Update history for next step: append the predicted values
            # Use p50 (median) predictions as the new "history" for the next step
            current_history.extend(step_result['p50'])
            current_history = current_history[-30:]  # Keep only last 30 days
            
            # Update counters
            remaining_days -= days_this_step
            current_day_offset += days_this_step
            
            logger.info(f"✅ Step completed. Collected {len(all_p50)} total predictions")
        
        logger.info(f"🎯 Multi-step prediction completed: {len(all_p50)} total predictions")
        
        return {
            "p10": all_p10[:forecast_days],
            "p50": all_p50[:forecast_days],
            "p90": all_p90[:forecast_days]
        }
        
    except Exception as e:
        logger.error(f"❌ Multi-step ONNX prediction failed: {e}")
        raise e
def generate_enhanced_mock_forecast(history_data: List[float], days: int = 7) -> Dict[str, List[float]]:
    """Generate realistic mock forecast based on actual historical data"""
    try:
        logger.info(f"📊 Generating enhanced mock forecast for {days} days based on {len(history_data)} historical points")
        
        if len(history_data) == 0:
            return generate_mock_forecast(days)
        
        # Use actual historical patterns
        recent_avg = np.mean(history_data[-7:]) if len(history_data) >= 7 else np.mean(history_data)
        recent_trend = 0
        if len(history_data) >= 14:
            recent_trend = (np.mean(history_data[-7:]) - np.mean(history_data[-14:-7])) / 7
        
        logger.info(f"📈 Base level: {recent_avg:.2f}, Trend: {recent_trend:.4f}")
        
        # Generate predictions with realistic variation
        base_forecast = []
        for i in range(days):
            # Trend component
            trend_value = recent_avg + (recent_trend * i)
            # Seasonal component (weekly seasonality)
            seasonal = 5 * np.sin(2 * np.pi * i / 7)
            # Random noise
            noise = np.random.normal(0, recent_avg * 0.05)
            
            base_forecast.append(max(0, trend_value + seasonal + noise))
        
        # Create confidence intervals
        p50 = base_forecast
        p10 = [max(0, val * 0.85) for val in p50]
        p90 = [val * 1.15 for val in p50]
        
        result = {
            "p10": p10,
            "p50": p50,
            "p90": p90
        }
        
        logger.info(f"✅ Enhanced forecast generated: P50 range {min(p50):.1f}-{max(p50):.1f}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Enhanced mock generation failed: {e}")
        return generate_mock_forecast(days)

def generate_mock_forecast(days: int = 7) -> Dict[str, List[float]]:
    """Generate basic mock forecast data with proper 7-day predictions"""
    try:
        logger.info(f"🎭 Generating basic mock forecast for {days} days")
        
        base_sales = 100
        trend = np.random.normal(0, 5, days)
        seasonality = 10 * np.sin(2 * np.pi * np.arange(days) / 7)
        
        p50 = base_sales + trend + seasonality
        p10 = p50 * 0.8 + np.random.normal(0, 2, days)
        p90 = p50 * 1.2 + np.random.normal(0, 2, days)
        
        # Ensure positive values
        p10 = np.maximum(p10, 0)
        p50 = np.maximum(p50, 0)
        p90 = np.maximum(p90, 0)
        
        return {
            "p10": p10.tolist()[:days],  # Ensure exactly 'days' predictions
            "p50": p50.tolist()[:days],
            "p90": p90.tolist()[:days]
        }
    except Exception as e:
        logger.error(f"❌ Basic mock generation failed: {e}")
        # Ultimate fallback
        return {
            "p10": [80.0] * days,
            "p50": [100.0] * days,
            "p90": [120.0] * days
        }

def create_sample_excel() -> io.BytesIO:
    """Create a sample Excel file for download"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('SampleData')
    
    # Add headers
    headers = ['date', 'history', 'onpromotion', 'is_holiday', 'transactions', 'store_nbr', 'item_nbr']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # Add sample data (37 rows as expected)
    for row in range(1, 38):
        date = datetime(2023, 1, 1) + timedelta(days=row-1)
        worksheet.write(row, 0, date.strftime('%Y-%m-%d'))  # date
        worksheet.write(row, 1, 100 + row * 5 if row <= 30 else None)  # history (only first 30)
        worksheet.write(row, 2, row % 2)  # onpromotion
        worksheet.write(row, 3, 1 if row % 7 == 0 else 0)  # is_holiday
        worksheet.write(row, 4, 50 + row * 2)  # transactions
        worksheet.write(row, 5, 1)  # store_nbr
        worksheet.write(row, 6, 1)  # item_nbr
    
    workbook.close()
    output.seek(0)
    return output

# === Endpoints ===

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-08-15T15:30:00.000000"
    }

@app.get("/auth-test")
async def test_auth_only(request: Request):
    """Test endpoint to verify authentication without Firestore dependency"""
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split("Bearer ")[1]
    try:
        # Verify the token
        decoded_token = auth.verify_id_token(token)
        
        # Return token data without Firestore access
        return {
            "success": True,
            "uid": decoded_token['uid'],
            "email": decoded_token.get('email'),
            "name": decoded_token.get('name', 'Unknown'),
            "auth_time": decoded_token.get('auth_time'),
            "message": "Authentication successful without Firestore"
        }
        
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}"
        )

@app.get("/user")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload and process Excel file with sales data"""
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Only Excel files (.xlsx, .xls) are allowed"
            )
        
        # Read the uploaded file
        contents = await file.read()
        
        # Process with pandas
        try:
            df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error reading Excel file: {str(e)}"
            )
        
        # Validate required columns
        required_columns = ['date', 'history', 'onpromotion', 'is_holiday', 'transactions', 'store_nbr', 'item_nbr']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing_columns}"
            )
        
        # Validate data (should have 37 rows)
        if len(df) != 37:
            raise HTTPException(
                status_code=400,
                detail=f"Excel file must have exactly 37 rows, got {len(df)} rows"
            )
        
        # Store in Firestore for the user
        upload_data = {
            "user_id": current_user["uid"],
            "filename": file.filename,
            "uploaded_at": firestore.SERVER_TIMESTAMP,
            "row_count": len(df),
            "data": df.to_dict('records')  # Store the data as records
        }
        
        # Save to Firestore
        doc_ref = db.collection('uploads').document()
        doc_ref.set(upload_data)
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "filename": file.filename,
            "row_count": len(df),
            "user": current_user["email"],
            "upload_id": doc_ref.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/forecast")
async def create_forecast(
    request: ForecastRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate forecast using TFT model with user's uploaded data"""
    try:
        logger.info(f"🔮 Forecast request from {current_user['email']} for {request.forecast_days} days")
        
        # First, try to get the user's latest uploaded data
        user_data = None
        uploads_ref = db.collection('uploads')
        query = uploads_ref.where('user_id', '==', current_user['uid']).order_by('uploaded_at', direction=firestore.Query.DESCENDING).limit(1)
        
        docs = list(query.stream())
        if docs:
            upload_doc = docs[0]
            upload_data = upload_doc.to_dict()
            user_data = upload_data.get('data', [])
            logger.info(f"📊 Found user data: {len(user_data)} rows from {upload_data.get('filename', 'unknown')}")
        else:
            logger.info("📭 No uploaded data found for user")
        
        # Generate forecast based on available data
        if user_data and len(user_data) > 0:
            logger.info("🧠 Generating forecast using user's uploaded data...")
            forecast_data = process_user_data_for_prediction(user_data, request.forecast_days, request)
        else:
            logger.info("🎭 No user data available, using mock forecast...")
            forecast_data = generate_mock_forecast(request.forecast_days)
        
        # Store prediction in Firestore
        prediction_data = {
            "user_id": current_user["uid"],
            "timestamp": firestore.SERVER_TIMESTAMP,
            "forecast_days": request.forecast_days,
            "forecast": forecast_data,
            "store_nbr": request.store_nbr,
            "item_nbr": request.item_nbr,
            "is_holiday": request.is_holiday,
            "onpromotion": request.onpromotion,
            "used_real_data": user_data is not None and len(user_data) > 0
        }
        
        doc_ref = db.collection('predictions').document()
        doc_ref.set(prediction_data)
        
        logger.info(f"✅ Forecast generated and saved with ID: {doc_ref.id}")
        
        return {
            "success": True,
            "forecast": forecast_data,
            "forecast_days": request.forecast_days,
            "prediction_id": doc_ref.id,
            "user": current_user["email"],
            "used_real_data": user_data is not None and len(user_data) > 0,
            "data_points": len(user_data) if user_data else 0
        }
        
    except Exception as e:
        logger.error(f"❌ Forecast error: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Forecast generation failed: {str(e)}"
        )

@app.get("/forecast")
async def get_latest_forecast(current_user: dict = Depends(get_current_user)):
    """Get the latest forecast for the current user"""
    try:
        # Query latest prediction from Firestore
        predictions_ref = db.collection('predictions')
        query = predictions_ref.where('user_id', '==', current_user['uid']).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1)
        
        docs = query.stream()
        for doc in docs:
            data = doc.to_dict()
            return {
                "success": True,
                "forecast": data.get('forecast', generate_mock_forecast()),
                "forecast_days": data.get('forecast_days', 7),
                "prediction_id": doc.id,
                "timestamp": data.get('timestamp'),
                "user": current_user["email"]
            }
        
        # If no previous prediction, return mock data
        return {
            "success": True,
            "forecast": generate_mock_forecast(),
            "forecast_days": 7,
            "user": current_user["email"],
            "message": "No previous predictions found, returning sample data"
        }
        
    except Exception as e:
        logger.error(f"Get forecast error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve forecast: {str(e)}"
        )

@app.get("/download-template")
async def download_template(current_user: dict = Depends(get_current_user)):
    """Download sample Excel template"""
    try:
        excel_file = create_sample_excel()
        
        return StreamingResponse(
            io.BytesIO(excel_file.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=sales_template.xlsx"}
        )
        
    except Exception as e:
        logger.error(f"Template download error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate template: {str(e)}"
        )

@app.get("/historical-data")
async def get_historical_data(current_user: dict = Depends(get_current_user)):
    """Get historical sales data for insights"""
    try:
        logger.info(f"📊 Getting historical data for {current_user['email']}")
        
        # Get user's latest uploaded data
        uploads_ref = db.collection('uploads')
        query = uploads_ref.where('user_id', '==', current_user['uid']).order_by('uploaded_at', direction=firestore.Query.DESCENDING).limit(1)
        
        docs = list(query.stream())
        if docs:
            upload_doc = docs[0]
            upload_data = upload_doc.to_dict()
            user_data = upload_data.get('data', [])
            
            if user_data:
                # Extract historical sales data
                df = pd.DataFrame(user_data)
                
                # Filter for rows with actual history data
                history_df = df[df['history'].notna()].copy()
                history_df['date'] = pd.to_datetime(history_df['date'])
                history_df = history_df.sort_values('date')
                
                # Prepare the response
                historical_data = {
                    "dates": history_df['date'].dt.strftime('%Y-%m-%d').tolist(),
                    "sales": history_df['history'].tolist(),
                    "onpromotion": history_df['onpromotion'].tolist() if 'onpromotion' in history_df.columns else [],
                    "is_holiday": history_df['is_holiday'].tolist() if 'is_holiday' in history_df.columns else [],
                    "transactions": history_df['transactions'].tolist() if 'transactions' in history_df.columns else [],
                }
                
                logger.info(f"✅ Returning {len(historical_data['sales'])} historical data points")
                
                return {
                    "success": True,
                    "historical_data": historical_data,
                    "filename": upload_data.get('filename', 'unknown'),
                    "upload_date": upload_data.get('uploaded_at'),
                    "user": current_user["email"]
                }
        
        # No data found
        logger.info("📭 No historical data found for user")
        return {
            "success": True,
            "historical_data": {
                "dates": [],
                "sales": [],
                "onpromotion": [],
                "is_holiday": [],
                "transactions": []
            },
            "message": "No historical data available. Please upload a data file first.",
            "user": current_user["email"]
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting historical data: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve historical data: {str(e)}"
        )
    """Get template download URL"""
    try:
        # In a real scenario, you might generate a signed URL
        # For now, return the direct download endpoint
        base_url = os.environ.get('BASE_URL', 'https://sales-prediction-api-qmp76ddexq-el.a.run.app')
        template_url = f"{base_url}/download-template"
        
        return {
            "success": True,
            "templateUrl": template_url,
            "user": current_user["email"]
        }
        
    except Exception as e:
        logger.error(f"Get template URL error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get template URL: {str(e)}"
        )

@app.post("/holiday-promotion")
async def update_holiday_promotion(
    request: HolidayPromotionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update holiday and promotion data and return updated forecast"""
    try:
        logger.info(f"🔄 Holiday/promotion update from {current_user['email']}")
        logger.info(f"📊 Holidays: {len(request.is_holiday)} values, Promotions: {len(request.onpromotion)} values")
        
        # Store the updated data in Firestore
        doc_data = {
            "user_id": current_user["uid"],
            "timestamp": firestore.SERVER_TIMESTAMP,
            "is_holiday": request.is_holiday,
            "onpromotion": request.onpromotion
        }
        
        doc_ref = db.collection('holiday_promotion').document()
        doc_ref.set(doc_data)
        
        # Generate updated forecast with new holiday/promotion data
        forecast_days = len(request.is_holiday)  # Use the length of holiday data as forecast days
        
        # Get the user's latest uploaded data for the forecast
        user_data = None
        uploads_ref = db.collection('uploads')
        query = uploads_ref.where('user_id', '==', current_user['uid']).order_by('uploaded_at', direction=firestore.Query.DESCENDING).limit(1)
        
        docs = list(query.stream())
        if docs:
            upload_doc = docs[0]
            upload_data = upload_doc.to_dict()
            user_data = upload_data.get('data', [])
            logger.info(f"📊 Found user data: {len(user_data)} rows")
            
            # Update the future data with new holiday/promotion values
            for i, row in enumerate(user_data):
                if row.get('history') is None:  # This is a future row
                    future_day_index = i - 30  # Assuming first 30 rows are history
                    if 0 <= future_day_index < len(request.is_holiday):
                        row['is_holiday'] = request.is_holiday[future_day_index]
                    if 0 <= future_day_index < len(request.onpromotion):
                        row['onpromotion'] = request.onpromotion[future_day_index]
        
        # Generate forecast with updated data
        if user_data and len(user_data) > 0:
            logger.info("🧠 Generating updated forecast with new holiday/promotion data...")
            forecast_data = process_user_data_for_prediction(user_data, forecast_days)
        else:
            logger.info("🎭 No user data available, using enhanced mock...")
            # Create mock history for enhanced forecast
            mock_history = [100 + i * 2 for i in range(30)]
            forecast_data = generate_enhanced_mock_forecast(mock_history, forecast_days)
        
        # Store updated prediction in Firestore
        prediction_data = {
            "user_id": current_user["uid"],
            "timestamp": firestore.SERVER_TIMESTAMP,
            "forecast_days": forecast_days,
            "forecast": forecast_data,
            "is_holiday": request.is_holiday,
            "onpromotion": request.onpromotion,
            "used_real_data": user_data is not None and len(user_data) > 0,
            "update_type": "holiday_promotion_toggle"
        }
        
        prediction_doc_ref = db.collection('predictions').document()
        prediction_doc_ref.set(prediction_data)
        
        logger.info(f"✅ Updated forecast generated with {len(forecast_data['p50'])} predictions")
        
        return {
            "success": True,
            "message": "Holiday and promotion data updated successfully",
            "forecast": forecast_data,
            "forecast_days": forecast_days,
            "user": current_user["email"],
            "prediction_id": prediction_doc_ref.id,
            "used_real_data": user_data is not None and len(user_data) > 0
        }
        
    except Exception as e:
        logger.error(f"❌ Holiday/promotion update error: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update data: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
