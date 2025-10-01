#!/usr/bin/env python3
"""
Test script to verify the upload endpoint is working
"""
import requests
import sys
import os

def test_upload_endpoint():
    """Test the /api/upload endpoint with a sample PDF"""
    url = "http://localhost:8000/api/upload"

    # Find a sample PDF in the uploads directory
    uploads_dir = "uploads"
    pdf_files = []

    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            if file.endswith('.pdf'):
                pdf_files.append(os.path.join(uploads_dir, file))

    if not pdf_files:
        print("❌ No PDF files found in uploads/ directory")
        print("Please place a test PDF file in the uploads/ directory")
        return False

    test_pdf = pdf_files[0]
    print(f"📄 Testing with PDF: {test_pdf}")

    try:
        with open(test_pdf, 'rb') as f:
            files = {'file': (os.path.basename(test_pdf), f, 'application/pdf')}
            print(f"📤 Uploading to {url}...")

            response = requests.post(url, files=files, timeout=120)

            print(f"\n📊 Response Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Upload successful!")
                print(f"   File ID: {data.get('file_id')}")
                print(f"   Filename: {data.get('filename')}")
                print(f"   Status: {data.get('status')}")

                if data.get('xf_schema'):
                    print(f"   ✅ XF Schema generated!")
                    schema = data['xf_schema']
                    if isinstance(schema, dict):
                        print(f"   Schema name: {schema.get('name')}")
                        children = schema.get('props', {}).get('children', [])
                        print(f"   Number of pages: {len(children)}")
                else:
                    print(f"   ⚠️  No XF Schema in response")

                return True
            else:
                print(f"❌ Upload failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out (took more than 120 seconds)")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_health_endpoint():
    """Test the /health endpoint"""
    url = "http://localhost:8000/health"

    try:
        print(f"🏥 Testing health endpoint: {url}")
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            print(f"✅ Server is healthy: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach server: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing SwiftForm API Endpoints\n")
    print("=" * 50)

    # Test health first
    if not test_health_endpoint():
        print("\n❌ Server is not running or not reachable")
        sys.exit(1)

    print("\n" + "=" * 50 + "\n")

    # Test upload
    if test_upload_endpoint():
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Upload test failed")
        sys.exit(1)
