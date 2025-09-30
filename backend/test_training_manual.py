#!/usr/bin/env python3
"""Test script to manually trigger training with small dataset"""

import sys
sys.path.insert(0, '/Users/joshuaungheanu/CloudCompli/swiftform/backend')

from dotenv import load_dotenv
load_dotenv()

from services.openai_trainer import OpenAITrainer

def main():
    print("=" * 80)
    print("MANUAL TRAINING TEST")
    print("=" * 80)

    trainer = OpenAITrainer()

    # Use the small test training file
    training_file = "test_training.jsonl"
    model_name = "gpt-3.5-turbo"

    print(f"\nTraining with file: {training_file}")
    print(f"Model: {model_name}")
    print("\nStarting training...")

    result = trainer.train_with_paired_data(
        training_file=training_file,
        model_name=model_name
    )

    print("\n" + "=" * 80)
    print("RESULT:")
    print("=" * 80)
    print(f"Success: {result.get('success')}")

    if result.get('success'):
        print(f"Job ID: {result.get('job_id')}")
        print(f"Status: {result.get('status')}")
        print("\n✓ Training job created successfully!")
    else:
        print(f"Errors: {result.get('errors')}")
        print(f"Error: {result.get('error')}")
        print("\n✗ Training job failed!")

    print("=" * 80)

    return result

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result.get('success') else 1)