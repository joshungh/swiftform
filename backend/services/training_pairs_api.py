"""
API endpoints for training pairs management
Handles uploading PDF + XF JSON pairs for model training
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from pydantic import BaseModel
import json
import os
from datetime import datetime
from pathlib import Path
import PyPDF2
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/training", tags=["training-pairs"])

# Storage files
STORAGE_FILE = Path("training_pairs_uploaded/pairs_storage.json")
JOBS_HISTORY_FILE = Path("training_pairs_uploaded/jobs_history.json")

def load_training_pairs():
    """Load training pairs from JSON file"""
    if STORAGE_FILE.exists():
        with open(STORAGE_FILE, 'r') as f:
            return json.load(f)
    return []

def save_training_pairs(pairs):
    """Save training pairs to JSON file"""
    STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STORAGE_FILE, 'w') as f:
        json.dump(pairs, f, indent=2)

def load_jobs_history():
    """Load training jobs history from JSON file"""
    if JOBS_HISTORY_FILE.exists():
        with open(JOBS_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_jobs_history(jobs):
    """Save training jobs history to JSON file"""
    JOBS_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(JOBS_HISTORY_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)

def add_job_to_history(job_id, model_name, pair_ids, training_examples):
    """Add a new training job to history"""
    jobs = load_jobs_history()
    job_entry = {
        "job_id": job_id,
        "model_name": model_name,
        "pair_ids": pair_ids,
        "training_examples": training_examples,
        "created_at": datetime.now().isoformat(),
        "timestamp": int(datetime.now().timestamp())
    }
    jobs.append(job_entry)
    save_jobs_history(jobs)
    logger.info(f"Added job {job_id} to history")
    return job_entry

# Load training pairs from storage
training_pairs_storage = load_training_pairs()


class TrainingPairResponse(BaseModel):
    pair_id: str
    form_name: str
    pdf_file: str
    json_file: str
    uploaded_at: str


class StartTrainingRequest(BaseModel):
    pair_ids: List[str]
    model_name: str = "gpt-3.5-turbo"


@router.post("/upload-pair", response_model=TrainingPairResponse)
async def upload_training_pair(
    pdf_file: UploadFile = File(...),
    json_file: UploadFile = File(...),
    form_name: str = ""
):
    """
    Upload a PDF + XF JSON training pair

    Args:
        pdf_file: PDF form file
        json_file: XF JSON schema file
        form_name: Optional name for the form

    Returns:
        Training pair details
    """
    try:
        # Validate files
        if not pdf_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="PDF file must have .pdf extension")

        if not json_file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="JSON file must have .json extension")

        # Generate unique ID for this pair
        pair_id = f"pair_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(training_pairs_storage)}"

        # Save files
        training_pairs_dir = Path("training_pairs_uploaded")
        training_pairs_dir.mkdir(exist_ok=True)
        (training_pairs_dir / "pdfs").mkdir(exist_ok=True)
        (training_pairs_dir / "schemas").mkdir(exist_ok=True)

        # Save PDF
        pdf_filename = f"{pair_id}.pdf"
        pdf_path = training_pairs_dir / "pdfs" / pdf_filename
        with open(pdf_path, "wb") as f:
            content = await pdf_file.read()
            f.write(content)

        # Save and validate JSON
        json_content = await json_file.read()
        try:
            schema = json.loads(json_content)
            # Validate it's a valid XF schema
            if not isinstance(schema, dict) or schema.get("name") != "xf:form":
                raise HTTPException(status_code=400, detail="Invalid XF schema format. Must be xf:form")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file")

        json_filename = f"{pair_id}.json"
        json_path = training_pairs_dir / "schemas" / json_filename
        with open(json_path, "w") as f:
            f.write(json_content.decode('utf-8'))

        # Create pair entry
        pair_entry = {
            "pair_id": pair_id,
            "form_name": form_name or pdf_file.filename.replace('.pdf', ''),
            "pdf_file": pdf_filename,
            "json_file": json_filename,
            "pdf_path": str(pdf_path),
            "json_path": str(json_path),
            "uploaded_at": datetime.now().isoformat()
        }

        training_pairs_storage.append(pair_entry)
        save_training_pairs(training_pairs_storage)

        logger.info(f"Training pair uploaded: {pair_id}")

        return TrainingPairResponse(**pair_entry)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training pair upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pairs")
async def get_training_pairs():
    """
    Get all uploaded training pairs

    Returns:
        List of training pairs
    """
    return {"pairs": training_pairs_storage, "total": len(training_pairs_storage)}


@router.delete("/pairs/{pair_id}")
async def delete_training_pair(pair_id: str):
    """
    Delete a training pair

    Args:
        pair_id: Training pair ID

    Returns:
        Success status
    """
    global training_pairs_storage

    pair = next((p for p in training_pairs_storage if p["pair_id"] == pair_id), None)

    if not pair:
        raise HTTPException(status_code=404, detail="Training pair not found")

    try:
        # Delete files
        if os.path.exists(pair["pdf_path"]):
            os.remove(pair["pdf_path"])
        if os.path.exists(pair["json_path"]):
            os.remove(pair["json_path"])

        # Remove from storage
        training_pairs_storage = [p for p in training_pairs_storage if p["pair_id"] != pair_id]
        save_training_pairs(training_pairs_storage)

        return {"success": True, "message": f"Training pair {pair_id} deleted"}

    except Exception as e:
        logger.error(f"Failed to delete training pair: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/pairs")
async def clear_all_training_pairs():
    """
    Delete all training pairs

    Returns:
        Success status with count of deleted pairs
    """
    global training_pairs_storage

    try:
        count = len(training_pairs_storage)

        # Delete all files
        for pair in training_pairs_storage:
            if os.path.exists(pair["pdf_path"]):
                os.remove(pair["pdf_path"])
            if os.path.exists(pair["json_path"]):
                os.remove(pair["json_path"])

        # Clear storage
        training_pairs_storage = []
        save_training_pairs(training_pairs_storage)

        return {"success": True, "message": f"Deleted {count} training pairs", "count": count}

    except Exception as e:
        logger.error(f"Failed to clear training pairs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs-history")
async def get_jobs_history():
    """
    Get local history of all training jobs created from this system

    Returns:
        List of training jobs with metadata
    """
    try:
        jobs = load_jobs_history()
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as e:
        logger.error(f"Failed to load jobs history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-from-pairs")
async def start_training_from_pairs(request: StartTrainingRequest):
    """
    Start training using uploaded PDF-XF pairs

    Args:
        request: Training request with pair_ids and model_name

    Returns:
        Training job details
    """
    try:
        print("=" * 80)
        print("START TRAINING REQUEST RECEIVED")
        print(f"Pair IDs: {request.pair_ids}")
        print(f"Model Name: {request.model_name}")
        print("=" * 80)

        from .openai_trainer import OpenAITrainer

        pair_ids = request.pair_ids
        model_name = request.model_name

        MIN_PAIRS = 10  # OpenAI requires minimum 10 examples for fine-tuning

        print(f"Checking minimum pairs: {len(pair_ids)} >= {MIN_PAIRS}")

        if len(pair_ids) < MIN_PAIRS:
            raise HTTPException(
                status_code=400,
                detail=f"Need at least {MIN_PAIRS} training pairs, got {len(pair_ids)}"
            )

        # Get the pairs
        print(f"Current training_pairs_storage has {len(training_pairs_storage)} pairs")
        pairs = [p for p in training_pairs_storage if p["pair_id"] in pair_ids]
        print(f"Found {len(pairs)} matching pairs")

        if len(pairs) != len(pair_ids):
            raise HTTPException(status_code=400, detail="Some training pairs not found")

        # Prepare training data
        training_examples = []
        print("Preparing training examples...")

        for pair in pairs:
            try:
                print(f"Processing pair: {pair['pair_id']}")

                # Extract PDF text (limited to avoid token overflow)
                pdf_text = ""
                try:
                    print(f"  Reading PDF: {pair['pdf_path']}")
                    with open(pair["pdf_path"], 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for i, page in enumerate(pdf_reader.pages):
                            if i < 2:  # Only first 2 pages
                                page_text = page.extract_text()
                                if page_text:
                                    pdf_text += page_text[:2000]  # Limit per page
                    print(f"  Extracted {len(pdf_text)} chars from PDF")
                except Exception as e:
                    print(f"  ERROR extracting PDF: {e}")
                    logger.warning(f"Error extracting PDF text for {pair['pair_id']}: {e}")
                    continue

                # Load schema
                print(f"  Reading JSON: {pair['json_path']}")
                with open(pair["json_path"], 'r') as f:
                    schema = json.load(f)
                print(f"  Loaded JSON schema")

                # Create training example with compact JSON (no indentation to save tokens)
                schema_json = json.dumps(schema, separators=(',', ':'))

                # OpenAI limit is ~16k tokens per message (roughly 64k chars total for all messages)
                # Truncate schema if too large to prevent API errors
                MAX_SCHEMA_CHARS = 50000
                if len(schema_json) > MAX_SCHEMA_CHARS:
                    print(f"  WARNING: Schema is very large ({len(schema_json)} chars), truncating to {MAX_SCHEMA_CHARS}")
                    schema_json = schema_json[:MAX_SCHEMA_CHARS] + '...truncated}'
                else:
                    print(f"  Schema size: {len(schema_json)} chars")

                training_example = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert form parser specializing in converting PDF documents into XF schemas for SwiftForm AI. Extract all fields and create accurate XF schemas."
                        },
                        {
                            "role": "user",
                            "content": f"Convert this PDF form into an XF schema.\n\nPDF Content:\n{pdf_text}\n\nGenerate the complete XF schema."
                        },
                        {
                            "role": "assistant",
                            "content": schema_json
                        }
                    ]
                }

                training_examples.append(training_example)
                print(f"  Added training example ({len(schema_json)} chars)")

            except Exception as e:
                import traceback
                print(f"  ERROR processing pair {pair.get('pair_id', 'unknown')}: {e}")
                print(traceback.format_exc())
                logger.error(f"Error processing pair: {e}\n{traceback.format_exc()}")
                continue

        logger.info(f"Prepared {len(training_examples)} training examples")
        print(f"Successfully prepared {len(training_examples)} training examples")

        # Save training file
        print("Saving training file...")
        training_file = Path("training_pairs_uploaded") / "training_data.jsonl"
        with open(training_file, 'w') as f:
            for example in training_examples:
                f.write(json.dumps(example) + '\n')
        print(f"Saved training file to: {training_file}")

        # Start training
        print("Creating OpenAI trainer...")
        trainer = OpenAITrainer()
        print("Calling train_with_paired_data...")
        result = trainer.train_with_paired_data(
            training_file=str(training_file),
            model_name=model_name
        )
        print(f"Trainer result: {result}")

        if not result.get("success"):
            print(f"Training failed: {result.get('error', 'Training failed')}")
            raise HTTPException(status_code=500, detail=result.get("error", "Training failed"))

        print("Training started successfully!")

        # Add job to history
        job_id = result["job_id"]
        add_job_to_history(
            job_id=job_id,
            model_name=model_name,
            pair_ids=pair_ids,
            training_examples=len(training_examples)
        )

        return {
            "success": True,
            "job_id": job_id,
            "status": result.get("status"),
            "training_examples": len(training_examples),
            "model": model_name
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print("=" * 80)
        print("ERROR IN START TRAINING:")
        print(error_detail)
        print("=" * 80)
        logger.error(f"Training from pairs failed: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))