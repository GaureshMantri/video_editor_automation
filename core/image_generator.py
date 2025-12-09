"""Image generator using DALL-E"""
import time
from pathlib import Path
from typing import Optional
import requests

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from ..config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__, settings.LOG_FILE, settings.LOG_LEVEL)

class ImageGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        if OpenAI is None:
            raise ImportError("openai package required")
        self.client = OpenAI(api_key=self.api_key)
        self.output_dir = settings.TEMP_DIR / "generated_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Image generator initialized")
    
    def generate_image(self, prompt: str, output_name: str = None, size: str = None, quality: str = None) -> Optional[Path]:
        size = size or settings.DALLE_SIZE
        quality = quality or settings.DALLE_QUALITY
        logger.info(f"Generating image: {prompt[:50]}...")
        try:
            response = self.client.images.generate(
                model=settings.DALLE_MODEL,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1
            )
            image_url = response.data[0].url
            image_data = requests.get(image_url).content
            if output_name:
                filename = f"{output_name}.png"
            else:
                timestamp = int(time.time() * 1000)
                filename = f"generated_{timestamp}.png"
            output_path = self.output_dir / filename
            with open(output_path, 'wb') as f:
                f.write(image_data)
            logger.info(f"Image generated successfully: {output_path.name}")
            return output_path
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return None
    
    def generate_from_analysis(self, analysis_result: dict) -> Optional[Path]:
        if not analysis_result.get("needs_visualization"):
            return None
        prompt = analysis_result.get("image_prompt")
        if not prompt:
            return None
        segment_id = analysis_result.get("segment_id", "unknown")
        output_name = f"segment_{segment_id}"
        return self.generate_image(prompt, output_name)

