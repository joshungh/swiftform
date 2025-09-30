#!/usr/bin/env python3
"""
Train with a subset of examples, excluding the ones that are too large
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

# Examples to exclude (these have schemas that are too large)
EXCLUDE_PDFS = [
    "CommercialIndustrial Inspection",
    "DOT CEM-2030SW"
]

def extract_pdf_text(pdf_path: str, max_chars: int = 2500) -> str:
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
    """Create training examples from paired PDFs and schemas, excluding large ones"""

    training_dir = Path("training_pairs")
    mappings_file = training_dir / "mappings.json"

    if not mappings_file.exists():
        print("❌ No training pairs found! Run setup_training_pairs.py first.")
        return []

    with open(mappings_file, 'r') as f:
        mappings = json.load(f)

    training_examples = []
    skipped = []

    for pair in mappings["pairs"]:
        # Skip the problematic large schemas
        if any(exclude in pair["name"] for exclude in EXCLUDE_PDFS):
            skipped.append(pair["name"])
            print(f"⚠️ Skipping (too large): {pair['name']}")
            continue

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

    if skipped:
        print(f"\n⚠️ Skipped {len(skipped)} examples due to size constraints")

    return training_examples


def main():
    """Main training function"""

    print("=== Training OpenAI Model (Subset) ===\n")
    print("This will exclude forms with very large schemas that exceed token limits.\n")

    # Initialize trainer
    try:
        trainer = OpenAITrainer()
        print("✓ OpenAI trainer initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize trainer: {e}")
        return

    # Create training examples
    print("Creating training examples from paired data...")
    training_examples = create_training_examples()

    print(f"\n✓ Created {len(training_examples)} training examples")

    if len(training_examples) < 10:
        print(f"\n⚠️ Only {len(training_examples)} examples available.")
        print("Note: OpenAI requires at least 10 examples, but we'll proceed with fewer.")

    # Save training data to JSONL
    training_file = Path("training_pairs/training_data_subset.jsonl")
    with open(training_file, 'w') as f:
        for example in training_examples:
            f.write(json.dumps(example) + '\n')

    print(f"✓ Saved training data to: {training_file}")

    # Use gpt-3.5-turbo
    base_model = "gpt-3.5-turbo"
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
            "type": "paired_pdf_xf_schema_subset",
            "excluded": EXCLUDE_PDFS
        }

        job_file = Path("training_pairs/latest_training_job_subset.json")
        with open(job_file, 'w') as f:
            json.dump(job_info, f, indent=2)

        print(f"\n✓ Job info saved to: {job_file}")
        print("\n" + "="*50)
        print("NOTE: This model is trained on 8 forms (excluding 2 very large ones)")
        print("It will still work well for most forms!")
        print("="*50)

    else:
        print("\n❌ Training job failed!")
        if result.get("error"):
            print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()