# Medical Summary Feature - Testing Guide

## Overview
The medical summary feature automatically detects when a user asks for a summary of medical files in the workspace and generates a comprehensive summary using all markdown (.md) files.

## How It Works

### Detection
The system detects summary requests based on keywords like:
- "summary", "summarize", "summarise"
- "patient summary", "medical summary"
- "overview", "medical history"
- And various combinations

### Processing Flow
1. User asks for a summary in chat (e.g., "Give me a summary of the patient's medical history")
2. System scans all workspace folders for .md files
3. Displays found files to the user
4. Sends all file contents to MedGemma for analysis
5. Streams the generated summary back to the user

## Test Files Included

Three sample medical documents have been created in the MedCompanion workspace:

1. **test_patient_history.md**
   - Patient demographics and background
   - Medical history and chronic conditions
   - Current medications and allergies
   - Social and family history

2. **test_lab_results.md**
   - Complete blood count (CBC)
   - Comprehensive metabolic panel
   - Lipid panel
   - HbA1c and other tests
   - Lab interpretations and recommendations

3. **test_consultation_notes.md**
   - Cardiology consultation
   - Physical examination findings
   - Diagnostic studies ordered
   - Assessment and treatment plan

## How to Test

### Prerequisites
1. Make sure VS Code is built and running
2. Ensure the MedGemma backend server is running:
   ```bash
   cd MedCompanion
   ./start_server.sh
   ```

### Testing Steps

1. **Open the MedCompanion workspace in VS Code**

2. **Open the Chat panel** (via command palette or shortcut)

3. **Try various summary requests**:
   
   ✅ **Basic Summary**:
   ```
   Summarize the patient's medical files
   ```
   
   ✅ **Generic Summary**:
   ```
   Give me a medical summary
   ```
   
   ✅ **Patient Overview**:
   ```
   What's the patient's medical history?
   ```
   
   ✅ **Specific Focus**:
   ```
   Summarize the patient's lab results
   ```
   
   ✅ **Alternative Phrasing**:
   ```
   Can you provide an overview of the medical documents?
   ```

4. **Expected Behavior**:
   - Chat shows: "Scanning workspace for medical files..."
   - Chat shows: "Found 3 medical documents:" followed by file list
   - Chat shows: "Generating medical summary..."
   - MedGemma streams a comprehensive summary organized by sections

### Edge Cases to Test

1. **No MD files in workspace**:
   - Temporarily rename the .md files
   - Ask for summary
   - Should see: "No medical documents (.md files) found in workspace"

2. **Empty MD file**:
   - Create an empty .md file
   - Should be skipped (not included in the list)

3. **Large files**:
   - The system handles files of any size, but very large files may exceed token limits
   - Consider future enhancements for chunking if needed

4. **Regular chat (not summary)**:
   - Ask regular questions like "What is diabetes?"
   - Should process normally without scanning files

## Implementation Details

### Files Created

1. **workspaceFileScanner.ts**
   - Scans workspace folders recursively
   - Filters for .md files
   - Reads file contents
   - Skips common directories (node_modules, .git, etc.)

2. **summaryDetector.ts**
   - Detects summary intent from user messages
   - Extracts focus areas (e.g., "lab results", "medications")
   - Uses keyword matching and regex patterns

3. **chatSetup.ts** (modified)
   - Added medical summary request handler
   - Shows progress indicators
   - Formats documents for MedGemma prompt
   - Streams response to user

## Future Enhancements

Potential improvements for the future:
1. Add PDF support (Option 2 from the original plan)
2. Implement chunking for very large document sets
3. Add caching to avoid re-scanning on every request
4. Support filtering by file type or date
5. Add ability to exclude specific files
6. Implement summarization of individual files before combining
