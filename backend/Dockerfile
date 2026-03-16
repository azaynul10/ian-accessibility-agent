FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by Playwright and WebSockets
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 🚨 THE MAGIC FIX FOR CLOUD RUN 🚨
# This installs the Chromium browser and all the complex Linux graphics libraries it needs
RUN pip install playwright
RUN playwright install chromium
RUN playwright install-deps

# Copy backend source code
COPY . .

# Expose port (Cloud Run defaults to 8080)
EXPOSE 8080

# Run the FastAPI server via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
