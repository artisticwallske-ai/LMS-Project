import os
import uuid
import logging
import asyncio
import edge_tts
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        logger.info("Initializing Edge-TTS Service...")
        self.model = True # Mock flag to indicate service is "loaded"

    async def generate_audio(self, text: str, language: str = "en") -> str:
        """
        Generates audio from text using Edge-TTS and saves it to a temporary file.
        Returns the file path.
        """
        # Determine voice based on language
        # Using premium "Friendly/Positive" Kenyan Neural voices
        voice = "en-KE-AsiliaNeural" # Default English Kenyan Female
        
        if language and language.lower().startswith("sw"):
            voice = "sw-KE-ZuriNeural" # Default Swahili Kenyan Female
        elif language and language.lower() == "en":
            voice = "en-KE-AsiliaNeural"

        try:
            logger.info(f"Generating audio using Edge-TTS voice '{voice}' for text: '{text[:50]}...'")
            
            output_dir = os.path.join(settings.BASE_DIR, "static", "audio")
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"{uuid.uuid4()}.mp3" # edge-tts generates mp3 by default
            filepath = os.path.join(output_dir, filename)
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filepath)
            
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
