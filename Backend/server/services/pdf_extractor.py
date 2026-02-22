"""PDF text extraction service with caching."""
import pymupdf
from pathlib import Path
from typing import Dict, Optional
import hashlib
import json


class PDFExtractor:
    """Service for extracting and caching PDF text."""
    
    def __init__(self, cache_dir: str = None):
        # Cache directory in backend folder (NOT system temp)
        if cache_dir is None:
            self.cache_dir = Path(__file__).parent.parent / "temp" / "pdf_cache"
        else:
            self.cache_dir = Path(cache_dir)
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, pdf_path: str) -> Path:
        """Generate cache file path based on PDF path hash."""
        # Use hash of path to avoid filesystem issues
        path_hash = hashlib.md5(pdf_path.encode()).hexdigest()
        return self.cache_dir / f"{path_hash}.txt"
    
    def _get_metadata_path(self, pdf_path: str) -> Path:
        """Generate metadata file path."""
        path_hash = hashlib.md5(pdf_path.encode()).hexdigest()
        return self.cache_dir / f"{path_hash}.json"
    
    def extract_and_cache(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract text from PDF and cache it.
        
        Args:
            pdf_path: Full path to the PDF file
            
        Returns:
            Dict with success status and metadata
        """
        try:
            path = Path(pdf_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {pdf_path}",
                    "cached_path": None
                }
            
            # Extract text
            doc = pymupdf.open(pdf_path)
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
            
            full_text = "\n\n".join(text_parts)
            page_count = len(doc)
            doc.close()
            
            # Cache the extracted text
            cache_path = self._get_cache_path(pdf_path)
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            # Save metadata with timestamp
            from datetime import datetime
            metadata = {
                "original_path": pdf_path,
                "filename": path.name,
                "pages": page_count,
                "cached_at": datetime.now().isoformat(),
                "cached_path": str(cache_path)
            }
            
            metadata_path = self._get_metadata_path(pdf_path)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            return {
                "success": True,
                "cached_path": str(cache_path),
                "filename": path.name,
                "pages": page_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "cached_path": None
            }
    
    def get_cached_text(self, pdf_path: str) -> Optional[str]:
        """
        Get cached text for a PDF file.
        
        Args:
            pdf_path: Original PDF file path
            
        Returns:
            Cached text content or None if not cached
        """
        cache_path = self._get_cache_path(pdf_path)
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def is_cached(self, pdf_path: str, ttl_minutes: int = 15) -> bool:
        """
        Check if PDF text is cached and not expired.
        
        Args:
            pdf_path: Original PDF file path
            ttl_minutes: Time-to-live in minutes (default 15)
            
        Returns:
            True if cached and not expired, False otherwise
        """
        cache_path = self._get_cache_path(pdf_path)
        metadata_path = self._get_metadata_path(pdf_path)
        
        if not cache_path.exists() or not metadata_path.exists():
            return False
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            from datetime import datetime, timedelta
            cached_time = datetime.fromisoformat(metadata.get('cached_at'))
            expiry_time = cached_time + timedelta(minutes=ttl_minutes)
            
            return datetime.now() < expiry_time
        except Exception:
            return False
    
    def clear_cache(self):
        """Clear all cached PDF text."""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)


# Global instance
pdf_extractor = PDFExtractor()
