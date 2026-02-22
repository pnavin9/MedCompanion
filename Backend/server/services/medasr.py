"""MedASR model service for medical speech recognition.

Based on the working test_medasr_direct.py implementation, this service wraps the MedASR model
for use in the FastAPI server.
"""

import torch
import librosa
from pathlib import Path
from typing import Dict
from transformers import AutoModelForCTC, AutoProcessor
from server.config import settings
import time
import logging

logger = logging.getLogger(__name__)


def get_device():
    """Determine the best device for the model."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


class MedASRService:
    """Service for MedASR medical speech recognition."""
    
    def __init__(self):
        """Initialize the MedASR service."""
        self.device = get_device()
        self.model = None
        self.processor = None
        self.model_loaded = False
        self.model_name = getattr(settings, 'medasr_model_name', 'google/medasr')
        
    def load_model(self):
        """Load the MedASR model and processor."""
        if self.model_loaded:
            return
            
        logger.info(f"Loading MedASR model on {self.device}...")
        print(f"Loading MedASR model: {self.model_name} on {self.device}...")
        
        load_start = time.time()
        
        # Load processor
        self.processor = AutoProcessor.from_pretrained(self.model_name)
        
        # Load model (don't use device_map with transformers 5.0 + MPS, has bugs)
        self.model = AutoModelForCTC.from_pretrained(self.model_name)
        self.model = self.model.to(self.device)
        self.model.eval()
        
        self.model_loaded = True
        load_time = time.time() - load_start
        logger.info(f"MedASR model loaded successfully in {load_time:.2f}s")
        print(f"MedASR model loaded successfully in {load_time:.2f}s!")
        
    def transcribe_audio(self, audio_path: str) -> Dict[str, any]:
        """Transcribe audio file to text using MedASR.
        
        Args:
            audio_path: Path to audio file (wav, mp3, etc.)
            
        Returns:
            Dictionary with:
                - text: Transcribed text
                - success: Boolean indicating success
                - error: Error message if success is False
        """
        if not self.model_loaded:
            logger.info("[MEDASR] Model not loaded, loading now...")
            try:
                self.load_model()
            except Exception as e:
                logger.error(f"[MEDASR] Failed to load model: {e}")
                return {
                    "text": "",
                    "success": False,
                    "error": f"Failed to load MedASR model: {str(e)}"
                }
        
        try:
            transcribe_start = time.time()
            
            # Load and resample audio to 16kHz (MedASR requirement)
            t1 = time.time()
            audio, sr = librosa.load(audio_path, sr=16000)
            logger.info(f"[MEDASR] Loaded audio ({len(audio)/sr:.2f}s): {time.time()-t1:.3f}s")
            
            # Process audio with processor
            t2 = time.time()
            inputs = self.processor(
                audio,
                sampling_rate=sr,
                return_tensors="pt"
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            logger.info(f"[MEDASR] Processed inputs: {time.time()-t2:.3f}s")
            
            # Generate transcription
            t3 = time.time()
            with torch.no_grad():
                outputs = self.model.generate(**inputs)
            
            # Decode to text
            transcription = self.processor.batch_decode(outputs)[0]
            logger.info(f"[MEDASR] Generated transcription: {time.time()-t3:.3f}s")
            
            total_time = time.time() - transcribe_start
            logger.info(f"[MEDASR] Total transcription time: {total_time:.2f}s")
            
            return {
                "text": transcription,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[MEDASR] Transcription failed: {e}", exc_info=True)
            return {
                "text": "",
                "success": False,
                "error": str(e)
            }


# Global service instance
medasr_service = MedASRService()
