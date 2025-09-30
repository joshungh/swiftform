#!/usr/bin/env python3
"""
Train OpenAI model using properly paired PDF-to-XF Schema data
This creates a highly accurate model that learns your specific mappings
"""

import os
import json
import PyPDF2
from pathlib import Path
from typing import List, Dict, Any
from services.openai_trainer import OpenAITrainer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def extract_pdf_text(pdf_path: str, max_chars: int = 3000) -> str:
    """Extract text from PDF for training - limited to prevent token overflow"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for i, page in enumerate(pdf_reader.pages):
                if i < 2:  # Only first 2 pages to keep tokens low
                    page_text = page.extract_text()
                    text += f"\n--- PAGE {i+1} ---\n{page_text}"

                if len(text) > max_chars:
                    text = text[:max_chars] + "..."
                    break
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text


def create_training_examples() -> List[Dict[str, Any]]:
    """Create training examples from paired PDFs and schemas"""

    training_dir = Path("training_pairs")
    mappings_file = training_dir / "mappings.json"

    if not mappings_file.exists():
        print("❌ No training pairs found! Run setup_training_pairs.py first.")
        return []

    with open(mappings_file, 'r') as f:
        mappings = json.load(f)

    training_examples = []

    for pair in mappings["pairs"]:
        pdf_path = training_dir / "pdfs" / pair["pdf"]
        schema_path = training_dir / "schemas" / pair["schema"]

        if not pdf_path.exists() or not schema_path.exists():
            print(f"⚠️ Missing files for pair: {pair['name']}")
            continue

        # Extract PDF text
        pdf_text = extract_pdf_text(str(pdf_path))

        # Load schema
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        # Create training example
        system_prompt = """You are an expert form parser specializing in converting PDF documents into XF schemas.
You understand the specific field mapping patterns used by SwiftForm AI.
Key principles:
1. Extract ALL fields visible in the PDF
2. Use exact xf:* element types that match the data type
3. Organize fields into logical pages and groups
4. Include proper validation rules and prepopulation hints
5. Use composite:deficiencies for deficiency tracking when applicable
6. Return ONLY the JSON schema, no explanations"""

        user_prompt = f"""Convert this PDF form into an XF schema.

PDF Content:
{pdf_text}

Generate the complete XF schema for this form following our standard patterns."""

        assistant_response = json.dumps(schema, indent=2)

        training_example = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_response}
            ]
        }

        training_examples.append(training_example)
        print(f"✓ Created training example for: {pair['name']}")

    return training_examples


def main():
    """Main training function"""

    print("=== Training OpenAI Model from PDF-XF Schema Pairs ===\n")

    # Initialize trainer
    try:
        trainer = OpenAITrainer()
        print("✓ OpenAI trainer initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize trainer: {e}")
        print("Make sure OPENAI_API_KEY is set in .env file")
        return

    # Create training examples
    print("Creating training examples from paired data...")
    training_examples = create_training_examples()

    if len(training_examples) < 10:
        print(f"\n⚠️ Only {len(training_examples)} training examples created.")
        print("OpenAI requires at least 10 examples for fine-tuning.")
        print("\nTo add more examples:")
        print("1. Add more PDFs to example-forms/")
        print("2. Run setup_training_pairs.py")
        print("3. Edit the schemas in training_pairs/schemas/")
        print("4. Run this script again")

        if len(training_examples) > 0:
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                return
        else:
            return

    print(f"\n✓ Created {len(training_examples)} training examples")

    # Save training data to JSONL
    training_file = Path("training_pairs/training_data.jsonl")
    with open(training_file, 'w') as f:
        for example in training_examples:
            f.write(json.dumps(example) + '\n')

    print(f"✓ Saved training data to: {training_file}")

    # Show sample of training data
    if training_examples:
        sample = training_examples[0]
        print("\nSample training example:")
        print(f"  System: {sample['messages'][0]['content'][:100]}...")
        print(f"  User: {sample['messages'][1]['content'][:200]}...")
        print(f"  Assistant: (XF Schema with {len(json.loads(sample['messages'][2]['content'])['props']['children'])} pages)")

    # Select model
    print("\n" + "="*50)
    print("Select base model for fine-tuning:")
    print("1. gpt-3.5-turbo (Recommended - Fast & cost-effective)")
    print("2. gpt-4 (Most accurate but slower)")
    print("3. Use existing fine-tuned model as base")

    choice = input("\nEnter choice [1]: ") or "1"

    if choice == "3":
        # List existing models
        existing_models = trainer.get_available_models()
        if existing_models:
            print("\nExisting fine-tuned models:")
            for i, model in enumerate(existing_models, 1):
                print(f"{i}. {model['id']}")
            model_choice = input("Select model number: ")
            try:
                base_model = existing_models[int(model_choice)-1]['id']
            except:
                base_model = "gpt-3.5-turbo"
        else:
            print("No existing fine-tuned models found. Using gpt-3.5-turbo")
            base_model = "gpt-3.5-turbo"
    else:
        base_model = "gpt-4" if choice == "2" else "gpt-3.5-turbo"

    print(f"\nUsing base model: {base_model}")

    # Start training
    print("\nStarting fine-tuning job...")
    result = trainer.train_with_paired_data(
        training_file=str(training_file),
        model_name=base_model
    )

    if result.get("success"):
        print("\n" + "="*50)
        print("✅ TRAINING JOB CREATED SUCCESSFULLY!")
        print("="*50)
        print(f"\nJob ID: {result['job_id']}")
        print(f"Status: {result['status']}")
        print(f"Training examples: {result['training_examples']}")
        print(f"Base model: {result['model']}")

        # Save job info
        job_info = {
            "job_id": result['job_id'],
            "base_model": result['model'],
            "training_examples": result['training_examples'],
            "created_at": result.get('created_at'),
            "training_pairs": len(training_examples),
            "type": "paired_pdf_xf_schema"
        }

        job_file = Path("training_pairs/latest_training_job.json")
        with open(job_file, 'w') as f:
            json.dump(job_info, f, indent=2)

        print(f"\n✓ Job info saved to: {job_file}")

        print("\n" + "="*50)
        print("WHAT HAPPENS NEXT:")
        print("="*50)
        print("\n1. Training will run in the background (20-60 minutes)")
        print("2. Monitor progress at: http://localhost:8000/training-dashboard")
        print("3. Once complete, the model will automatically appear in your upload page")
        print("4. The new model will be specifically trained on YOUR PDF-to-XF mappings")
        print("\nThe trained model will understand:")
        print("  • Your specific field naming conventions")
        print("  • Your preferred XF schema structure")
        print("  • Which fields to extract from similar PDFs")
        print("  • Your validation rules and prepopulation patterns")

    else:
        print("\n❌ Training job failed!")
        if result.get("error"):
            print(f"Error: {result['error']}")
        if result.get("errors"):
            for error in result['errors']:
                print(f"  - {error}")


if __name__ == "__main__":
    main()