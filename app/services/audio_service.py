import os
import uuid
import logging
import tempfile
import time
from pathlib import Path
from typing import Optional, Union, BinaryIO
from gtts import gTTS
from openai import OpenAI
from ..config import settings

logger = logging.getLogger(__name__)

class AudioService:
    """Service for handling audio operations: download, transcribe, generate"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.temp_dir = tempfile.gettempdir()
        
    async def download_audio(self, audio_content: bytes, extension: str = "ogg") -> str:
        """Save audio bytes to a temporary file"""
        try:
            filename = os.path.join(self.temp_dir, f"{uuid.uuid4()}.{extension}")
            
            # Ensure the temp directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Write the audio content to file
            with open(filename, "wb") as f:
                f.write(audio_content)
                
            logger.info(f"Audio saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            raise
    
    async def transcribe_audio(self, audio_file: Union[str, BinaryIO]) -> str:
        """Transcribe audio using OpenAI's Whisper API"""
        try:
            # If we have a filename, open the file
            if isinstance(audio_file, str):
                with open(audio_file, "rb") as f:
                    transcription = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f
                    )
            # Otherwise use the file object directly
            else:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                
            logger.info("Audio transcription successful")
            return transcription.text
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise
    
    async def generate_audio(self, text: str, language: str = "pt") -> str:
        """Generate audio from text using gTTS"""
        try:
            # Create a unique filename
            filename = os.path.join(self.temp_dir, f"response_{uuid.uuid4()}.mp3")
            
            # Ensure the temp directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Generate the audio
            tts = gTTS(text=text, lang=language)
            tts.save(filename)
            
            logger.info(f"Audio generated and saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            raise
            
    async def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """Clean up temporary audio files older than specified hours"""
        try:
            count = 0
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            # Look for audio files in the temp directory
            for file_path in Path(self.temp_dir).glob("*.mp3"):
                # Check if the file is old enough to delete
                if (current_time - os.path.getmtime(file_path)) > max_age_seconds:
                    os.remove(file_path)
                    count += 1
                    
            # Also clean up OGG files
            for file_path in Path(self.temp_dir).glob("*.ogg"):
                if (current_time - os.path.getmtime(file_path)) > max_age_seconds:
                    os.remove(file_path)
                    count += 1
                    
            logger.info(f"Cleaned up {count} temporary audio files")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
            return 0