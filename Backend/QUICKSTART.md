# MedCompanion Server - Quick Start Guide

## Prerequisites

✅ Python 3.10 (already installed)
✅ MedGemma model downloaded (already done)
✅ Virtual environment created (`medgemma-env`)

## Installation

1. **Install server dependencies:**

```bash
cd /Users/navin1/MedCompanion
source medgemma-env/bin/activate
pip install -r requirements.txt
```

2. **Create environment file (optional):**

```bash
cp .env.example .env
# Edit .env if you want to change default settings
```

## Running the Server

### Option 1: Using the start script (easiest)

```bash
./start_server.sh
```

### Option 2: Direct Python

```bash
source medgemma-env/bin/activate
python -m server.main
```

### Option 3: Using uvicorn

```bash
source medgemma-env/bin/activate
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing the Server

Once the server is running, you can test it:

### 1. Check health

```bash
curl http://localhost:8000/api/v1/health
```

### 2. Run the test script

```bash
# In a new terminal
source medgemma-env/bin/activate
python test_api.py
```

### 3. Try the interactive API docs

Open your browser to: http://localhost:8000/docs

## Example Usage

### Create a session and chat:

```bash
# 1. Create session
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "My Chat"}' | jq -r '.session_id')

echo "Session ID: $SESSION_ID"

# 2. Send a message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What is hemoglobin?\"
  }" | jq

# 3. Get session history
curl http://localhost:8000/api/v1/sessions/$SESSION_ID | jq
```

## Server Details

- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: SQLite (`medcompanion.db`)
- **Storage**: `./storage/` directory
- **Model**: MedGemma 4B-it (already loaded)

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/sessions` | Create session |
| GET | `/api/v1/sessions` | List sessions |
| GET | `/api/v1/sessions/{id}` | Get session history |
| DELETE | `/api/v1/sessions/{id}` | Delete session |
| POST | `/api/v1/chat` | Send message |
| POST | `/api/v1/chat/stream` | Send message (streaming) |
| POST | `/api/v1/images` | Upload image |

## Troubleshooting

### Server won't start

Check if the port is already in use:
```bash
lsof -i :8000
```

### Model loading errors

Make sure MedGemma is properly downloaded and you have enough RAM (~12-16GB).

### Import errors

Reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

## Next Steps

1. Test with curl or Postman
2. Integrate with VS Code extension (future)
3. Add authentication (future)
4. Add DICOM support (future)

## Notes

- First request will be slower (~30-60s) as model loads
- Responses take 5-10s on M4 Max
- Model uses dummy images for text-only queries automatically
- NOT clinical-grade - for development/research only
