# MedCompanion Server

FastAPI server for MedGemma medical AI assistant with multi-modal support (images + text).

## Features

- ✅ Multi-modal chat (text + medical images)
- ✅ Session management with conversation history
- ✅ Streaming responses (Server-Sent Events)
- ✅ SQLite database for persistence
- ✅ REST API for easy integration
- ✅ MedGemma 4B multimodal model

## Setup

### 1. Install System Dependencies

```bash
# Required for voice transcription
brew install ffmpeg
```

### 2. Install Python Dependencies

```bash
cd /Users/navin1/MedCompanion
source medgemma-env/bin/activate
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and adjust settings if needed:

```bash
cp .env.example .env
```

### 4. Run the Server

```bash
python -m server.main
```

Or with uvicorn directly:

```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### Sessions

**Create Session**
```bash
POST /api/v1/sessions
{
  "title": "My Medical Chat"
}
```

**List Sessions**
```bash
GET /api/v1/sessions
```

**Get Session with History**
```bash
GET /api/v1/sessions/{session_id}
```

**Delete Session**
```bash
DELETE /api/v1/sessions/{session_id}
```

### Chat

**Send Message**
```bash
POST /api/v1/chat
{
  "session_id": "...",
  "message": "What is diabetes?",
  "image_path": null
}
```

**Send Message with Image**
```bash
POST /api/v1/chat
{
  "session_id": "...",
  "message": "What do you see in this X-ray?",
  "image_path": "/path/to/image.jpg"
}
```

**Streaming Chat**
```bash
POST /api/v1/chat/stream
{
  "session_id": "...",
  "message": "Explain hemoglobin"
}
```

### Image Upload

```bash
POST /api/v1/images
Content-Type: multipart/form-data

file: <image file>
```

## Project Structure

```
server/
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── api/
│   ├── routes/
│   │   ├── chat.py      # Chat endpoints
│   │   └── sessions.py  # Session endpoints
│   └── schemas/
│       ├── request.py   # Request models
│       └── response.py  # Response models
├── services/
│   ├── medgemma.py      # MedGemma service
│   └── session_manager.py  # Session management
└── db/
    ├── database.py      # Database setup
    └── models.py        # SQLAlchemy models
```

## Testing

Test the API with curl:

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Create session
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Session"}'

# Send message (replace SESSION_ID)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID",
    "message": "What is hemoglobin?"
  }'
```

## Model Information

- **Model**: google/medgemma-4b-it
- **Type**: Multimodal (text + images)
- **Vision Encoder**: SigLIP (trained on medical images)
- **Context Window**: 128K tokens
- **Image Size**: 896×896 pixels
- **Device**: Auto-detected (MPS/CUDA/CPU)

## Notes

- Model requires ~12-16GB RAM for full precision
- First request will be slower (model loading)
- Images are required even for text-only queries (uses dummy image automatically)
- Session history is maintained server-side
- NOT clinical-grade - for research/development only

## Development

Install development dependencies:

```bash
pip install pytest httpx
```

Run tests:

```bash
pytest
```

## License

See LICENSE file for details.
