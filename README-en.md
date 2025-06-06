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
[![GitHub stars](https://img.shields.io/github/stars/lichman0405/mineru-api.svg?style=social)](https://github.com/lichman0405/mineru-api.git])

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

We recommend using the provided client scripts to interact with the service. This greatly simplifies the process of submitting tasks, polling for status, and downloading results. Please run these scripts on your local machine, not inside a container.

### Option 1: Test a Single File (Recommended for Debugging)

Use the `test_single_file.py` script to perform a complete end-to-end test from submission to downloading the result.

1.  **Install Dependencies**:
    ```bash
    pip install requests
    ```
2.  **Run the Script**:
    ```bash
    # Process test.pdf and download the results to the ./downloaded_results directory
    python test_single_file.py --file ./data/input_pdfs/test.pdf --download-dir ./downloaded_results
    ```
3.  **Check the Output**:
    The script will automatically submit the file, poll for status, and upon successful completion, download a `.zip` archive containing all results into the `./downloaded_results` directory.

### Option 2: Batch Submit Tasks (Recommended for Production)

Use the `batch_submit.py` script to efficiently submit all PDFs from a directory.

1.  **Install Dependencies**:
    ```bash
    pip install requests tqdm
    ```
2.  **Run the Script**:
    ```bash
    # Submit all PDFs from the specified directory using 10 concurrent workers
    python batch_submit.py --directory ./data/input_pdfs/ --workers 10
    ```
3.  **Get Task IDs**:
    After the script finishes, a `submission_log.csv` file will be created in the current directory. This file contains the mapping between each filename and its `task_id`, which you can use for tracking later.

### API Endpoint Reference

If you prefer to build your own client, here are the core API endpoints:

| Method | Path                               | Description                                                  |
| :----- | :--------------------------------- | :----------------------------------------------------------- |
| `POST` | `/process-pdf/`                    | Submits a PDF file and returns a `task_id`.                  |
| `GET`  | `/tasks/status/{task_id}`          | Checks the status and result (if completed) of a specific task. |
| `GET`  | `/tasks/result/download/{task_id}` | Downloads all result files for a task as a `.zip` archive.    |

## 📁 Output Structure

When you download the result `.zip` archive via the API and extract it, you will find a dedicated folder named after the original PDF file, with the following internal structure:

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