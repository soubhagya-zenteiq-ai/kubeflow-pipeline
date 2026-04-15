# Use a Python base image with build tools
FROM python:3.10-slim

# Install build essentials for compiling llama-cpp
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/main.py .

# We don't COPY the .gguf model into the image (it's too big).
# Instead, we will "mount" it from your Ubuntu host into the container.

ENTRYPOINT ["python", "main.py"]