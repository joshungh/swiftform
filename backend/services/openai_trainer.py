"""
OpenAI Model Training Module for SwiftformAI
Handles fine-tuning and training of OpenAI models for form processing
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import openai
from openai import OpenAI
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAITrainer:
    """Handles OpenAI model training and fine-tuning for form processing"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI trainer with API key"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=self.api_key)

    def prepare_training_data(self, forms_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Prepare training data in OpenAI fine-tuning format

        Args:
            forms_data: List of form schemas and their extracted data

        Returns:
            List of training examples in OpenAI format
        """
        training_examples = []

        for form in forms_data:
            # Create system message for context
            system_msg = "You are an expert form parser that extracts structured data from documents and creates JSON schemas in xf:* format."

            # Create user message (input document text)
            user_msg = form.get("document_text", "")

            # Create assistant message (expected output schema)
            assistant_msg = json.dumps(form.get("extracted_schema", {}), indent=2)

            training_example = {
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg}
                ]
            }
            training_examples.append(training_example)

        return training_examples

    def create_training_file(self, training_data: List[Dict[str, str]],
                           filename: str = "training_data.jsonl") -> str:
        """
        Create a JSONL file for OpenAI fine-tuning

        Args:
            training_data: Prepared training examples
            filename: Output filename for training data

        Returns:
            Path to created file
        """
        filepath = os.path.join("uploads", "training", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w') as f:
            for example in training_data:
                f.write(json.dumps(example) + '\n')

        logger.info(f"Training file created: {filepath}")
        return filepath

    def upload_training_file(self, filepath: str) -> str:
        """
        Upload training file to OpenAI

        Args:
            filepath: Path to training JSONL file

        Returns:
            File ID from OpenAI
        """
        with open(filepath, 'rb') as f:
            response = self.client.files.create(
                file=f,
                purpose='fine-tune'
            )

        file_id = response.id
        logger.info(f"Training file uploaded with ID: {file_id}")
        return file_id

    def create_fine_tuning_job(self, file_id: str,
                              model: str = "gpt-3.5-turbo",
                              suffix: str = "swiftform") -> str:
        """
        Create a fine-tuning job with OpenAI

        Args:
            file_id: OpenAI file ID of training data
            model: Base model to fine-tune
            suffix: Custom suffix for the fine-tuned model

        Returns:
            Fine-tuning job ID
        """
        response = self.client.fine_tuning.jobs.create(
            training_file=file_id,
            model=model,
            suffix=suffix,
            hyperparameters={
                "n_epochs": 3,
                "batch_size": 1,
                "learning_rate_multiplier": 0.1
            }
        )

        job_id = response.id
        logger.info(f"Fine-tuning job created with ID: {job_id}")
        return job_id

    def monitor_fine_tuning(self, job_id: str) -> Dict[str, Any]:
        """
        Monitor the progress of a fine-tuning job

        Args:
            job_id: Fine-tuning job ID

        Returns:
            Job status and details
        """
        job = self.client.fine_tuning.jobs.retrieve(job_id)

        status = {
            "job_id": job.id,
            "status": job.status,
            "model": job.model,
            "created_at": job.created_at,
            "finished_at": job.finished_at,
            "fine_tuned_model": job.fine_tuned_model,
            "error": job.error.__dict__ if job.error else None
        }

        # Get events for detailed progress
        events = self.client.fine_tuning.jobs.list_events(
            fine_tuning_job_id=job_id,
            limit=10
        )

        status["recent_events"] = [
            {"message": event.message, "created_at": event.created_at}
            for event in events.data
        ]

        logger.info(f"Job {job_id} status: {job.status}")
        return status

    def validate_training_data(self, training_data: List[Dict[str, str]]) -> Tuple[bool, List[str]]:
        """
        Validate training data format and content

        Args:
            training_data: Training examples to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # OpenAI requires minimum 10 examples for fine-tuning
        if len(training_data) < 10:
            errors.append(f"Insufficient training data: {len(training_data)} examples (minimum 10 required)")

        for i, example in enumerate(training_data):
            if "messages" not in example:
                errors.append(f"Example {i}: Missing 'messages' field")
                continue

            messages = example["messages"]
            if not isinstance(messages, list) or len(messages) < 2:
                errors.append(f"Example {i}: Invalid messages format")
                continue

            # Check for required roles
            roles = [msg.get("role") for msg in messages]
            if "user" not in roles or "assistant" not in roles:
                errors.append(f"Example {i}: Missing required user/assistant roles")

            # Check message content
            for msg in messages:
                if not msg.get("content"):
                    errors.append(f"Example {i}: Empty message content for role {msg.get('role')}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def train_on_form_batch(self, forms: List[Dict[str, Any]],
                           model_name: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """
        Complete training pipeline for a batch of forms

        Args:
            forms: List of form data for training
            model_name: Base model to fine-tune

        Returns:
            Training job details
        """
        try:
            # Prepare training data
            logger.info(f"Preparing training data for {len(forms)} forms...")
            training_data = self.prepare_training_data(forms)

            # Validate data
            is_valid, errors = self.validate_training_data(training_data)
            if not is_valid:
                return {
                    "success": False,
                    "errors": errors
                }

            # Create training file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"swiftform_training_{timestamp}.jsonl"
            filepath = self.create_training_file(training_data, filename)

            # Upload to OpenAI
            file_id = self.upload_training_file(filepath)

            # Create fine-tuning job
            job_id = self.create_fine_tuning_job(
                file_id,
                model=model_name,
                suffix=f"swiftform_{timestamp}"
            )

            # Return job details
            return {
                "success": True,
                "job_id": job_id,
                "file_id": file_id,
                "training_examples": len(training_data),
                "model_base": model_name,
                "timestamp": timestamp
            }

        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available fine-tuned models

        Returns:
            List of model details
        """
        try:
            models = self.client.models.list()

            # Filter for fine-tuned models with our suffix
            fine_tuned = [
                {
                    "id": model.id,
                    "created": model.created,
                    "owned_by": model.owned_by
                }
                for model in models.data
                if "swiftform" in model.id.lower()
            ]

            return fine_tuned

        except Exception as e:
            logger.error(f"Failed to fetch models: {str(e)}")
            return []

    def test_model(self, model_id: str, test_document: str) -> Dict[str, Any]:
        """
        Test a fine-tuned model with a document

        Args:
            model_id: Fine-tuned model ID
            test_document: Document text to test

        Returns:
            Model response and extracted schema
        """
        try:
            response = self.client.chat.completions.create(
                model=model_id,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert form parser that extracts structured data from documents and creates JSON schemas in xf:* format."
                    },
                    {
                        "role": "user",
                        "content": f"Extract the form schema from this document:\n\n{test_document}"
                    }
                ],
                temperature=0,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            extracted_schema = json.loads(response.choices[0].message.content)

            return {
                "success": True,
                "model_id": model_id,
                "extracted_schema": extracted_schema,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            logger.error(f"Model test failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def cancel_training_job(self, job_id: str) -> bool:
        """
        Cancel an ongoing training job

        Args:
            job_id: Fine-tuning job ID to cancel

        Returns:
            Success status
        """
        try:
            self.client.fine_tuning.jobs.cancel(job_id)
            logger.info(f"Training job {job_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {str(e)}")
            return False

    def train_with_paired_data(self, training_file: str, model_name: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """
        Train a model using properly paired PDF-to-XF schema training data

        Args:
            training_file: Path to JSONL file with training examples
            model_name: Base model to fine-tune

        Returns:
            Training job information
        """
        try:
            # Validate the training file exists
            if not Path(training_file).exists():
                return {
                    "success": False,
                    "error": f"Training file not found: {training_file}"
                }

            # Validate training data format
            training_examples = []
            with open(training_file, 'r') as f:
                for line in f:
                    training_examples.append(json.loads(line))

            logger.info(f"Loaded {len(training_examples)} training examples")

            # Validate the data
            is_valid, errors = self.validate_training_data(training_examples)
            if not is_valid:
                return {
                    "success": False,
                    "errors": errors
                }

            # Upload the training file
            logger.info(f"Uploading training file: {training_file}")
            with open(training_file, "rb") as f:
                file_response = self.client.files.create(
                    file=f,
                    purpose="fine-tune"
                )

            logger.info(f"File uploaded: {file_response.id}")

            # Create fine-tuning job with custom suffix
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            suffix = f"swiftform-paired-{timestamp}"

            logger.info(f"Creating fine-tuning job with model: {model_name}")

            # Determine batch size based on training examples count
            # OpenAI recommends batch size between 1-256, with "auto" being most flexible
            job = self.client.fine_tuning.jobs.create(
                training_file=file_response.id,
                model=model_name,
                suffix=suffix,
                hyperparameters={
                    "n_epochs": "auto"  # Let OpenAI optimize based on dataset size
                }
            )

            logger.info(f"Fine-tuning job created: {job.id}")

            return {
                "success": True,
                "job_id": job.id,
                "status": job.status,
                "model": model_name,
                "training_file": file_response.id,
                "training_examples": len(training_examples),
                "created_at": job.created_at,
                "suffix": suffix
            }

        except Exception as e:
            logger.error(f"Error creating training job: {e}")
            return {
                "success": False,
                "error": str(e)
            }