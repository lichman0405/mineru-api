# Dockerfile

# 1. Use a lightweight official Python image as a base
FROM python:3.10-slim

# 2. Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 3. Set the working directory
WORKDIR /app

# 4. Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# 5. Download and run the model download script
RUN wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/scripts/download_models_hf.py -O download_models_hf.py
RUN python download_models_hf.py

# 6. Copy our own application code
COPY ./app /app/app

# 7. Expose the port the FastAPI service runs on
EXPOSE 8000

# 8. Define the default command to run
# This is overridden by docker-compose but good practice to have
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]