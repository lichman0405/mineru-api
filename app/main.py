# The model for processing PDF files, analyzing them, and generating output files.
# Author: Shibo Li
# Date: 2025-06-06
# Version: 0.1.0


import os
import shutil
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from celery.result import AsyncResult
from app.worker import create_pdf_analysis_task, celery_app
from app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

CONTAINER_INPUT_DIR = "/app/data/input_pdfs"
CONTAINER_OUTPUT_DIR = "/app/data/output"  

app = FastAPI(
    title="Magic PDF Analysis Service with Celery",
    description="An API to submit PDF analysis tasks and check their status.",
    version="3.0.0" 
)

@app.post("/process-pdf/", status_code=202, summary="Submit a PDF for processing")
def submit_pdf_processing(file: UploadFile = File(..., description="The PDF file to be processed.")):
    """
    Submit a PDF file for processing. The file will be saved to a specific directory,
    and a Celery task will be created to analyze the PDF.
    Args:
        file (UploadFile): The PDF file to be processed.
    Returns:
        dict: A dictionary containing the task ID and a URL to check the task status.
    Raises:
        HTTPException: If the file is not a valid PDF or if there is an error saving the file."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are accepted.")

    # --- Start of modifications ---
    # 1. Prepare paths
    input_pdf_path = os.path.join(CONTAINER_INPUT_DIR, str(file.filename))
    name_without_ext = os.path.splitext(str(file.filename))[0]
    # Create a unique output directory for this specific task
    task_output_dir = os.path.join(CONTAINER_OUTPUT_DIR, name_without_ext)
    os.makedirs(task_output_dir, exist_ok=True)
    # --- End of modifications ---

    try:
        with open(input_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Received and saved file to: {input_pdf_path}")
    except Exception as e:
        logger.error(f"Error saving file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")
    finally:
        file.file.close()

    # Pass the new single output directory to the Celery task
    task = create_pdf_analysis_task.delay(
        pdf_path=input_pdf_path,
        output_dir=task_output_dir 
    )
    logger.info(f"Submitted task {task.id} for file '{file.filename}'. Output will be in '{task_output_dir}'")
    
    return {"task_id": task.id, "status_url": f"/tasks/status/{task.id}"}


@app.get("/tasks/status/{task_id}", summary="Check the status of a task")
def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
    if task_result.failed():
        response["result"] = str(task_result.info)
    return response