# backend/voice_transcriber.py

from faster_whisper import WhisperModel
import requests
from pathlib import Path
from pydub import AudioSegment
import os

# --- NEW IMPORT ---
# Import the settings that now contain our Twilio keys
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
        # --- Step A: Download the audio file (IMPROVED WITH AUTHENTICATION) ---
        # We now use our Twilio credentials to log in and download the protected media file.
        auth_creds = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        audio_content = requests.get(media_url, auth=auth_creds).content
        
        # Check if the download was successful
        if not audio_content:
            raise ValueError("Downloaded audio content is empty.")
            
        ogg_path = TEMP_AUDIO_PATH / "temp_audio.ogg"
        with open(ogg_path, "wb") as f:
            f.write(audio_content)

        # --- Step B: Convert .ogg to .wav ---
        wav_path = TEMP_AUDIO_PATH / "temp_audio.wav"
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")
        print(f"Audio converted and saved to {wav_path}")

        # --- Step C: Transcribe the .wav file ---
        segments, _ = WHISPER_MODEL.transcribe(str(wav_path), beam_size=5)
        transcribed_text = " ".join([segment.text for segment in segments])
        print(f"Transcription complete: '{transcribed_text}'")

        # --- Step D: Clean up temporary files ---
        os.remove(ogg_path)
        os.remove(wav_path)

        return transcribed_text.strip()

    except Exception as e:
        print(f"Error during audio transcription: {e}")
        return "Sorry, I had trouble understanding the audio. Could you please try again?"