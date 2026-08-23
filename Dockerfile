# Use official lightweight Python image
FROM python:3.10-slim

# Prevent Python from writing pyc files to disk and enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies needed for compiling psycopg2 and other packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the API port
EXPOSE 8000

# Start the FastAPI server using Gunicorn for multi-process concurrency
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "1", "--timeout", "120", "--bind", "0.0.0.0:8000"]