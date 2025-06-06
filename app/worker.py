# The module for the Celery worker that processes PDF files.
# Author: Shibo Li
# Date: 2025-06-06
# Version: 0.1.0

# app/worker.py

import logging
from celery import Celery
from app.logging_config import setup_logging
from app.process_pdf import analyze_pdf

setup_logging()
logger = logging.getLogger(__name__)

redis_url = "redis://redis:6379/0"

celery_app = Celery("tasks", broker=redis_url, backend=redis_url)
celery_app.conf.update(task_track_started=True)

@celery_app.task(bind=True, name="create_pdf_analysis_task")
def create_pdf_analysis_task(self, pdf_path: str, output_dir: str):
    logger.info(f"[TASK ID: {self.request.id}] Task received for PDF: {pdf_path}")
    try:
        return analyze_pdf(pdf_path, output_dir)
    except Exception as e:
        logger.error(f"[TASK ID: {self.request.id}] Task failed spectacularly.", exc_info=True)
        raise e