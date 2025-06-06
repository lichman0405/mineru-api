# test_single_file.py
# A client script to submit a single PDF, poll for status, and download the result.

import requests
import argparse
import time
import json
import os

def download_results(base_url: str, task_id: str, download_dir: str):
    """
    Downloads the ZIP archive for a completed task and saves it to a local directory.
    """
    download_url = f"{base_url.rstrip('/')}/tasks/result/download/{task_id}"
    print(f"\nDownloading results from {download_url} ...")
    
    try:
        # Use stream=True for potentially large files
        with requests.get(download_url, stream=True, timeout=60) as response:
            response.raise_for_status()

            # Get filename from headers, with a fallback
            content_disp = response.headers.get("content-disposition")
            if content_disp and 'filename=' in content_disp:
                filename = content_disp.split('filename=')[1].strip('"')
            else:
                filename = f"task_{task_id}_results.zip"
                
            local_filepath = os.path.join(download_dir, filename)
            
            os.makedirs(download_dir, exist_ok=True)

            with open(local_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✓ Results successfully downloaded to: {local_filepath}")
            return local_filepath

    except requests.exceptions.RequestException as e:
        print(f"Error downloading results: {e}")
        return None


def main():
    """
    Main function to drive the single-file test workflow.
    """
    parser = argparse.ArgumentParser(
        description="Submit a single PDF, wait for completion, and download the results.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-f", "--file", required=True, help="Path to the single PDF file to process.")
    parser.add_argument("-u", "--url", default="http://localhost:8001", help="Base URL of the API service.")
    parser.add_argument("-i", "--interval", type=int, default=3, help="Polling interval in seconds.")
    parser.add_argument("-t", "--timeout", type=int, default=300, help="Task completion timeout in seconds (default: 5 minutes).")
    parser.add_argument("--download-dir", default="./downloaded_results", help="Local directory to save the result ZIP file.")
    
    args = parser.parse_args()

    submit_url = f"{args.url.rstrip('/')}/process-pdf/"
    
    if not os.path.isfile(args.file):
        print(f"Error: File not found at '{args.file}'")
        return

    # Submit the file to the API
    print(f"Submitting '{os.path.basename(args.file)}' to {submit_url} ...")
    try:
        with open(args.file, 'rb') as f:
            files = {'file': (os.path.basename(args.file), f, 'application/pdf')}
            response = requests.post(submit_url, files=files, timeout=30)
        
        response.raise_for_status()

        if response.status_code != 202:
            print(f"Error: API returned an unexpected status code {response.status_code}")
            print(f"Response: {response.text}")
            return
            
        task_id = response.json().get("task_id")
        if not task_id:
            print(f"Error: API response did not include a task_id.")
            print(f"Response: {response.json()}")
            return
        
        print(f"✓ Task submitted successfully. Task ID: {task_id}")

    except requests.exceptions.RequestException as e:
        print(f"Error submitting file: {e}")
        return

    # Polling for task status
    status_url = f"{args.url.rstrip('/')}/tasks/status/{task_id}"
    start_time = time.time()
    
    print(f"\nPolling for status every {args.interval} seconds (timeout in {args.timeout}s)...")
    final_status = None
    
    while time.time() - start_time < args.timeout:
        try:
            response = requests.get(status_url, timeout=10)
            response.raise_for_status()
            
            status_data = response.json()
            final_status = status_data.get("status")
            
            print(f"  - Status: {final_status}")
            
            if final_status in ["SUCCESS", "FAILURE"]:
                break

            time.sleep(args.interval)
        except requests.exceptions.RequestException as e:
            print(f"Error polling status: {e}. Retrying...")
            time.sleep(args.interval)
    else: # This else belongs to the while loop, executes if loop finishes without break
        print(f"\n[TIMEOUT] Task did not complete within the {args.timeout} second timeout.")
        return

    # Check final status
    if final_status == "SUCCESS":
        print("\n[SUCCESS] Task completed. Preparing to download results...")
        download_results(args.url, task_id, args.download_dir)
    elif final_status == "FAILURE":
        print("\n[FAILURE] Task failed. Check server logs for details.")
        print("Error Details from API:", json.dumps(response.json().get("result"), indent=2))

if __name__ == "__main__":
    main()