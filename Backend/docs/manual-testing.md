# Manual Testing Guide

This guide provides curl commands to manually test the API, including health, sessions, and domain/mode combinations.

## Prerequisites

1. Start the server from the `Backend` directory (activate the virtual environment, then run `python -m server.main` or `./start_server.sh` if present).
2. Wait for the model to load (first request may take 30–60 seconds).

## Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected: JSON with `"status": "ok"` (or similar) and model/session info.

## Create Session

```bash
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "Domain/Mode Test Session"}' | jq -r '.session_id')

echo "Session ID: $SESSION_ID"
```

## Domain/Mode Combinations

Chat requests accept optional `domain` and `mode`:

- **Domains:** `general`, `radiology`, `pathology`, `dermatology`
- **Modes:** `consult`, `plan`, `diagnose`

Example (General + Consult):

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What is aspirin?\",
    \"domain\": \"general\",
    \"mode\": \"consult\"
  }" | jq
```

Repeat with other `domain`/`mode` pairs (e.g. `radiology` + `diagnose`, `pathology` + `plan`). Omit `domain` and `mode` to use defaults (general / consult).

## Get Session History

```bash
curl http://localhost:8000/api/v1/sessions/$SESSION_ID | jq
```

## Speech (MedASR)

```bash
# POST audio file to /api/v1/speech/transcribe (multipart/form-data)
# See API docs at http://localhost:8000/docs
```

## Interactive API Docs

- **Swagger UI:** http://localhost:8000/docs  
- **ReDoc:** http://localhost:8000/redoc  

Use these to try chat, sessions, documents, and DICOM endpoints with your own payloads.

## Cleanup

```bash
curl -X DELETE http://localhost:8000/api/v1/sessions/$SESSION_ID | jq
```

## Automated Tests

From the `Backend` directory with the virtual environment activated:

```bash
pytest
python test_api.py   # if present
```
