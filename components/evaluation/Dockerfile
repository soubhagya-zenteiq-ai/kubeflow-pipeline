FROM python:3.9-slim

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/main.py .

ENTRYPOINT ["python", "main.py"]