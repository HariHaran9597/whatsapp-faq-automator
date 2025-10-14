# backend/voice_transcriber.py (Simplified)

from faster_whisper import WhisperModel
import requests
from pathlib import Path
import os

from backend.config import settings

TEMP_AUDIO_PATH = Path("data/temp_audio")
TEMP_AUDIO_PATH.mkdir(parents=True, exist_ok=True)

print("Loading Whisper model...")
try:
    WHISPER_MODEL = WhisperModel("base", device="cpu", compute_type="int8")
    print("Whisper model loaded successfully.")
except Exception as e:
    WHISPER_MODEL = None
    print(f"Error loading Whisper model: {e}")

async def transcribe_audio(media_url: str) -> str:
    if not WHISPER_MODEL:
        return "Voice transcription service is currently unavailable."

    try:
        # Step A: Download the audio file with authentication
        auth_creds = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        audio_content = requests.get(media_url, auth=auth_creds).content
        
        if not audio_content:
            raise ValueError("Downloaded audio content is empty.")
            
        # Step B: Save the original .ogg file
        ogg_path = TEMP_AUDIO_PATH / "temp_audio.ogg"
        with open(ogg_path, "wb") as f:
            f.write(audio_content)
        print(f"Audio downloaded to {ogg_path}")

        # Step C: Transcribe the .ogg file DIRECTLY
        segments, _ = WHISPER_MODEL.transcribe(str(ogg_path), beam_size=5)
        
        transcribed_text = " ".join([segment.text for segment in segments])
        print(f"Transcription complete: '{transcribed_text}'")

        # Step D: Clean up the temporary file
        os.remove(ogg_path)

        return transcribed_text.strip()

    except Exception as e:
        print(f"Error during audio transcription: {e}")
        return "Sorry, I had trouble understanding the audio. Could you please try again?"