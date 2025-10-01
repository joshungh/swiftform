from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import uuid
from datetime import datetime
import json
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.bmp_parser import BMPFormParser
from services.enhanced_bmp_parser import EnhancedBMPParser
from services.history_manager import HistoryManager
from services.training_api import router as training_router
from services.training_pairs_api import router as training_pairs_router
from services.progress_tracker import progress_tracker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="SwiftForm AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include training routers
app.include_router(training_router)
app.include_router(training_pairs_router)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# Simple in-memory storage for demo
uploaded_files = {}
job_results = {}

# Initialize history manager
history_manager = HistoryManager()

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
async def upload_document(file: UploadFile = File(...), session_id: Optional[str] = Form(None)):
    """Upload a document and immediately generate xf:json using GPT-4"""
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

        # Use provided session_id or generate new one
        file_id = session_id if session_id else str(uuid.uuid4())

        # Save file to disk
        file_path = f"uploads/{file_id}{file_ext}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Store file info
        uploaded_files[file_id] = {
            "filename": file.filename,
            "file_type": file_ext,
            "file_path": file_path,
            "uploaded_at": datetime.now().isoformat()
        }

        # If it's a PDF, immediately generate xf:json using GPT-5
        xf_schema = None
        if file_ext == '.pdf':
            try:
                progress_tracker.add_event(file_id, "upload", "File uploaded successfully", {
                    "filename": file.filename,
                    "size": os.path.getsize(file_path)
                })

                print(f"Starting GPT-5 processing for {file.filename}...")
                progress_tracker.add_event(file_id, "processing", "Starting GPT-5 processing...")

                from services.openai_trainer import OpenAITrainer
                trainer = OpenAITrainer()
                # Use GPT-5 (the latest model released Aug 2025)
                print(f"Calling generate_xf_from_pdf with gpt-5...")
                result = trainer.generate_xf_from_pdf(file_path, "gpt-5", use_examples=True, session_id=file_id)

                print(f"GPT-5 result: success={result.get('success')}")
                if result["success"]:
                    xf_schema = result["xf_schema"]
                    print(f"✅ Successfully generated xf:json schema with {len(str(xf_schema))} characters")
                    progress_tracker.add_event(file_id, "success", "Schema generated successfully", {
                        "schema_size": len(str(xf_schema)),
                        "token_usage": result.get("usage", {}),
                        "schema": xf_schema  # Include the actual schema in the event
                    })

                    # Add to history
                    try:
                        history_manager.add_to_history(
                            filename=file.filename,
                            form_schema=xf_schema,
                            file_type=file_ext,
                            processing_time=result.get("processing_time", 0)
                        )
                        print(f"✅ Added to history: {file.filename}")
                    except Exception as hist_error:
                        print(f"⚠️ Failed to add to history: {hist_error}")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"❌ GPT-5 parsing failed: {error_msg}")
                    progress_tracker.add_event(file_id, "error", f"GPT-5 parsing failed: {error_msg}")
                    if 'raw_response' in result:
                        print(f"Raw response preview: {str(result['raw_response'])[:200]}...")
            except Exception as e:
                print(f"❌ GPT-5 parsing error: {type(e).__name__}: {e}")
                progress_tracker.add_event(file_id, "error", f"Error: {str(e)}")
                import traceback
                traceback.print_exc()

        return JSONResponse(content={
            "file_id": file_id,
            "filename": file.filename,
            "file_type": file_ext,
            "status": "uploaded",
            "message": "File uploaded successfully",
            "xf_schema": xf_schema  # Include generated schema if available
        })

    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/{session_id}")
