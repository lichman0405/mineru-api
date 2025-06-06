# Dockerfile (The new robust version)

# 1. Use a lightweight official Python image as a base
FROM python:3.10-slim

# Set environment variables to non-interactive
ENV DEBIAN_FRONTEND=noninteractive

# 2. Install essential system dependencies, inspired by the official Dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    # --- Tools for document processing ---
    libreoffice \
    poppler-utils \
    # --- Essential libraries identified before ---
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    # --- Additional graphics/rendering libraries for safety ---
    libxrender1 \
    libsm6 \
    libxext6 \
    # --- Crucial font packages for CJK and common web fonts ---
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    # 'ttf-mscorefonts-installer' requires accepting a EULA, which is complex in Docker.
    # We will install a close equivalent 'fonts-liberation' which is metric-compatible.
    fonts-liberation \
    fontconfig \
    # --- Clean up ---
    && rm -rf /var/lib/apt/lists/*

# 3. Set the working directory
WORKDIR /app

# 4. Copy and install Python dependencies (no change here)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# 5. Download models (no change here)
RUN wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/scripts/download_models_hf.py -O download_models_hf.py
RUN python download_models_hf.py

# 6. Copy our application code (no change here)
COPY ./app /app/app

# 7. Expose the port (no change here)
EXPOSE 8000

# 8. Define the default command (no change here)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]