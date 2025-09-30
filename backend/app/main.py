from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import uuid
from datetime import datetime
import json

from services.document_parser import DocumentParser
from services.ai_form_generator import AIFormGenerator
from models.form_schema import FormSchema, FormField
from utils.file_handler import FileHandler

app = FastAPI(title="SwiftForm AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

document_parser = DocumentParser()
ai_generator = AIFormGenerator()
file_handler = FileHandler()

class ProcessRequest(BaseModel):
    file_id: str
    ai_model: Optional[str] = "gpt-4"
    custom_instructions: Optional[str] = None

class ProcessResponse(BaseModel):
    job_id: str
    status: str
    message: str

class FormGenerationResult(BaseModel):
    job_id: str
    status: str
    form_schema: Optional[Dict[Any, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

@app.get("/")
async def root():
    return {
        "name": "SwiftForm AI API",
        "version": "1.0.0",
        "description": "AI-powered form generation from documents"
    }

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for processing"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        allowed_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx'}
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {allowed_extensions}"
            )

        file_id = str(uuid.uuid4())
        file_path = await file_handler.save_upload(file, file_id)

        return JSONResponse(content={
            "file_id": file_id,
            "filename": file.filename,
            "file_type": file_ext,
            "status": "uploaded",
            "message": "File uploaded successfully"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process", response_model=ProcessResponse)
async def process_document(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Process uploaded document and generate form schema"""
    try:
        job_id = str(uuid.uuid4())

        background_tasks.add_task(
            generate_form_async,
            job_id,
            request.file_id,
            request.ai_model,
            request.custom_instructions
        )

        return ProcessResponse(
            job_id=job_id,
            status="processing",
            message="Form generation started"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def generate_form_async(job_id: str, file_id: str, ai_model: str, custom_instructions: Optional[str]):
    """Background task to generate form from document"""
    try:
        start_time = datetime.now()

        file_path = file_handler.get_file_path(file_id)
        if not file_path:
            raise Exception(f"File not found: {file_id}")

        extracted_content = await document_parser.parse_document(file_path)

        form_schema = await ai_generator.generate_form(
            extracted_content,
            ai_model=ai_model,
            custom_instructions=custom_instructions
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        result = {
            "job_id": job_id,
            "status": "completed",
            "form_schema": form_schema,
            "processing_time": processing_time
        }

        await file_handler.save_result(job_id, result)

    except Exception as e:
        result = {
            "job_id": job_id,
            "status": "failed",
            "error": str(e)
        }
        await file_handler.save_result(job_id, result)

@app.get("/api/status/{job_id}", response_model=FormGenerationResult)
async def get_job_status(job_id: str):
    """Get the status of a form generation job"""
    try:
        result = await file_handler.get_result(job_id)
        if not result:
            return FormGenerationResult(
                job_id=job_id,
                status="processing",
                form_schema=None
            )

        return FormGenerationResult(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/validate")
async def validate_form_schema(schema: Dict[Any, Any]):
    """Validate a generated form schema"""
    try:
        is_valid, errors = FormSchema.validate_schema(schema)
        return {
            "valid": is_valid,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/examples")
async def get_form_examples():
    """Get example form schemas"""
    return {
        "examples": [
            {
                "name": "Simple Contact Form",
                "schema": {
                    "name": "xf:form",
                    "props": {
                        "xfPageNavigation": "none",
                        "children": [
                            {
                                "name": "xf:page",
                                "props": {
                                    "xfName": "contact_info",
                                    "xfLabel": "Contact Information",
                                    "children": [
                                        {
                                            "name": "xf:string",
                                            "props": {
                                                "xfName": "full_name",
                                                "xfLabel": "Full Name",
                                                "xfRequired": True
                                            }
                                        },
                                        {
                                            "name": "xf:string",
                                            "props": {
                                                "xfName": "email",
                                                "xfLabel": "Email Address",
                                                "xfFormat": "email",
                                                "xfRequired": True
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)