# 1. Use an official lightweight Python image as a base
FROM python:3.10-slim

# 2. Install system dependencies. wget is for downloading model scripts, libgl1 is a dependency for many CV/PDF libraries.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 3. Set the working directory
WORKDIR /app

# 4. Copy the dependency manifest and install Python packages.
#    Copying this file first and installing allows leveraging Docker's layer caching.
#    This layer won't be rebuilt as long as requirements.txt doesn't change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i

# 5. Download and run the model download script.
#    This step can be time-consuming but also benefits from Docker caching.
#    It won't re-execute if the previous step hasn't changed.
RUN wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/scripts/download_models_hf.py -O download_models_hf.py
RUN python download_models_hf.py

# 6. Copy our application code.
#    Placing this step last means only this layer needs to be rebuilt when our code changes,
#    speeding up development iterations without reinstalling dependencies or redownloading models.
COPY ./app /app/app

# 7. Expose the port FastAPI will run on
EXPOSE 8000

# 8. Define the command to run when the container starts.
#    Start the uvicorn server, listening on all network interfaces (0.0.0.0).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]