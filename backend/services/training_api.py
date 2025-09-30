"""
API endpoints for OpenAI model training integration
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import os
from datetime import datetime
from .openai_trainer import OpenAITrainer
from .ai_form_parser import AIFormParser
from .training_dashboard import TrainingDashboard
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/training", tags=["training"])

# Pydantic models for request/response
class TrainingDataUpload(BaseModel):
    forms: List[Dict[str, Any]]
    model_name: Optional[str] = "gpt-3.5-turbo"


class TrainingJobResponse(BaseModel):
    success: bool
    job_id: Optional[str] = None
    file_id: Optional[str] = None
    training_examples: Optional[int] = None
    model_base: Optional[str] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None
    errors: Optional[List[str]] = None


class ModelTestRequest(BaseModel):
    model_id: str
    test_document: str


class TrainingStatusResponse(BaseModel):
    job_id: str
    status: str
    model: Optional[str] = None
    created_at: Optional[int] = None
    finished_at: Optional[int] = None
    fine_tuned_model: Optional[str] = None
    error: Optional[Dict[str, Any]] = None
    recent_events: Optional[List[Dict[str, Any]]] = None


# Initialize trainer
trainer = None


def get_trainer() -> OpenAITrainer:
    """Get or create trainer instance"""
    global trainer
    if trainer is None:
        trainer = OpenAITrainer()
    return trainer


@router.post("/upload-forms", response_model=TrainingJobResponse)
async def upload_forms_for_training(
    files: List[UploadFile] = File(...),
    model_name: str = "gpt-3.5-turbo",
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload PDF forms for training a custom model

    Args:
        files: List of PDF files to process
        model_name: Base OpenAI model to fine-tune
        background_tasks: FastAPI background tasks

    Returns:
        Training job details
    """
    try:
        trainer = get_trainer()
        parser = AIFormParser(provider="openai")

        forms_data = []

        # Process each uploaded file
        for file in files:
            if not file.filename.endswith('.pdf'):
                continue

            # Save uploaded file temporarily
            temp_path = f"uploads/temp_{file.filename}"
            os.makedirs("uploads", exist_ok=True)

            content = await file.read()
            with open(temp_path, 'wb') as f:
                f.write(content)

            try:
                # Extract text and schema from PDF
                document_text = parser.extract_pdf_text(temp_path)
                extracted_schema = parser.parse_pdf_with_ai(temp_path)

                forms_data.append({
                    "filename": file.filename,
                    "document_text": document_text[:10000],  # Limit for training
                    "extracted_schema": extracted_schema
                })

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        if not forms_data:
            raise HTTPException(status_code=400, detail="No valid PDF files found")

        # Start training
        result = trainer.train_on_form_batch(forms_data, model_name)

        return TrainingJobResponse(**result)

    except Exception as e:
        logger.error(f"Training upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-training", response_model=TrainingJobResponse)