async def get_progress(session_id: str):
    """Stream progress events via Server-Sent Events"""
    async def event_generator():
        try:
            async for event in progress_tracker.get_events(session_id):
                yield event
        except asyncio.CancelledError:
            progress_tracker.cleanup_session(session_id)
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/process", response_model=ProcessResponse)
async def process_document(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Process uploaded document and generate form schema"""
    try:
        job_id = str(uuid.uuid4())

        # For demo, generate a sample form immediately
        background_tasks.add_task(
            generate_form_demo,
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

async def generate_form_demo(job_id: str, file_id: str, ai_model: str, custom_instructions: Optional[str]):
    """Demo task to generate form (returns sample form)"""
    try:
        # Simulate processing
        await asyncio.sleep(1)  # Simulate processing time

        # Get file info if available
        file_info = uploaded_files.get(file_id, {})
        filename = file_info.get("filename", "document")
        file_path = file_info.get("file_path", "")

        # Try to parse the PDF if it exists
        if file_path and os.path.exists(file_path) and file_path.endswith('.pdf'):
            try:
                # Check if this is a fine-tuned model
                if ai_model and ai_model.startswith('ft:'):
                    print(f"Using fine-tuned model: {ai_model}")
                    try:
                        from services.openai_trainer import OpenAITrainer
                        trainer = OpenAITrainer()
                        result = trainer.generate_xf_from_pdf(file_path, ai_model)

                        if result["success"]:
                            form_schema = result["xf_schema"]
                            print(f"Successfully generated schema with fine-tuned model")
                        else:
                            print(f"Fine-tuned model failed: {result.get('error')}, falling back to enhanced parser")
                            enhanced_parser = EnhancedBMPParser()
                            form_schema = enhanced_parser.parse_pdf_complete(file_path)
                    except Exception as ft_error:
                        print(f"Fine-tuned model error: {ft_error}, falling back to enhanced parser")
                        enhanced_parser = EnhancedBMPParser()
                        form_schema = enhanced_parser.parse_pdf_complete(file_path)
                else:
                    # Determine if we should use AI based on model selection
                    use_ai = ai_model and ai_model != 'basic'

                    # Map model names to providers
                    if ai_model and ai_model.startswith('gpt'):
                        ai_provider = 'openai'
                    elif ai_model and ai_model.startswith('claude'):
                        ai_provider = 'claude'
                    else:
                        ai_provider = 'openai'  # Default to OpenAI

                    if use_ai:
                        # Try AI parsing first for best accuracy
                        try:
                            from services.ai_form_parser import AIFormParser
                            ai_parser = AIFormParser(provider=ai_provider, model_name=ai_model)
                            form_schema = ai_parser.parse_pdf_with_ai(file_path)

                            if form_schema.get("props", {}).get("children"):
                                print(f"Successfully parsed with AI ({ai_provider}) using model: {ai_model}")
                            else:
                                raise Exception("AI parsing returned empty form")
                        except Exception as ai_error:
                            print(f"AI parsing failed: {ai_error}, falling back to enhanced parser")
                            # Fall back to enhanced parser
                            enhanced_parser = EnhancedBMPParser()
                            form_schema = enhanced_parser.parse_pdf_complete(file_path)
                    else:
                        # Use enhanced parser if AI is disabled
                        enhanced_parser = EnhancedBMPParser()
                        form_schema = enhanced_parser.parse_pdf_complete(file_path)

                # If enhanced parser returns empty form, try basic parser
                if not form_schema.get("props", {}).get("children"):
                    parser = BMPFormParser()
                    form_schema = parser.parse_pdf_to_xf(file_path)

                    # If still empty, use default
                    if not form_schema.get("props", {}).get("children"):
                        raise Exception("No fields extracted")

            except Exception as e:
                print(f"PDF parsing failed: {e}, using default form")
                # Fall back to default form
                form_schema = get_default_form_schema(filename)
        else:
            # Return a sample form schema based on file type
            form_schema = get_default_form_schema(filename)

        result = {
            "job_id": job_id,
            "status": "completed",
            "form_schema": form_schema,
            "processing_time": 2.0
        }

        job_results[job_id] = result

        # Add to history
        history_manager.add_to_history(
            filename=filename,
            form_schema=form_schema,
            file_type=file_info.get("file_type", ".pdf"),
            processing_time=2.0
        )

    except Exception as e:
        result = {
            "job_id": job_id,
            "status": "failed",
            "error": str(e)
        }
        job_results[job_id] = result

def get_default_form_schema(filename: str) -> Dict:
    """Get default form schema"""
    return {
            "name": "xf:form",
            "props": {
                "xfPageNavigation": "toc",
                "children": [
                    {
                        "name": "xf:page",
                        "props": {
                            "xfName": "general_information",
                            "xfLabel": "General Information",
                            "children": [
                                {
                                    "name": "xf:string",
                                    "props": {
                                        "xfName": "document_name",
                                        "xfLabel": "Document Name",
                                        "xfDefaultValue": filename,
                                        "xfRequired": True
                                    }
                                },
                                {
                                    "name": "xf:date",
                                    "props": {
                                        "xfName": "inspection_date",
                                        "xfLabel": "Inspection Date",
                                        "xfPrepopulateValueType": "date_today",
                                        "xfPrepopulateValueEnabled": True
                                    }
                                },
                                {
                                    "name": "xf:string",
                                    "props": {
                                        "xfName": "inspector_name",
                                        "xfLabel": "Inspector Name",
                                        "xfPrepopulateValueType": "user_name",
                                        "xfPrepopulateValueEnabled": True
                                    }
                                },
                                {
                                    "name": "xf:text",
                                    "props": {
                                        "xfName": "notes",
                                        "xfLabel": "Notes"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "name": "xf:page",
                        "props": {
                            "xfName": "site_details",
                            "xfLabel": "Site Details",
                            "children": [
                                {
                                    "name": "xf:group",
                                    "props": {
                                        "xfLabel": "Location",
                                        "children": [
                                            {
                                                "name": "xf:string",
                                                "props": {
                                                    "xfName": "site_name",
                                                    "xfLabel": "Site Name"
                                                }
                                            },
                                            {
                                                "name": "xf:text",
                                                "props": {
                                                    "xfName": "site_address",
                                                    "xfLabel": "Site Address"
                                                }
                                            },
                                            {
                                                "name": "xf:string",
                                                "props": {
                                                    "xfName": "site_id",
                                                    "xfLabel": "Site ID"
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "name": "xf:select",
                                    "props": {
                                        "xfName": "weather_condition",
                                        "xfLabel": "Weather Condition",
                                        "xfOptions": "Clear\nCloudy\nRain\nSnow"
                                    }
                                },
                                {
                                    "name": "xf:boolean",
                                    "props": {
                                        "xfName": "compliance_met",
                                        "xfLabel": "Compliance Requirements Met?"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "name": "xf:page",
                        "props": {
                            "xfName": "checklist",
                            "xfLabel": "Inspection Checklist",
                            "children": [
                                {
                                    "name": "xf:ternary",
                                    "props": {
                                        "xfName": "erosion_control",
                                        "xfLabel": "Erosion Control Measures"
                                    }
                                },
                                {
                                    "name": "xf:ternary",
                                    "props": {
                                        "xfName": "sediment_control",
                                        "xfLabel": "Sediment Control Measures"
                                    }
                                },
                                {
                                    "name": "xf:ternary",
                                    "props": {
                                        "xfName": "waste_management",
                                        "xfLabel": "Waste Management"
                                    }
                                },
                                {
                                    "name": "xf:text",
                                    "props": {
                                        "xfName": "corrective_actions",
                                        "xfLabel": "Corrective Actions Required"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

@app.get("/api/status/{job_id}", response_model=FormGenerationResult)
async def get_job_status(job_id: str):
    """Get the status of a form generation job"""
    if job_id in job_results:
        return FormGenerationResult(**job_results[job_id])
    else:
        return FormGenerationResult(
            job_id=job_id,
            status="processing",
            form_schema=None
        )

@app.post("/api/validate")
async def validate_form_schema(schema: Dict[Any, Any]):
    """Validate a generated form schema"""
    try:
        # Basic validation
        is_valid = schema.get("name") == "xf:form" and "props" in schema
        return {
            "valid": is_valid,
            "errors": [] if is_valid else ["Invalid form schema structure"]
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

@app.get("/api/history")
async def get_history(limit: int = 50):
    """Get form generation history"""
    try:
        history = history_manager.get_history(limit)
        return {
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{entry_id}")
async def get_history_entry(entry_id: str):
    """Get a specific history entry with form schema"""
    try:
        entry = history_manager.get_entry(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="History entry not found")
        return entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history/{entry_id}")
async def delete_history_entry(entry_id: str):
    """Delete a history entry"""
    try:
        success = history_manager.delete_entry(entry_id)
        if not success:
            raise HTTPException(status_code=404, detail="History entry not found")
        return {"message": "Entry deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history")
async def clear_history():
    """Clear all history"""
    try:
        success = history_manager.clear_history()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear history")
        return {"message": "History cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/search/{query}")
async def search_history(query: str):
    """Search history by filename"""
    try:
        results = history_manager.search_history(query)
        return {
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/training-dashboard")
async def serve_training_dashboard():
    """Serve the training dashboard HTML file"""
    dashboard_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "training_dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        raise HTTPException(status_code=404, detail="Dashboard not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)