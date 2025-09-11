@echo off
echo =====================================================
echo Testing Forecast Functionality
echo =====================================================

echo.
echo 1. Testing Firebase authentication...
echo =====================================================
python test_files\test_auth_endpoint.py

echo.
echo 2. Testing basic forecast functionality (no auth)...
echo =====================================================
python test_files\test_forecast.py

echo.
echo 3. Testing authenticated forecasts...
echo =====================================================
python test_files\test_authenticated_forecast.py

echo.
echo 4. Testing multi-day forecasts...
echo =====================================================
python test_files\test_multi_day_forecasts.py

echo.
echo 5. Testing forecast toggles...
echo =====================================================
python test_files\test_forecast_toggles.py

echo.
echo 6. Testing file uploads...
echo =====================================================
python test_files\test_upload_forecast.py

echo.
echo 7. Testing frontend integration...
echo =====================================================
python test_files\test_frontend_integration.py

echo.
echo 8. Testing mobile workflow...
echo =====================================================
python test_files\test_mobile_workflow.py

echo.
echo All tests complete!
pause
