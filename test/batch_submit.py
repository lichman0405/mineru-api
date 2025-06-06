# batch_submit.py
# A client script for efficiently submitting a large batch of PDFs for processing.

import os
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import csv

def submit_pdf_task(api_url: str, pdf_path: str) -> dict:
    """
    Submits a single PDF file to the processing service.

    Args:
        api_url: The URL of the API endpoint for processing PDFs.
        pdf_path: The local path to the PDF file.

    Returns:
        A dictionary containing the submission result.
    """
    file_name = os.path.basename(pdf_path)
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (file_name, f, 'application/pdf')}
            response = requests.post(api_url, files=files, timeout=30)

        if response.status_code == 202:
            return {
                "filename": file_name,
                "status": "submitted",
                "task_id": response.json().get("task_id", ""),
                "error": None
            }
        else:
            return {
                "filename": file_name,
                "status": "failed",
                "task_id": None,
                "error": f"API Error: Status {response.status_code} - {response.text}"
            }
    except requests.exceptions.RequestException as e:
        return {
            "filename": file_name,
            "status": "failed",
            "task_id": None,
            "error": f"Network Error: {e}"
        }
    except Exception as e:
        return {
            "filename": file_name,
            "status": "failed",
            "task_id": None,
            "error": f"An unexpected error occurred: {e}"
        }

def main():
    """
    Main function to find PDFs in a directory and submit them concurrently.
    """
    parser = argparse.ArgumentParser(description="Batch submit PDF files to the MinerU analysis service.")
    parser.add_argument("-d", "--directory", required=True, help="The directory containing PDF files to submit.")
    parser.add_argument("-u", "--url", default="http://localhost:8001/process-pdf/", help="The API endpoint URL.")
    parser.add_argument("-w", "--workers", type=int, default=5, help="Number of concurrent submission workers (threads).")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: Directory not found at '{args.directory}'")
        return

    pdf_files = [os.path.join(args.directory, f) for f in os.listdir(args.directory) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in '{args.directory}'.")
        return

    print(f"Found {len(pdf_files)} PDF files. Starting submission with {args.workers} concurrent workers...")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_pdf = {executor.submit(submit_pdf_task, args.url, pdf_path): pdf_path for pdf_path in pdf_files}
        
        for future in tqdm(as_completed(future_to_pdf), total=len(pdf_files), desc="Submitting PDFs"):
            result = future.result()
            results.append(result)

    print("\nSubmission summary:")
    successful_submissions = [r for r in results if r['status'] == 'submitted']
    failed_submissions = [r for r in results if r['status'] == 'failed']

    print(f"  Successfully submitted: {len(successful_submissions)}")
    print(f"  Failed submissions: {len(failed_submissions)}")

    if failed_submissions:
        print("\nDetails of failed submissions:")
        for failure in failed_submissions:
            print(f"  - {failure['filename']}: {failure['error']}")

    log_file = "submission_log.csv"
    print(f"\nSaving detailed submission log to '{log_file}'...")
    with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['filename', 'status', 'task_id', 'error']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Done. You can now use the task IDs in '{log_file}' to check the status or download results later.")

if __name__ == "__main__":
    main()