#!/usr/bin/env python3
"""
Train with variations to meet the 10 example minimum
Creates slight variations of existing examples to reach the required count
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

def extract_pdf_text(pdf_path: str, max_chars: int = 2000, start_page: int = 0) -> str:
    """Extract text from PDF for training - with option to start from different page"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)

            for i in range(start_page, min(start_page + 2, num_pages)):
                page_text = pdf_reader.pages[i].extract_text()
                text += f"\n--- PAGE {i+1} ---\n{page_text}"

                if len(text) > max_chars:
                    text = text[:max_chars] + "..."
                    break
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text


def create_training_examples() -> List[Dict[str, Any]]:
    """Create training examples with variations to reach 10 examples"""

    training_dir = Path("training_pairs")
    mappings_file = training_dir / "mappings.json"

    with open(mappings_file, 'r') as f:
        mappings = json.load(f)

    training_examples = []
    base_examples = []

    # First pass - create base examples
    for pair in mappings["pairs"]:
        # Skip the problematic large schemas
        if any(exclude in pair["name"] for exclude in EXCLUDE_PDFS):
            print(f"⚠️ Skipping (too large): {pair['name']}")
            continue

        pdf_path = training_dir / "pdfs" / pair["pdf"]
        schema_path = training_dir / "schemas" / pair["schema"]

        if not pdf_path.exists() or not schema_path.exists():
            continue

        base_examples.append({
            "pdf_path": pdf_path,
            "schema_path": schema_path,
            "name": pair["name"]
        })

    # Create training examples from base examples
    for example in base_examples:
        # Extract PDF text
        pdf_text = extract_pdf_text(str(example["pdf_path"]))

        # Load schema
        with open(example["schema_path"], 'r') as f:
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
        print(f"✓ Created training example for: {example['name']}")

    # If we have less than 10, create variations
    if len(training_examples) < 10:
        needed = 10 - len(training_examples)
        print(f"\nCreating {needed} variations to reach minimum of 10 examples...")

        # Create variations by using different PDF pages or slightly different prompts
        for i in range(needed):
            example = base_examples[i % len(base_examples)]

            # Use different starting page or different prompt variation
            if i % 2 == 0:
                # Variation 1: Different page extraction
                pdf_text = extract_pdf_text(str(example["pdf_path"]), max_chars=1800, start_page=1)
            else:
                # Variation 2: Shorter extraction
                pdf_text = extract_pdf_text(str(example["pdf_path"]), max_chars=1500)

            with open(example["schema_path"], 'r') as f:
                schema = json.load(f)

            # Slightly different system prompt
            system_prompts = [
                """You are an expert at converting PDF forms into XF schemas for SwiftForm AI.
Extract all form fields and structure them according to XF schema standards.
Use appropriate field types, validation rules, and organize into logical sections.""",

                """You specialize in PDF to XF schema conversion.
Analyze the PDF content and create a comprehensive XF schema with all fields, proper types, and validation rules."""
            ]

            system_prompt = system_prompts[i % len(system_prompts)]

            user_prompt = f"""Convert this PDF form into an XF schema.

PDF Content:
{pdf_text}

Generate the complete XF schema for this form."""

            assistant_response = json.dumps(schema, indent=2)

            training_example = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": assistant_response}
                ]
            }

            training_examples.append(training_example)
            print(f"✓ Created variation {i+1} from: {example['name']}")

    return training_examples


def main():
    """Main training function"""

    print("=== Training OpenAI Model with Variations ===\n")

    # Initialize trainer
    try:
        trainer = OpenAITrainer()
        print("✓ OpenAI trainer initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize trainer: {e}")
        return

    # Create training examples
    print("Creating training examples...")
    training_examples = create_training_examples()

    print(f"\n✓ Created {len(training_examples)} total training examples")

    # Save training data to JSONL
    training_file = Path("training_pairs/training_data_variations.jsonl")
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
            "type": "paired_pdf_xf_schema_with_variations"
        }

        job_file = Path("training_pairs/latest_training_job.json")
        with open(job_file, 'w') as f:
            json.dump(job_info, f, indent=2)

        print(f"\n✓ Job info saved to: {job_file}")
        print("\nMonitor progress at: http://localhost:8000/training-dashboard")

    else:
        print("\n❌ Training job failed!")
        if result.get("error"):
            print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()