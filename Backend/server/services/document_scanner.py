"""Document scanner service for reading workspace files."""
from pathlib import Path
from typing import List
from server.services.pdf_extractor import pdf_extractor


def scan_and_read_workspace(workspace_path: str) -> str:
    """
    Scan workspace for MD and PDF files, read/extract all content.
    
    Args:
        workspace_path: Path to workspace folder
        
    Returns:
        Combined document content formatted for AI processing
    """
    workspace = Path(workspace_path)
    if not workspace.exists():
        return "Workspace path not found."
    
    documents = []
    
    # 1. Scan and read all MD files
    for md_file in workspace.glob("*.md"):
        # Skip test/docs files
        if (md_file.name.startswith('test_') or 
            md_file.name.upper().startswith('README') or 
            md_file.name.upper().startswith('IMPLEMENTATION') or
            md_file.name.upper().startswith('MANUAL') or
            md_file.name.upper().startswith('QUICKSTART') or
            md_file.name.upper().startswith('MEDICAL_SUMMARY')):
            continue
        
        try:
            content = md_file.read_text(encoding='utf-8')
            if content.strip():
                documents.append(f"\n--- File: {md_file.name} ---\n{content}\n--- End of file ---\n")
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    # 2. Scan for PDF files
    for pdf_file in workspace.glob("*.pdf"):
        pdf_path = str(pdf_file)
        
        # Check if cached (with 15-min expiry)
        if not pdf_extractor.is_cached(pdf_path, ttl_minutes=15):
            # Cache expired or doesn't exist - extract and cache
            result = pdf_extractor.extract_and_cache(pdf_path)
            if not result.get("success"):
                print(f"Failed to extract PDF {pdf_file.name}: {result.get('error')}")
                continue
        
        # Read cached text
        cached_text = pdf_extractor.get_cached_text(pdf_path)
        if cached_text:
            documents.append(f"\n--- File: {pdf_file.name} (PDF) ---\n{cached_text}\n--- End of file ---\n")
    
    if not documents:
        return "No medical documents found in workspace."
    
    return "\n".join(documents)
