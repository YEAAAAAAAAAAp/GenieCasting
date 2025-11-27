FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build actor index at runtime and start server
CMD python backend/scripts/build_actor_index_insightface.py --dataset dataset/ --clusters 1 && \
    uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
