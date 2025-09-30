# SwiftForm AI

AI-powered form generation and training system using OpenAI's GPT models. SwiftForm converts PDF forms into structured JSON schemas (XF format) and provides a comprehensive training dashboard for fine-tuning models.

## Features

### 🤖 AI Form Processing
- **PDF to JSON Conversion**: Upload PDF forms and automatically extract structure
- **XF Schema Support**: Generate standardized XF JSON schemas from any form
- **Multi-file Upload**: Process up to 10 forms simultaneously

### 📊 Training Dashboard
- **Interactive Training Interface**: User-friendly dashboard for managing training data
- **Training Pair Management**: Upload PDF + XF JSON pairs for model fine-tuning
- **Real-time Job Tracking**: Monitor OpenAI training jobs with live status updates
- **Job History**: Persistent tracking of all training jobs with visual indicators
- **Example Templates**: Built-in XF JSON examples to guide users

### 🔧 Training Configuration
- **Minimum 10 Examples**: Enforced OpenAI requirement for quality training
- **Schema Validation**: Automatic validation and formatting of XF JSON
- **Schema Truncation**: Smart truncation to fit OpenAI token limits (50K chars)
- **Job Persistence**: Local history tracking with 🏠 badge for your jobs

## Project Structure

```
swiftform/
├── backend/
│   ├── app/
│   │   └── main_simple.py           # FastAPI application
│   ├── services/
│   │   ├── ai_form_parser.py        # PDF parsing with OpenAI
│   │   ├── openai_trainer.py        # Training job management
│   │   ├── training_api.py          # Training API endpoints
│   │   ├── training_pairs_api.py    # Pair upload & management
│   │   └── training_dashboard.py    # Dashboard utilities
│   ├── training_dashboard.html      # Main dashboard UI
│   ├── training_pairs/              # Training data storage
│   │   └── schemas/                 # Sample XF JSON schemas
│   └── requirements.txt             # Python dependencies
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.8+
- OpenAI API Key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/joshuaungheanu/swiftform.git
cd swiftform
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment:
```bash
# Create .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

4. Start the server:
```bash
uvicorn app.main_simple:app --reload --port 8000
```

5. Open the training dashboard:
```
http://localhost:8000/training-dashboard
```

## Usage

### Training a Model

1. **Upload Training Pairs**:
   - Upload PDF files (up to 10 at once)
   - Paste or upload corresponding XF JSON schema
   - Click "Add to Training Data"

2. **Start Training**:
   - Ensure you have at least 10 training pairs
   - Review your uploaded pairs
   - Click "Start Training"

3. **Monitor Progress**:
   - Select your training job from the dropdown (marked with 🏠)
   - View real-time status updates
   - Check training metrics and logs

### API Endpoints

#### Training Pairs
- `POST /api/training/upload-pair` - Upload PDF + XF JSON pair
- `GET /api/training/pairs` - List all training pairs
- `DELETE /api/training/pairs/{pair_id}` - Delete specific pair
- `DELETE /api/training/pairs` - Clear all pairs

#### Training Jobs
- `POST /api/training/start-from-pairs` - Start training job
- `GET /api/training/jobs/list` - List all training jobs
- `GET /api/training/jobs-history` - Get local job history
- `GET /api/training/job/{job_id}/details` - Get job details

## Features in Detail

### Training Dashboard
The training dashboard provides a comprehensive interface for:
- **Pair Upload**: Drag-and-drop or browse for PDFs and JSON files
- **Example Templates**: Click "Show Example" to see XF JSON structure
- **JSON Validation**: Real-time validation with format and validate buttons
- **Pair Management**: View, remove individual pairs, or clear all
- **Job Selection**: Dropdown with all training jobs (local jobs marked with 🏠)
- **Status Monitoring**: Real-time job status with emojis (✓ ✗ ▶ ⏳ 🔍)

### Job History Tracking
All training jobs are automatically tracked in `training_pairs_uploaded/jobs_history.json`:
```json
{
  "job_id": "ftjob-xxx",
  "model_name": "gpt-3.5-turbo",
  "pair_ids": [...],
  "training_examples": 10,
  "created_at": "2025-09-30T...",
  "timestamp": 1759248543
}
```

## Technologies

- **Backend**: FastAPI, Python 3.8+
- **AI/ML**: OpenAI GPT-4, Fine-tuning API
- **Frontend**: Vanilla JS, Tailwind CSS
- **Storage**: JSON file-based persistence

## Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built with ❤️ using OpenAI's GPT models and fine-tuning API.
