FROM python:3.10-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements_minimal.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_minimal.txt && \
    pip install --no-cache-dir onnxruntime==1.17.0

# Copy application files
COPY app_minimal.py ./app.py
COPY firebase-key.json .
COPY tft_model_cpu.onnx .

# Create uploads directory
RUN mkdir -p uploads
RUN chmod -R 755 uploads

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV FIREBASE_SERVICE_ACCOUNT=firebase-key.json

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
