
import os
import torch
import torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
import logging
import uuid
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading Chatterbox Multilingual TTS on {self.device}...")
        try:
            # This will load the model from cache if downloaded, or download it if missing.
            # We expect the user to have run download_models.py first.
            self.model = ChatterboxMultilingualTTS.from_pretrained(device=self.device)
            self.sr = self.model.sr
            logger.info("Chatterbox Multilingual model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Chatterbox model: {e}")
            logger.warning("Ensure you have run 'python download_models.py' to download the model.")
            self.model = None

    def generate_audio(self, text: str, language: str = "en") -> str:
        """
        Generates audio from text and saves it to a temporary file.
        Returns the file path.
        """
        if not self.model:
            raise RuntimeError("TTS model not initialized. Did you run download_models.py?")
        
        # Determine language code for Chatterbox
        lang_id = language.lower()
        supported_langs = ["en", "sw", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "ko", "hu", "fi"]
        
        # Fallback for unsupported languages
        if lang_id not in supported_langs:
            logger.warning(f"Language {lang_id} not explicitly supported, defaulting to 'en'.")
            if lang_id not in ["en", "sw"]: 
                lang_id = "en"

        try:
            logger.info(f"Generating audio for text: '{text[:50]}...' in {lang_id}")
            wav = self.model.generate(text, language_id=lang_id)
            
            # Save to temporary file
            output_dir = os.path.join(settings.BASE_DIR, "static", "audio")
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"{uuid.uuid4()}.wav"
            filepath = os.path.join(output_dir, filename)
            
            torchaudio.save(filepath, wav.cpu(), self.sr)
            logger.info(f"Audio saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise e

# Singleton instance
tts_service = None

def get_tts_service():
    global tts_service
    if tts_service is None:
        tts_service = TTSService()
    return tts_service
