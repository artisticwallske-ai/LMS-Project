
import os
from faster_whisper import WhisperModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STTService:
    # Upgraded to multilingual "base" to support both English and Kiswahili
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        logger.info(f"Loading Whisper model: {model_size} on {device}...")
        try:
            # Check if CUDA is available, otherwise force CPU
            import torch
            if torch.cuda.is_available():
                device = "cuda"
                compute_type = "float16" # faster on GPU
            else:
                device = "cpu"
                compute_type = "int8"
            
            logger.info(f"Using device: {device}, compute_type: {compute_type}")
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None

    def transcribe(self, audio_path: str, language: str = None) -> str:
        if not self.model:
            raise RuntimeError("Whisper model not initialized.")
        
        try:
            # Optimize for speed:
            # beam_size=1 (greedy decoding) - faster
            # vad_filter=True - ignores silence - faster
            # language=None - auto-detect (supports Swahili 'sw')
            kwargs = {
                "beam_size": 1,
                "vad_filter": True
            }
            if language:
                kwargs["language"] = language
                
            segments, info = self.model.transcribe(
                audio_path, 
                **kwargs
            )
            
            # segments is a generator, so we iterate
            text = " ".join([segment.text for segment in segments]).strip()
            logger.info(f"Transcription result: '{text}' (prob: {info.language_probability:.2f})")
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise e

# Singleton instance
stt_service = None

def get_stt_service():
    global stt_service
    if stt_service is None:
        stt_service = STTService()
    return stt_service