async def start_training(request: TrainingDataUpload):
    """
    Start training with pre-processed form data

    Args:
        request: Training data with forms and model name

    Returns:
        Training job details
    """
    try:
        trainer = get_trainer()
        result = trainer.train_on_form_batch(request.forms, request.model_name)
        return TrainingJobResponse(**result)

    except Exception as e:
        logger.error(f"Training start failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=TrainingStatusResponse)
async def get_training_status(job_id: str):
    """
    Get status of a training job

    Args:
        job_id: OpenAI fine-tuning job ID

    Returns:
        Job status and details
    """
    try:
        trainer = get_trainer()
        status = trainer.monitor_fine_tuning(job_id)
        return TrainingStatusResponse(**status)

    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_trained_models():
    """
    List all available fine-tuned models

    Returns:
        List of model details
    """
    try:
        trainer = get_trainer()
        models = trainer.get_available_models()
        return {"models": models}

    except Exception as e:
        logger.error(f"Model list failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-model")
async def test_trained_model(request: ModelTestRequest):
    """
    Test a fine-tuned model with a document

    Args:
        request: Model ID and test document

    Returns:
        Extracted schema and model response
    """
    try:
        trainer = get_trainer()
        result = trainer.test_model(request.model_id, request.test_document)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except Exception as e:
        logger.error(f"Model test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{job_id}")
async def cancel_training_job(job_id: str):
    """
    Cancel an ongoing training job

    Args:
        job_id: Fine-tuning job ID

    Returns:
        Success status
    """
    try:
        trainer = get_trainer()
        success = trainer.cancel_training_job(job_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel job")

        return {"success": True, "message": f"Job {job_id} cancelled"}

    except Exception as e:
        logger.error(f"Job cancellation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-data")
async def validate_training_data(request: TrainingDataUpload):
    """
    Validate training data before submitting

    Args:
        request: Training data to validate

    Returns:
        Validation results
    """
    try:
        trainer = get_trainer()
        training_data = trainer.prepare_training_data(request.forms)
        is_valid, errors = trainer.validate_training_data(training_data)

        return {
            "is_valid": is_valid,
            "errors": errors,
            "example_count": len(training_data)
        }

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training-history")
async def get_training_history():
    """
    Get history of all training jobs

    Returns:
        List of training job records
    """
    try:
        trainer = get_trainer()

        # Get all fine-tuning jobs
        jobs = trainer.client.fine_tuning.jobs.list(limit=20)

        history = []
        for job in jobs.data:
            history.append({
                "job_id": job.id,
                "status": job.status,
                "model": job.model,
                "created_at": job.created_at,
                "finished_at": job.finished_at,
                "fine_tuned_model": job.fine_tuned_model,
                "error": job.error
            })

        return {"history": history}

    except Exception as e:
        logger.error(f"Failed to fetch history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard():
    """
    Get comprehensive training dashboard

    Returns:
        Dashboard summary with metrics and active jobs
    """
    try:
        dashboard = TrainingDashboard()
        return dashboard.get_dashboard_summary()

    except Exception as e:
        logger.error(f"Dashboard failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_training_metrics():
    """
    Get detailed training metrics and analytics

    Returns:
        Training metrics and cost estimates
    """
    try:
        dashboard = TrainingDashboard()
        return dashboard.get_training_metrics()

    except Exception as e:
        logger.error(f"Metrics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/list")
async def list_training_jobs(limit: int = 20):
    """
    List all training jobs from OpenAI, prioritizing local history

    Args:
        limit: Maximum number of jobs to return (default 20)

    Returns:
        List of training jobs with basic information
    """
    try:
        from openai import OpenAI
        from pathlib import Path

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Load local job history
        jobs_history_file = Path("training_pairs_uploaded/jobs_history.json")
        local_job_ids = set()
        if jobs_history_file.exists():
            with open(jobs_history_file, 'r') as f:
                local_jobs = json.load(f)
                local_job_ids = {job['job_id'] for job in local_jobs}
                logger.info(f"Loaded {len(local_job_ids)} jobs from local history")

        # List fine-tuning jobs from OpenAI
        response = client.fine_tuning.jobs.list(limit=limit)

        # Format jobs for frontend - prioritize local jobs first
        local_jobs_list = []
        other_jobs_list = []

        for job in response.data:
            job_data = {
                "job_id": job.id,
                "status": job.status,
                "model": job.model,
                "created_at": job.created_at,
                "finished_at": job.finished_at,
                "fine_tuned_model": job.fine_tuned_model,
                "local": job.id in local_job_ids
            }

            if job.id in local_job_ids:
                local_jobs_list.append(job_data)
            else:
                other_jobs_list.append(job_data)

        # Combine: local jobs first, then others
        jobs = local_jobs_list + other_jobs_list

        logger.info(f"Returning {len(jobs)} jobs ({len(local_jobs_list)} local, {len(other_jobs_list)} others)")
        return {"jobs": jobs, "count": len(jobs), "local_count": len(local_jobs_list)}

    except Exception as e:
        logger.error(f"List jobs failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}/details")
async def get_job_details(job_id: str):
    """
    Get detailed information about a specific training job

    Args:
        job_id: OpenAI fine-tuning job ID

    Returns:
        Comprehensive job details with progress estimation
    """
    try:
        dashboard = TrainingDashboard()
        return dashboard.get_job_details(job_id)

    except Exception as e:
        logger.error(f"Job details failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare-models")
async def compare_models(
    model_ids: List[str],
    test_prompt: str
):
    """
    Compare multiple models on the same test prompt

    Args:
        model_ids: List of model IDs to compare
        test_prompt: Test document or prompt

    Returns:
        Comparison results with responses from each model
    """
    try:
        dashboard = TrainingDashboard()
        return dashboard.compare_models(model_ids, test_prompt)

    except Exception as e:
        logger.error(f"Model comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def export_training_report():
    """
    Generate comprehensive training report

    Returns:
        Full report with dashboard, metrics, and recommendations
    """
    try:
        dashboard = TrainingDashboard()
        return dashboard.export_training_report()

    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))