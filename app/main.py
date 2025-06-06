# The model for processing PDF files, analyzing them, and generating output files.
# Author: Shibo Li
# Date: 2025-06-06
# Version: 0.1.0


import os
import shutil
import logging
import io
import zipfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from celery.result import AsyncResult
from app.worker import create_pdf_analysis_task, celery_app
from app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

CONTAINER_INPUT_DIR = "/app/data/input_pdfs"
CONTAINER_OUTPUT_DIR = "/app/data/output"

app = FastAPI(
    title="Magic PDF Analysis Service with Celery",
    description="An API to submit PDF analysis tasks, check their status, and download results.",
    version="4.0.0"
)

@app.post("/process-pdf/", status_code=202, summary="Submit a PDF for processing")
def submit_pdf_processing(file: UploadFile = File(..., description="The PDF file to be processed.")):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are accepted.")

    name_without_ext = os.path.splitext(str(file.filename))[0]
    task_output_dir = os.path.join(CONTAINER_OUTPUT_DIR, name_without_ext)
    os.makedirs(task_output_dir, exist_ok=True)
    
    input_pdf_path = os.path.join(CONTAINER_INPUT_DIR, str(file.filename))
    try:
        with open(input_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Received and saved file to: {input_pdf_path}")
    except Exception as e:
        logger.error(f"Error saving file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")
    finally:
        file.file.close()

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

@app.get("/tasks/result/download/{task_id}", summary="Download the results of a completed task")
def download_task_result(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)

    if not task_result.ready():
        raise HTTPException(status_code=409, detail="Task is still processing. Please wait.")
    if task_result.failed():
        raise HTTPException(status_code=404, detail="Task failed and has no result to download.")
    
    result_data = task_result.result
    output_dir = result_data.get("output_directory")

    if not output_dir or not os.path.isdir(output_dir):
        logger.error(f"Output directory not found for task {task_id}: {output_dir}")
        raise HTTPException(status_code=404, detail="Result directory not found.")
    
    zip_io = io.BytesIO()
    dir_name = os.path.basename(output_dir)

    with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                archive_path = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname=os.path.join(dir_name, archive_path))
    
    zip_io.seek(0)
    
    return StreamingResponse(
        zip_io,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=results_{dir_name}.zip"}
    )