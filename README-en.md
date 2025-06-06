<div align="center">
  <a href="https://github.com/lichman0405/mineru-api.git">
    <img src="/assets/edit_logo.png" alt="Logo" width="150px">
  </a>
  
  <h1 align="center">MinerU PDF Intelligent Parsing Service</h1>
  
  <p align="center">
    A powerful, scalable PDF parsing API service built with MinerU, FastAPI, and Celery.
    <br>
    <a href="./README.md"><strong>中文</strong></a>
    ·
    <a href="https://github.com/lichman0405/mineru-api.git/issues">Report Bug</a>
    ·
    <a href="https://github.com/lichman0405/mineru-api.git/issues">Request Feature</a>
  </p>
</div>

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi)
![Celery](https://img.shields.io/badge/Celery-3778AF?style=flat&logo=celery)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker)
[![GitHub issues](https://img.shields.io/github/issues/lichman0405/mineru-api.svg)](https://github.com/lichman0405/mineru-api/issues)
[![GitHub stars](https://img.shields.io/github/stars/lichman0405/mineru-api.git.svg?style=social)](https://github.com/lichman0405/mineru-api.git])

</div>

---

## 📖 About The Project

This project is a powerful PDF document parsing service. It leverages the core capabilities of [MinerU](https://github.com/opendatalab/MinerU) to deeply analyze PDF files, extract elements like text, tables, and images, and convert them into structured Markdown and JSON formats.
Note that GPU support has not yet been added to MinerU here.

If you are interested in the project, please fork and star the original [MinerU](https://github.com/opendatalab/MinerU) project.

The service uses an asynchronous architecture, receiving requests via FastAPI and utilizing Celery and Redis to build a distributed task queue, ensuring stability and high performance under high concurrency and when processing large files. The entire service is fully containerized and can be deployed with a single command using Docker Compose.

### ✨ Key Features

*   **PDF to Markdown**: High-quality conversion of PDF content (including text and images) to Markdown format.
*   **PDF to JSON**: Extracts document content and outputs it in two structured JSON formats for easy programmatic processing.
*   **OCR Support**: Automatically detects scanned PDFs and invokes OCR to extract text.
*   **Asynchronous Processing**: Celery-based task queue allows the API to respond immediately while time-consuming tasks are processed in the background.
*   **Logging System**: Outputs to both a beautified console and persistent files for easy debugging and tracking.
*   **Containerized Deployment**: Uses Docker and Docker Compose for one-click startup and environment isolation.
*   **Scalable Architecture**: Web service and computational tasks are decoupled, allowing Celery Workers to be scaled independently to handle high loads.

### 🏗️ System Architecture

The service adopts a classic M-M-W (Master-MessageQueue-Worker) pattern, consisting of three core containers:
1.  **FastAPI Web App**: Acts as the Master, receives PDF files uploaded by users, creates parsing tasks, pushes them to the Redis queue, and then immediately returns a task ID.
2.  **Redis**: Serves as the message broker, storing the queue of pending tasks, and as the backend to store task results.
3.  **Celery Worker**: Acts as the Worker, fetches tasks from the Redis queue, calls the `magic-pdf` library to perform the heavy PDF parsing work, and writes the results back to Redis.

## 🚀 Getting Started

### 📋 Prerequisites

Before you begin, ensure your system has the following software installed:
*   [Docker](https://www.docker.com/get-started)
*   [Docker Compose](https://docs.docker.com/compose/install/) (Usually installed with Docker Desktop)

### ⚙️ Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/lichman0405/mineru-api.git
    cd mineru-api
    ```

2.  **Create data directories**
    The service requires a `data` directory to store input, output, and log files. Please execute the following in the project root directory:
    ```bash
    mkdir -p data/input_pdfs data/output data/logs
    ```

3.  **Prepare test files**
    Place one or more PDF files you want to test into the `./data/input_pdfs/` directory.

4.  **Build and start the services**
    Use Docker Compose to build and start all services (Web App, Worker, Redis) with a single command.
    ```bash
    docker-compose up --build -d
    ```
    The `-d` flag runs the services in detached mode (in the background). You can view real-time logs using `docker-compose logs -f`.

## 🕹️ Usage

Once the service is running, you can interact with it through its API endpoints.

### 1. Submit PDF Processing Task

Send a `POST` request to the `/process-pdf/` endpoint to upload and submit a PDF file.

-   **Example (`curl`)**:
    (Please replace `my_document.pdf` with your own filename and `localhost:8001` with the IP address of the host where you deployed the service)
    ```bash
    curl -X POST -F "file=@./data/input_pdfs/my_document.pdf" http://localhost:8001/process-pdf/
    ```

-   **Successful Response**:
    The service will immediately accept the task and return a `task ID` with a `202 Accepted` status code.

    ```JSON
    {
    "task_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "status_url": "/tasks/status/a1b2c3d4-e5f6-7890-abcd-1234567890ab"
    }
    ```

### 2. Check Task Status and Results
Use the `task_id` obtained in the previous step to send a `GET` request to the `/tasks/status/{task_id}` endpoint to check the task status.

-   **Example (`curl`)**:

```Bash
curl http://localhost:8001/tasks/status/a1b2c3d4-e5f6-7890-abcd-1234567890ab
```

-   **Possible Responses**:

    -   Processing:
    ```JSON
    {
    "task_id": "...",
    "status": "PENDING",
    "result": null
    }
    ```
    -   Successfully processed:
    ```JSON
    {
      "task_id": "...",
      "status": "SUCCESS",
      "result": {
        "status": "success",
        "input_file": "/app/data/input_pdfs/my_document.pdf",
        "analysis_mode": "Text",
        "output_directory": "/app/data/output/my_document",
        "generated_files": { ... }
      }
    }
    ```

## 📁 Output Structure
All processing results will be saved in the `./data/output/` directory on your host machine, under a dedicated subdirectory named after the original PDF file.
```bash
data/output/
└── my_document/
    ├── my_document.md
    ├── my_document_content_list.json
    ├── my_document_middle.json
    ├── my_document_layout.pdf
    └── images/
        └── ...
```
## 📝 License
This project is licensed under the MIT License. See the LICENSE file for details.

## ✍️ Author (Engineering)
Shibo Li