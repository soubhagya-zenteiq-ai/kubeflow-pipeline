# Use Python Slim to keep the image size under 200MB
FROM python:3.9-slim

WORKDIR /app

# Install dependencies first (for better Docker caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/main.py .

# Entrypoint allows Kubeflow to pass arguments directly to the script
ENTRYPOINT ["python", "main.py"]