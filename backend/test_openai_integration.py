"""
Test script for OpenAI integration with SwiftformAI
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.openai_trainer import OpenAITrainer
from services.ai_form_parser import AIFormParser

# Load environment variables
load_dotenv()


def test_openai_connection():
    """Test basic OpenAI API connection"""
    print("Testing OpenAI API connection...")

    try:
        trainer = OpenAITrainer()
        print("✓ OpenAI trainer initialized successfully")

        # Test API connection by listing models
        models = trainer.get_available_models()
        print(f"✓ Connected to OpenAI API")
        print(f"  Found {len(models)} fine-tuned models")

        return True
    except Exception as e:
        print(f"✗ Failed to connect to OpenAI: {str(e)}")
        return False


def test_form_parser():
    """Test OpenAI-powered form parser"""
    print("\nTesting OpenAI Form Parser...")

    try:
        parser = AIFormParser(provider="openai")
        print("✓ Form parser initialized with OpenAI")

        # Create a simple test document
        test_text = """
        INSPECTION FORM

        Date: _______________
        Inspector Name: _______________
        Location: _______________

        Checklist:
        [ ] Equipment functional
        [ ] Safety protocols followed
        [ ] Documentation complete

        Comments: _______________
        """

        prompt = parser.create_extraction_prompt(test_text)
        print("✓ Created extraction prompt")

        # Test parsing (this will actually call OpenAI API)
        print("  Parsing test document...")
        schema = parser.parse_with_openai(prompt)

        if schema and "name" in schema:
            print("✓ Successfully extracted form schema")
            print(f"  Form type: {schema.get('name')}")
            return True
        else:
            print("✗ Failed to extract valid schema")
            return False

    except Exception as e:
        print(f"✗ Form parser test failed: {str(e)}")
        return False


def test_training_data_preparation():
    """Test training data preparation"""
    print("\nTesting Training Data Preparation...")

    try:
        trainer = OpenAITrainer()

        # Create sample form data
        sample_forms = [
            {
                "document_text": "Sample form 1 with fields",
                "extracted_schema": {
                    "name": "xf:form",
                    "props": {
                        "children": []
                    }
                }
            },
            {
                "document_text": "Sample form 2 with different fields",
                "extracted_schema": {
                    "name": "xf:form",
                    "props": {
                        "children": []
                    }
                }
            }
        ]

        # Prepare training data
        training_data = trainer.prepare_training_data(sample_forms)
        print(f"✓ Prepared {len(training_data)} training examples")

        # Validate training data
        is_valid, errors = trainer.validate_training_data(training_data)

        if is_valid:
            print("✓ Training data validation passed")
        else:
            print(f"⚠ Training data validation failed: {errors}")
            # This is expected with only 2 samples (minimum is 10)

        return True

    except Exception as e:
        print(f"✗ Training data preparation failed: {str(e)}")
        return False


def test_api_endpoints():
    """Test if API endpoints are accessible"""
    print("\nTesting API Endpoints...")

    try:
        import requests

        # Check if server is running
        base_url = "http://localhost:8000"

        endpoints = [
            "/health",
            "/api/training/models",
            "/docs"
        ]

        server_running = False

        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=2)
                if response.status_code in [200, 422]:  # 422 for endpoints requiring params
                    print(f"✓ Endpoint {endpoint} is accessible")
                    server_running = True
                else:
                    print(f"⚠ Endpoint {endpoint} returned status {response.status_code}")
            except requests.exceptions.ConnectionError:
                if not server_running:
                    print(f"⚠ Server not running. Start with: uvicorn app.main_simple:app --reload")
                    break
            except Exception as e:
                print(f"⚠ Could not reach {endpoint}: {str(e)}")

        return server_running

    except ImportError:
        print("⚠ requests library not installed. Skipping endpoint tests.")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("SwiftformAI OpenAI Integration Test Suite")
    print("=" * 50)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("✗ OPENAI_API_KEY not found in environment variables")
        print("  Please set it in your .env file")
        return

    if api_key.startswith("sk-"):
        print(f"✓ OpenAI API key found (starts with sk-...)")
    else:
        print("⚠ API key format might be incorrect")

    # Run tests
    tests = [
        ("OpenAI Connection", test_openai_connection),
        ("Form Parser", test_form_parser),
        ("Training Data", test_training_data_preparation),
        ("API Endpoints", test_api_endpoints)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"✗ {test_name} crashed: {str(e)}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("=" * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! OpenAI integration is working correctly.")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()