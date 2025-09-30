#!/usr/bin/env python3
"""
Script to train OpenAI model with paired PDF-to-XF schema data
This creates a more accurate fine-tuned model that understands the mapping
"""

import os
import sys
import json
from pathlib import Path
from services.openai_trainer import OpenAITrainer
from services.training_data_manager import TrainingDataManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Main function to train with paired data"""

    print("=== OpenAI Model Training with Paired Data ===\n")

    # Initialize trainer
    try:
        trainer = OpenAITrainer()
        print("✓ OpenAI trainer initialized\n")
    except Exception as e:
        print(f"✗ Failed to initialize OpenAI trainer: {e}")
        print("Make sure your OPENAI_API_KEY is set in the .env file")
        return

    # Check for training data
    training_file = Path("training_data/training_data.jsonl")

    if not training_file.exists():
        print("✗ Training data file not found!")
        print("Please run 'python prepare_training_data.py' first to create training pairs")
        return

    # Load and display training data info
    training_examples = []
    with open(training_file, 'r') as f:
        for line in f:
            training_examples.append(json.loads(line))

    print(f"Found {len(training_examples)} training examples")

    if len(training_examples) < 10:
        print(f"⚠️ Warning: Only {len(training_examples)} examples found. OpenAI requires at least 10.")
        print("Add more PDFs to example-forms/ and run prepare_training_data.py again")

        # Ask if user wants to continue anyway
        response = input("\nDo you want to continue with training? (y/n): ")
        if response.lower() != 'y':
            return

    # Display sample training data
    print("\nSample training data:")
    sample = training_examples[0] if training_examples else {}
    if sample:
        messages = sample.get("messages", [])
        for msg in messages[:2]:  # Show system and user messages
            role = msg.get("role", "")
            content = msg.get("content", "")[:200] + "..." if len(msg.get("content", "")) > 200 else msg.get("content", "")
            print(f"  {role}: {content}")
    print()

    # Select base model
    print("Select base model for fine-tuning:")
    print("1. gpt-3.5-turbo (Recommended - Fast and cost-effective)")
    print("2. gpt-4 (More capable but slower)")
    print("3. gpt-4-turbo-preview (Latest GPT-4)")

    choice = input("\nEnter choice (1-3) [default: 1]: ") or "1"

    model_map = {
        "1": "gpt-3.5-turbo",
        "2": "gpt-4",
        "3": "gpt-4-turbo-preview"
    }

    base_model = model_map.get(choice, "gpt-3.5-turbo")
    print(f"\nUsing base model: {base_model}\n")

    # Start training
    print("Starting fine-tuning job...")
    result = trainer.train_with_paired_data(
        training_file=str(training_file),
        model_name=base_model
    )

    if result.get("success"):
        print("\n✓ Training job created successfully!")
        print(f"  Job ID: {result['job_id']}")
        print(f"  Status: {result['status']}")
        print(f"  Training examples: {result['training_examples']}")
        print(f"  Base model: {result['model']}")
        print(f"  Training file: {result['training_file']}")

        print("\n" + "="*50)
        print("Training has started! The job will run in the background.")
        print("This typically takes 20-60 minutes depending on data size.")
        print("\nYou can monitor progress by:")
        print("1. Running: python check_training_status.py")
        print("2. Visiting: http://localhost:8000/training-dashboard")
        print("3. Using the OpenAI dashboard: https://platform.openai.com/finetune")

        # Save job ID for monitoring
        job_info = {
            "job_id": result['job_id'],
            "base_model": result['model'],
            "training_examples": result['training_examples'],
            "created_at": result.get('created_at')
        }

        with open("training_data/latest_job.json", "w") as f:
            json.dump(job_info, f, indent=2)

        print(f"\nJob info saved to: training_data/latest_job.json")

    else:
        print("\n✗ Training job failed!")
        if result.get("errors"):
            print("Validation errors:")
            for error in result['errors']:
                print(f"  - {error}")
        elif result.get("error"):
            print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()