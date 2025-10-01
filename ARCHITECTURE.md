# SwiftForm AI - System Architecture & API Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [AI Model Integration](#ai-model-integration)
4. [API Endpoints](#api-endpoints)
5. [Data Flow](#data-flow)
6. [Training Pipeline](#training-pipeline)
7. [Database Schema](#database-schema)
8. [Frontend Components](#frontend-components)

---

## System Overview

SwiftForm AI is a PDF-to-form conversion system that uses OpenAI's GPT-5 model to automatically extract form fields from PDF documents and generate structured XF JSON schemas.

### Tech Stack
- **Backend**: FastAPI (Python 3.x)
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **AI Model**: OpenAI GPT-5 (via OpenAI API)
- **PDF Processing**: PyPDF2
- **Real-time Updates**: Server-Sent Events (SSE)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ Upload Page  │  │ Result Page  │  │ Training Dashboard │   │
│  │ (with Audit) │  │              │  │                    │   │
│  └──────┬───────┘  └──────────────┘  └─────────┬──────────┘   │
│         │                                       │               │
└─────────┼───────────────────────────────────────┼───────────────┘
          │                                       │
          │ HTTP/SSE                              │ HTTP
          ▼                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ Upload API   │  │ Progress SSE │  │ Training API       │   │
│  │ /api/upload  │  │ /api/progress│  │ /api/training/*    │   │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬──────────┘   │
│         │                  │                    │               │
│         ▼                  ▼                    ▼               │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           OpenAI Trainer Service                       │    │
│  │  - PDF Text Extraction (PyPDF2)                        │    │
│  │  - GPT-5 API Integration                               │    │
│  │  - Fine-tuning Management                              │    │
│  │  - Progress Tracking                                   │    │
│  └────────────────────────────┬───────────────────────────┘    │
└─────────────────────────────────┼──────────────────────────────┘
                                  │
                                  │ HTTPS API Calls
                                  ▼
                    ┌─────────────────────────────┐
                    │   OpenAI API (GPT-5)        │
                    │  - Chat Completions         │
                    │  - Fine-tuning Jobs         │
                    │  - File Management          │
                    └─────────────────────────────┘
```

---

## AI Model Integration

### GPT-5 Configuration

**Model**: `gpt-5`
**Release**: August 2025
**Provider**: OpenAI

#### Key Parameters
```python
{
    "model": "gpt-5",
    "max_completion_tokens": 16000,  # GPT-5 uses this instead of max_tokens
    "temperature": 1,  # Default and only supported value for GPT-5
    "response_format": {"type": "json_object"}  # Enforces JSON output
}
```

#### Important Notes
- **GPT-5 does NOT support `max_tokens`** - use `max_completion_tokens` instead
- **GPT-5 does NOT support `temperature=0`** - only default value of 1 is supported
- Maximum output: 128k tokens (we use 16k for form generation)

### PDF to XF Conversion Process

```python
# Location: backend/services/openai_trainer.py
# Method: generate_xf_from_pdf()

Step 1: Extract PDF Text
├── Use PyPDF2 to read PDF
├── Extract text from all pages
├── Limit to 100k characters (~25k tokens)
└── Mark page boundaries

Step 2: Build Prompt
├── System message: "You are an expert form analyzer"
├── Optional: Add few-shot examples
└── User message: PDF content + conversion instructions

Step 3: Call GPT-5 API
├── Send messages with JSON format enforcement
├── Track progress via ProgressTracker
├── Log request/response metrics
└── Parse JSON response

Step 4: Validate & Return
├── Parse JSON schema
├── Validate structure
├── Return XF schema with metadata
└── Track token usage
```

---

## API Endpoints

### Upload & Processing

#### POST /api/upload
Upload a PDF and generate XF schema using GPT-5.

**Request:**
```http
POST /api/upload
Content-Type: multipart/form-data

file: <PDF file>
```

**Response:**
```json
{
  "file_id": "uuid-string",
  "filename": "example.pdf",
  "file_type": ".pdf",
  "status": "uploaded",
  "message": "File uploaded successfully",
  "xf_schema": {
    "title": "Form Title",
    "fields": [
      {
        "id": "field1",
        "type": "text",
        "label": "Field Label",
        "required": true
      }
    ]
  }
}
```

**Processing Flow:**
1. File saved to `backend/uploads/`
2. PDF text extracted via PyPDF2
3. GPT-5 API called with prompt
4. XF JSON schema generated
5. Progress events emitted to SSE stream

---

#### GET /api/progress/{session_id}
Stream real-time progress events via Server-Sent Events.

**Request:**
```http
GET /api/progress/{session_id}
Accept: text/event-stream
```

**Response (Stream):**
```
data: {"timestamp": "2025-10-01T10:30:00", "event_type": "upload", "message": "File uploaded successfully", "data": {"filename": "example.pdf", "size": 12345}}

data: {"timestamp": "2025-10-01T10:30:01", "event_type": "extraction", "message": "Extracting text from PDF...", "data": {}}

data: {"timestamp": "2025-10-01T10:30:05", "event_type": "api_request", "message": "Sending request to gpt-5...", "data": {"model": "gpt-5", "pages": 3, "text_length": 4567}}

data: {"timestamp": "2025-10-01T10:30:25", "event_type": "api_response", "message": "Received response from OpenAI", "data": {"prompt_tokens": 1234, "completion_tokens": 5678, "total_tokens": 6912}}

data: {"timestamp": "2025-10-01T10:30:26", "event_type": "success", "message": "Schema generated successfully", "data": {"schema_size": 15234, "token_usage": {...}}}
```

**Event Types:**
- `upload`: File upload complete
- `extraction`: PDF text extraction
- `processing`: GPT-5 processing started
- `api_request`: API request sent to OpenAI
- `api_response`: API response received
- `success`: Schema generation complete
- `error`: Processing error occurred

---

### Training & Fine-tuning

#### GET /api/training/jobs/list
List all fine-tuning jobs.

**Request:**
```http
GET /api/training/jobs/list?limit=50
```

**Response:**
```json
{
  "jobs": [
    {
      "id": "ftjob-xxx",
      "status": "succeeded",
      "model": "gpt-4o-2024-08-06",
      "fine_tuned_model": "ft:gpt-4o-2024-08-06:org:model:xxx",
      "created_at": 1234567890,
      "finished_at": 1234567890
    }
  ],
  "total": 10
}
```

---

#### POST /api/training/jobs/create
Create a new fine-tuning job.

**Request:**
```json
{
  "training_file_id": "file-xxx",
  "model": "gpt-4o-2024-08-06",
  "hyperparameters": {
    "n_epochs": 3
  }
}
```

**Response:**
```json
{
  "job_id": "ftjob-xxx",
  "status": "queued",
  "message": "Fine-tuning job created successfully"
}
```

---

#### GET /api/training/job/{job_id}/details
Get detailed status of a fine-tuning job.

**Response:**
```json
{
  "id": "ftjob-xxx",
  "status": "running",
  "model": "gpt-4o-2024-08-06",
  "training_file": "file-xxx",
  "validation_file": null,
  "created_at": 1234567890,
  "finished_at": null,
  "fine_tuned_model": null,
  "hyperparameters": {
    "n_epochs": 3
  },
  "result_files": [],
  "trained_tokens": 50000,
  "events": [
    {
      "level": "info",
      "message": "Training started",
      "created_at": 1234567890
    }
  ]
}
```

---

#### GET /api/training/pairs
Get training data pairs (PDF + XF schema).

**Response:**
```json
{
  "pairs": [
    {
      "id": "pair-1",
      "pdf_filename": "example.pdf",
      "xf_filename": "example.json",
      "created_at": "2025-10-01T10:30:00",
      "status": "ready"
    }
  ]
}
```

---

#### POST /api/training/pairs/upload
Upload a training pair (PDF + XF JSON).

**Request:**
```http
POST /api/training/pairs/upload
Content-Type: multipart/form-data

pdf_file: <PDF file>
xf_file: <JSON file>
```

---

## Data Flow

### 1. PDF Upload Flow
```
User → Frontend (UploadWithAudit.tsx)
  ↓
  POST /api/upload with PDF file
  ↓
Backend (main_simple.py)
  ↓
  Save file to uploads/
  ↓
OpenAI Trainer (openai_trainer.py)
  ↓
  Extract PDF text (PyPDF2)
  ↓
  Build prompt with system + user messages
  ↓
  Call GPT-5 API
  ↓
  Parse JSON response
  ↓
  Return XF schema
  ↓
Frontend receives response + connects to SSE
  ↓
Display audit trail + navigate to result
```

### 2. Real-time Progress Flow
```
Backend processes PDF
  ↓
Progress Tracker emits events
  ↓
  - upload: File saved
  - extraction: Text extraction progress
  - api_request: API call details
  - api_response: Token usage, response size
  - success/error: Final status
  ↓
SSE endpoint streams events
  ↓
Frontend receives events via EventSource
  ↓
UI updates in real-time
```

### 3. Fine-tuning Flow
```
User uploads training pairs (PDF + XF JSON)
  ↓
Backend stores pairs in history/pairs/
  ↓
User creates training file
  ↓
Backend converts pairs to JSONL format
  ↓
Upload to OpenAI Files API
  ↓
Create fine-tuning job
  ↓
OpenAI trains model (hours to days)
  ↓
Fine-tuned model available
  ↓
Use fine-tuned model for future conversions
```

---

## Training Pipeline

### Training Data Format

**JSONL Format (OpenAI Fine-tuning):**
```jsonl
{"messages": [{"role": "system", "content": "You are an expert form analyzer..."}, {"role": "user", "content": "PDF content here..."}, {"role": "assistant", "content": "{\"title\": \"Form\", \"fields\": [...]}"}]}
{"messages": [{"role": "system", "content": "You are an expert form analyzer..."}, {"role": "user", "content": "PDF content here..."}, {"role": "assistant", "content": "{\"title\": \"Form\", \"fields\": [...]}"}]}
```

### Training Pair Structure

**Directory**: `backend/history/pairs/`

```
pairs/
├── pair-uuid-1/
│   ├── document.pdf
│   └── schema.json
├── pair-uuid-2/
│   ├── document.pdf
│   └── schema.json
```

### Fine-tuning Process

1. **Prepare Training Data**
   - Upload PDF + XF JSON pairs
   - System validates JSON schema structure
   - Pairs stored in `history/pairs/`

2. **Create Training File**
   - Convert pairs to JSONL format
   - Upload to OpenAI Files API
   - Receive `file_id`

3. **Start Fine-tuning Job**
   ```python
   client.fine_tuning.jobs.create(
       training_file="file-xxx",
       model="gpt-4o-2024-08-06",
       hyperparameters={"n_epochs": 3}
   )
   ```

4. **Monitor Progress**
   - Poll `/api/training/job/{job_id}/details`
   - Check events for progress
   - Wait for `status: "succeeded"`

5. **Use Fine-tuned Model**
   - Model ID: `ft:gpt-4o-2024-08-06:org:name:xxx`
   - Use in `generate_xf_from_pdf(model_id="ft:...")`

---

## Database Schema

### File Storage

**Uploaded Files**: `backend/uploads/`
```
uploads/
├── uuid-1.pdf
├── uuid-2.pdf
```

**History Storage**: `backend/history/`
```
history/
├── forms/
│   ├── uuid-1.json  # Generated XF schemas
│   └── uuid-2.json
├── pairs/
│   ├── pair-uuid-1/
│   │   ├── document.pdf
│   │   └── schema.json
└── history.json  # Metadata
```

### History JSON Structure

**File**: `backend/history/history.json`

```json
{
  "uuid-1": {
    "filename": "example.pdf",
    "uploaded_at": "2025-10-01T10:30:00",
    "model": "gpt-5",
    "status": "completed",
    "schema_path": "forms/uuid-1.json",
    "token_usage": {
      "prompt_tokens": 1234,
      "completion_tokens": 5678,
      "total_tokens": 6912
    }
  }
}
```

---

## Frontend Components

### Key Pages

#### UploadWithAudit.tsx
- Main upload page with real-time audit trail
- Shows SSE events as they happen
- Color-coded event types
- Expandable event details
- Auto-navigates on success

**Location**: `/upload`

#### ResultPage.tsx
- Displays generated XF schema
- JSON viewer with syntax highlighting
- Download schema button
- Form preview (if applicable)

**Location**: `/result/:jobId`

#### TrainingDashboard (Backend HTML)
- Fine-tuning job management
- Training pair upload
- Job status monitoring
- Model selection

**Location**: `/training-dashboard`

### API Service

**File**: `frontend/src/services/api.ts`

```typescript
export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    body: formData,
  })

  return response.json()
}
```

---

## Environment Configuration

### Backend (.env)

```bash
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...

# Server
PORT=8000
HOST=0.0.0.0

# Uploads
UPLOAD_DIR=uploads
HISTORY_DIR=history
```

### Frontend (.env)

```bash
REACT_APP_API_URL=http://localhost:8000/api
```

---

## Key Files Reference

### Backend
- `app/main_simple.py` - Main FastAPI application, API endpoints
- `services/openai_trainer.py` - GPT-5 integration, PDF processing
- `services/progress_tracker.py` - Real-time progress tracking
- `services/training_api.py` - Fine-tuning job management
- `services/training_pairs_api.py` - Training data management
- `services/history_manager.py` - History storage

### Frontend
- `src/pages/UploadWithAudit.tsx` - Upload page with audit trail
- `src/pages/ResultPage.tsx` - Schema display page
- `src/services/api.ts` - API client
- `src/App.tsx` - React router configuration

---

## Model Comparison

| Feature | GPT-4o | GPT-5 |
|---------|--------|-------|
| Parameter | `max_tokens` | `max_completion_tokens` |
| Temperature | Supports 0-2 | Only supports 1 (default) |
| Max Output | 16k tokens | 128k tokens |
| JSON Mode | Supported | Supported |
| Release | 2024-08 | 2025-08 |
| Speed | Fast | Faster |
| Accuracy | High | Higher |

---

## Error Handling

### Common Errors

**1. GPT-5 Parameter Error**
```
Error: Unsupported parameter: 'max_tokens' is not supported
Solution: Use 'max_completion_tokens' instead
```

**2. Temperature Error**
```
Error: 'temperature' does not support 0 with this model
Solution: Remove temperature parameter (defaults to 1)
```

**3. JSON Parse Error**
```
Error: Model response was not valid JSON
Solution: Check prompt, ensure response_format is set
```

---

## Performance Metrics

### Typical Processing Times
- PDF Text Extraction: 1-3 seconds
- GPT-5 API Call: 15-30 seconds (depends on PDF size)
- Total Upload Time: 20-35 seconds

### Token Usage
- Average prompt: 1,000-3,000 tokens
- Average response: 2,000-8,000 tokens
- Cost per conversion: ~$0.10-0.50 (GPT-5 pricing)

---

## Security Considerations

1. **API Keys**: Stored in `.env`, never committed
2. **File Upload**: Validated file types, size limits
3. **CORS**: Configured for specific origins
4. **Rate Limiting**: Not yet implemented (TODO)
5. **Authentication**: Not yet implemented (TODO)

---

## Deployment

### Backend Deployment
```bash
cd backend
source venv/bin/activate
uvicorn app.main_simple:app --host 0.0.0.0 --port 8000
```

### Frontend Deployment
```bash
cd frontend
npm run build
# Serve build/ directory with nginx or similar
```

---

## Future Enhancements

1. **Authentication & Authorization**
   - User accounts
   - API key management
   - Role-based access

2. **Advanced Features**
   - Batch processing
   - Custom model selection
   - Schema validation rules
   - Form preview rendering

3. **Optimization**
   - Caching frequently used PDFs
   - Response streaming for large PDFs
   - Background job processing

4. **Monitoring**
   - Error tracking (Sentry)
   - Performance monitoring (New Relic)
   - Usage analytics

---

## Contact & Support

**Project**: SwiftForm AI
**Version**: 1.0.0
**Last Updated**: October 2025

For questions or issues, please contact the engineering team.
