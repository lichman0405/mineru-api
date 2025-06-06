# batch_download.py
# A client script to read a submission log and download all completed task results.

import requests
import argparse
import time
import os
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def check_and_download(base_url: str, task_id: str, download_dir: str) -> dict:
    """
    Checks the status of a task, and if successful, downloads the result.

    Args:
        base_url: The base URL of the API service.
        task_id: The ID of the task to check and download.
        download_dir: The local directory to save the downloaded file.

    Returns:
        A dictionary summarizing the outcome for this task.
    """
    status_url = f"{base_url.rstrip('/')}/tasks/status/{task_id}"
    download_url = f"{base_url.rstrip('/')}/tasks/result/download/{task_id}"
    
    try:
        # Step 1: Check status first
        response = requests.get(status_url, timeout=10)
        response.raise_for_status()
        status = response.json().get("status")

        if status != "SUCCESS":
            return {"task_id": task_id, "status": status, "file": None, "error": f"Task not successful (status: {status})."}

        # Step 2: If successful, proceed to download
        with requests.get(download_url, stream=True, timeout=180) as r_download:
            r_download.raise_for_status()
            
            content_disp = r_download.headers.get("content-disposition")
            if content_disp and 'filename=' in content_disp:
                filename = content_disp.split('filename=')[1].strip('"')
            else:
                filename = f"task_{task_id}_results.zip"
            
            local_filepath = os.path.join(download_dir, filename)
            os.makedirs(download_dir, exist_ok=True)

            with open(local_filepath, 'wb') as f:
                for chunk in r_download.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return {"task_id": task_id, "status": "DOWNLOADED", "file": local_filepath, "error": None}

    except requests.exceptions.RequestException as e:
        return {"task_id": task_id, "status": "ERROR", "file": None, "error": f"Network error: {e}"}
    except Exception as e:
        return {"task_id": task_id, "status": "ERROR", "file": None, "error": f"An unexpected error occurred: {e}"}


def main():
    """
    Main function to read a CSV, and concurrently download results.
    """
    parser = argparse.ArgumentParser(description="Batch download results from a submission log CSV.")
    parser.add_argument(
        "-c", "--csv-file",
        default="submission_log.csv",
        help="The submission log file containing task IDs."
    )
    parser.add_argument(
        "-u", "--url",
        default="http://localhost:8001",
        help="The base URL of the API service."
    )
    parser.add_argument(
        "-d", "--download-dir",
        default="./batch_results",
        help="Local directory to save the downloaded result ZIP files."
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=5,
        help="Number of concurrent download workers (threads)."
    )
    args = parser.parse_args()

    if not os.path.isfile(args.csv_file):
        print(f"Error: CSV log file not found at '{args.csv_file}'")
        return

    tasks_to_process = []
    with open(args.csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("status") == "submitted" and row.get("task_id"):
                tasks_to_process.append(row["task_id"])

    if not tasks_to_process:
        print("No submitted tasks found in the CSV file to process.")
        return

    print(f"Found {len(tasks_to_process)} submitted tasks. Starting download process with {args.workers} workers...")
    
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_task = {executor.submit(check_and_download, args.url, task_id, args.download_dir): task_id for task_id in tasks_to_process}
        
        for future in tqdm(as_completed(future_to_task), total=len(tasks_to_process), desc="Downloading Results"):
            result = future.result()
            results.append(result)

    print("\nDownload summary:")
    successful_downloads = [r for r in results if r['status'] == 'DOWNLOADED']
    other_statuses = [r for r in results if r['status'] != 'DOWNLOADED']

    print(f"  Successfully downloaded: {len(successful_downloads)}")
    print(f"  Not downloaded (pending, failed, or error): {len(other_statuses)}")

    if other_statuses:
        print("\nDetails for tasks not downloaded:")
        for res in other_statuses:
            print(f"  - Task ID {res['task_id']}: {res['error']}")

    print("\nBatch download process finished.")


if __name__ == "__main__":
    main()