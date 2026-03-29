
import os
import logging
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from faster_whisper import WhisperModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def download_models():
    print("="*50)
    print("STARTING MODEL DOWNLOADS")
    print("This process may take a while depending on your internet connection.")
    print("="*50)

    # 1. Download Whisper Model
    try:
        model_size = "base.en"
        print(f"\n[1/2] Downloading Whisper Model ('{model_size}')...")
        # Just instantiating it triggers download
        WhisperModel(model_size, device="cpu", compute_type="int8")
        print("✅ Whisper Model downloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download Whisper model: {e}")
        print("❌ Whisper Model download failed.")

    # 2. Download Chatterbox Multilingual Model
    try:
        print(f"\n[2/2] Downloading Chatterbox Multilingual Model (~3.2GB)...")
        print("Please be patient. Do not close this window.")
        # Instantiating triggers download
        # Use CPU for download to avoid CUDA errors if not available during setup
        ChatterboxMultilingualTTS.from_pretrained(device="cpu")
        print("✅ Chatterbox Multilingual Model downloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download Chatterbox model: {e}")
        print("❌ Chatterbox Model download failed.")

    print("\n" + "="*50)
    print("DOWNLOAD PROCESS COMPLETE")
    print("="*50)

if __name__ == "__main__":
    download_models()
