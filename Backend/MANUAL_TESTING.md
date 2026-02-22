# Manual Testing Guide for Domain/Mode Support

This guide provides curl commands to manually test all domain/mode combinations.

## Prerequisites

1. Start the server:
```bash
cd /Users/navin1/MedCompanion
./start_server.sh
```

2. Wait for the model to load (first request takes 30-60 seconds)

## Test 1: Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected: `{"status": "healthy"}`

## Test 2: Create Session

```bash
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "Domain/Mode Test Session"}' | jq -r '.session_id')

echo "Session ID: $SESSION_ID"
```

## Test 3: Domain/Mode Combinations

### General Domain

**General + Consult (Default)**
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

**General + Plan**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"How can I improve my cardiovascular health?\",
    \"domain\": \"general\",
    \"mode\": \"plan\"
  }" | jq
```

**General + Diagnose**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"I have a persistent headache. What could it be?\",
    \"domain\": \"general\",
    \"mode\": \"diagnose\"
  }" | jq
```

### Radiology Domain

**Radiology + Consult**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What imaging modality is best for detecting lung nodules?\",
    \"domain\": \"radiology\",
    \"mode\": \"consult\"
  }" | jq
```

**Radiology + Plan**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"I need to plan follow-up imaging for a suspicious lesion.\",
    \"domain\": \"radiology\",
    \"mode\": \"plan\"
  }" | jq
```

**Radiology + Diagnose**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What is pneumonia?\",
    \"domain\": \"radiology\",
    \"mode\": \"diagnose\"
  }" | jq
```

### Pathology Domain

**Pathology + Consult**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What does elevated CRP indicate?\",
    \"domain\": \"pathology\",
    \"mode\": \"consult\"
  }" | jq
```

**Pathology + Plan**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What additional tests should I order based on these findings?\",
    \"domain\": \"pathology\",
    \"mode\": \"plan\"
  }" | jq
```

**Pathology + Diagnose**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Interpret these lab results for anemia.\",
    \"domain\": \"pathology\",
    \"mode\": \"diagnose\"
  }" | jq
```

### Dermatology Domain

**Dermatology + Consult**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What are the treatment options for acne?\",
    \"domain\": \"dermatology\",
    \"mode\": \"consult\"
  }" | jq
```

**Dermatology + Plan**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Help me plan treatment for severe eczema.\",
    \"domain\": \"dermatology\",
    \"mode\": \"plan\"
  }" | jq
```

**Dermatology + Diagnose**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"I have a red, itchy rash on my arm.\",
    \"domain\": \"dermatology\",
    \"mode\": \"diagnose\"
  }" | jq
```

## Test 4: Mid-Conversation Domain Switching

```bash
# First message with Radiology
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What does a chest X-ray show?\",
    \"domain\": \"radiology\",
    \"mode\": \"diagnose\"
  }" | jq

# Second message switching to Pathology (same session)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Now analyze this from a pathology perspective.\",
    \"domain\": \"pathology\",
    \"mode\": \"diagnose\"
  }" | jq
```

## Test 5: Invalid Mode (Agent)

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Hello\",
    \"mode\": \"agent\"
  }" | jq
```

Expected: HTTP 422 with validation error message about Agent mode not being supported.

## Test 6: Default Behavior (No Domain/Mode)

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What is diabetes?\"
  }" | jq
```

Expected: Should default to General + Consult mode.

## Test 7: Get Session History

```bash
curl http://localhost:8000/api/v1/sessions/$SESSION_ID | jq
```

Verify that the conversation history includes all previous messages.

## Test 8: Swagger UI

Open browser to: http://localhost:8000/docs

Verify that:
- `domain` and `mode` fields appear in the ChatRequest schema
- Enum values are properly documented
- You can test requests interactively

## Cleanup

```bash
curl -X DELETE http://localhost:8000/api/v1/sessions/$SESSION_ID | jq
```

## Success Criteria

✅ All 12 domain/mode combinations work
✅ Responses reflect appropriate specialist personas
✅ Mid-conversation switching works seamlessly
✅ Agent mode is rejected with 422 error
✅ Defaults work for backward compatibility
✅ Swagger UI is updated
✅ Medical disclaimers present in all responses

## Automated Testing

Run the automated test script:
```bash
cd /Users/navin1/MedCompanion
source medgemma-env/bin/activate
python test_api.py
```

## Unit Tests

Run unit tests for system prompts:
```bash
cd /Users/navin1/MedCompanion
source medgemma-env/bin/activate
python -m pytest server/tests/test_system_prompts.py -v
```
