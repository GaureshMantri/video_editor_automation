"""Audio processor using OpenAI Whisper"""
import subprocess
from pathlib import Path
from typing import Dict, List

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from ..config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__, settings.LOG_FILE, settings.LOG_LEVEL)

class AudioProcessor:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        if OpenAI is None:
            raise ImportError("openai package required")
        self.client = OpenAI(api_key=self.api_key)
        self.temp_dir = settings.TEMP_DIR
        logger.info("Audio processor initialized")
    
    def extract_audio(self, video_path: Path) -> Path:
        logger.info(f"Extracting audio from {video_path.name}")
        audio_path = self.temp_dir / f"{video_path.stem}_audio.mp3"
        cmd = ['ffmpeg', '-i', str(video_path), '-vn', '-acodec', 'libmp3lame', '-q:a', '2', '-y', str(audio_path)]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Audio extracted: {audio_path}")
            return audio_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            raise
    
    def translate_to_english(self, audio_path: Path) -> Dict:
        logger.info(f"Translating audio to English: {audio_path.name}")
        try:
            with open(audio_path, 'rb') as audio_file:
                translation = self.client.audio.translations.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            result = {"text": translation.text, "language": "en", "segments": []}
            if hasattr(translation, 'segments') and translation.segments:
                for segment in translation.segments:
                    result["segments"].append({
                        "id": segment.id,
                        "text": segment.text,
                        "start": segment.start,
                        "end": segment.end
                    })
            logger.info("Translation completed")
            return result
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise
    
    def get_phrases_from_segments(self, segments: List[Dict], max_duration: float = 5.0) -> List[Dict]:
        phrases = []
        current_phrase = {"text": "", "start": None, "end": None, "segment_ids": []}
        for segment in segments:
            if current_phrase["start"] is None:
                current_phrase["start"] = segment["start"]
            duration = segment["end"] - current_phrase["start"]
            if duration > max_duration and current_phrase["text"]:
                current_phrase["end"] = segment["start"]
                phrases.append(current_phrase.copy())
                current_phrase = {
                    "text": segment["text"],
                    "start": segment["start"],
                    "end": segment["end"],
                    "segment_ids": [segment["id"]]
                }
            else:
                if current_phrase["text"]:
                    current_phrase["text"] += " " + segment["text"]
                else:
                    current_phrase["text"] = segment["text"]
                current_phrase["end"] = segment["end"]
                current_phrase["segment_ids"].append(segment["id"])
        if current_phrase["text"]:
            phrases.append(current_phrase)
        logger.info(f"Created {len(phrases)} phrases from {len(segments)} segments")
        return phrases
