#!/usr/bin/env python3
"""
Batch training script for SwiftformAI
Automatically uploads all PDFs from example-forms directory for training
"""

import os
import sys
import glob
import requests
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
EXAMPLES_DIR = "example-forms"
MODEL_NAME = "gpt-3.5-turbo"


def check_server():
    """Check if the FastAPI server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✓ Server is running")
            return True
    except:
        pass

    print("✗ Server is not running")
    print("  Start it with: uvicorn app.main_simple:app --reload")
    return False


def count_pdf_files():
    """Count PDF files in the examples directory"""
    pdf_files = glob.glob(os.path.join(EXAMPLES_DIR, "*.pdf"))
    return len(pdf_files), pdf_files


def upload_forms_for_training(pdf_files):
    """Upload PDF files for training"""
    print(f"\nUploading {len(pdf_files)} PDF files for training...")

    # Prepare files for upload
    files = []
    for pdf_path in pdf_files:
        files.append(('files', (os.path.basename(pdf_path), open(pdf_path, 'rb'), 'application/pdf')))

    # Add model name to the request
    data = {'model_name': MODEL_NAME}

    try:
        # Send request
        response = requests.post(
            f"{API_BASE_URL}/api/training/upload-forms",
            files=files,
            data=data
        )

        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("\n✓ Training job started successfully!")
                print(f"  Job ID: {result.get('job_id')}")
                print(f"  Training examples: {result.get('training_examples')}")
                print(f"  Model: {result.get('model_base')}")
                return result.get('job_id')
            else:
                print(f"\n✗ Training failed: {result.get('error')}")
                if result.get('errors'):
                    for error in result['errors']:
                        print(f"  - {error}")
        else:
            print(f"\n✗ Upload failed with status {response.status_code}")
            print(f"  Response: {response.text}")

    except Exception as e:
        print(f"\n✗ Failed to upload forms: {str(e)}")

    return None


def monitor_training(job_id):
    """Monitor training job status"""
    if not job_id:
        return

    print(f"\nMonitoring training job: {job_id}")
    print("Check status with:")
    print(f"  curl {API_BASE_URL}/api/training/status/{job_id}")
    print("\nOr visit:")
    print(f"  {API_BASE_URL}/docs#/training/get_training_status_api_training_status__job_id__get")


def main():
    """Main training workflow"""
    print("=" * 50)
    print("SwiftformAI Batch Training Script")
    print("=" * 50)

    # Check server
    if not check_server():
        sys.exit(1)

    # Count PDF files
    count, pdf_files = count_pdf_files()

    print(f"\nFound {count} PDF files in {EXAMPLES_DIR}/")

    if count == 0:
        print("\n✗ No PDF files found!")
        print(f"  Add PDF forms to: {os.path.abspath(EXAMPLES_DIR)}/")
        sys.exit(1)

    if count < 10:
        print(f"\n⚠ Warning: Only {count} PDF files found")
        print("  OpenAI requires minimum 10 examples for fine-tuning")
        print(f"  Add more PDFs to: {os.path.abspath(EXAMPLES_DIR)}/")

        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)

    # List files
    print("\nFiles to be processed:")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"  {i}. {os.path.basename(pdf)}")

    # Confirm
    response = input(f"\nTrain model with these {count} forms? (y/n): ")
    if response.lower() != 'y':
        print("Training cancelled")
        sys.exit(0)

    # Upload and train
    job_id = upload_forms_for_training(pdf_files)

    # Monitor
    monitor_training(job_id)

    print("\n" + "=" * 50)
    print("Training process initiated!")
    print("=" * 50)

    if job_id:
        print("\nNext steps:")
        print("1. Monitor training progress (usually takes 1-3 hours)")
        print("2. Once complete, test the model using the API")
        print("3. Use the fine-tuned model for better form parsing")

        print("\nUseful commands:")
        print(f"  # Check status")
        print(f"  curl {API_BASE_URL}/api/training/status/{job_id}")
        print(f"  ")
        print(f"  # List available models")
        print(f"  curl {API_BASE_URL}/api/training/models")
        print(f"  ")
        print(f"  # View training history")
        print(f"  curl {API_BASE_URL}/api/training/training-history")


if __name__ == "__main__":
    main()