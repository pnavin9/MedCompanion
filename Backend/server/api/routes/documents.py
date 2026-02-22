"""Document processing API routes."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from server.services.pdf_extractor import pdf_extractor

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class PDFPreprocessRequest(BaseModel):
    file_paths: List[str]  # List of PDF paths to process


class PDFPreprocessResponse(BaseModel):
    processed: int
    failed: int
    details: List[dict]


@router.post("/preprocess-pdfs", response_model=PDFPreprocessResponse)
async def preprocess_pdfs(request: PDFPreprocessRequest):
    """
    Extract and cache text from multiple PDF files.
    
    Args:
        file_paths: List of full paths to PDF files
        
    Returns:
        Summary of processing results
    """
    results = []
    success_count = 0
    fail_count = 0
    
    for pdf_path in request.file_paths:
        # Check if already cached
        if pdf_extractor.is_cached(pdf_path):
            results.append({
                "path": pdf_path,
                "status": "already_cached"
            })
            success_count += 1
            continue
        
        # Extract and cache
        result = pdf_extractor.extract_and_cache(pdf_path)
        
        if result["success"]:
            results.append({
                "path": pdf_path,
                "status": "cached",
                "pages": result["pages"]
            })
            success_count += 1
        else:
            results.append({
                "path": pdf_path,
                "status": "failed",
                "error": result["error"]
            })
            fail_count += 1
    
    return PDFPreprocessResponse(
        processed=success_count,
        failed=fail_count,
        details=results
    )


@router.post("/clear-pdf-cache")
async def clear_pdf_cache():
    """Clear all cached PDF text."""
    pdf_extractor.clear_cache()
    return {"status": "ok", "message": "PDF cache cleared"}
