# Model Constraints and Technical Details

## TFT Model Specifications

The Temporal Fusion Transformer (TFT) model used in this application is designed for time series forecasting of sales data.

### Key Parameters

- **max_encoder_length=30**: The model uses 30 days of historical data as input
- **max_prediction_length=7**: The model can only predict up to 7 days into the future
- **decoder_length=1**: Used during ONNX conversion for tracing

## Limitations

### 7-Day Forecast Limit

The model was specifically trained with `max_prediction_length=7`, which means it can only generate forecasts for up to 7 days. Attempting to request forecasts for longer periods (like 14 or 30 days) will result in errors.

### Technical Explanation

During the ONNX conversion process, the model was traced with `decoder_length=1`, which means multi-step prediction must be handled explicitly in the inference code. The backend implementation handles this for 7-day forecasts, but cannot properly extend beyond this limit due to the model's training constraints.

## API Enforcement

The API enforces these constraints through validation:

```python
class ForecastRequest(BaseModel):
    forecast_days: int = 7  # Fixed to 7 days as model was trained with max_prediction_length=7
    
    # Validator to enforce 7-day maximum forecast
    def __init__(self, **data):
        if 'forecast_days' in data and data['forecast_days'] > 7:
            data['forecast_days'] = 7  # Limit to 7 days maximum
        super().__init__(**data)
```

## Future Improvements

To enable longer-term forecasts, the following approaches could be considered:

1. **Retrain the model**: Create a new TFT model with a larger `max_prediction_length`
2. **Create separate models**: Build different models for different forecast horizons
3. **Improved multi-step approach**: Develop a more sophisticated approach for multi-step prediction beyond what was used in the ONNX tracing

## References

- [Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting](https://arxiv.org/abs/1912.09363)
- [PyTorch Forecasting Documentation](https://pytorch-forecasting.readthedocs.io/)
- [ONNX Runtime Documentation](https://onnxruntime.ai/)
