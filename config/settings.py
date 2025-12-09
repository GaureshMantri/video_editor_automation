"""
Configuration settings for Video Editor Automation
"""
import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

# Create directories if they don't exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# API Keys (set via environment variable or pass with --api-key)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Content Analysis Settings
MIN_IMPORTANCE_SCORE = 8  # Only generate images for scores >= 8 (more selective)
MAX_IMAGES_PER_2_MINUTES = 5  # Maximum 5 images per 2 minutes
IMAGE_DISPLAY_DURATION = 1.0  # Each image displays for exactly 1 second
CONTEXT_WINDOW_SECONDS = 30
MAX_TEXT_LENGTH = 60

# Text Display Settings
TEXT_FONT_SIZE = 48
TEXT_COLOR = (255, 255, 255)
TEXT_STROKE_COLOR = (0, 0, 0)
TEXT_STROKE_WIDTH = 3
TEXT_SHADOW = True
TEXT_SHADOW_OFFSET = (2, 2)
TEXT_BACKGROUND_OPACITY = 0.7

# Face Detection Settings
FACE_DETECTION_INTERVAL = 5
FACE_DETECTION_MODEL = "opencv"
SAFE_ZONE_THRESHOLD = 70

# Image Generation Settings
DALLE_MODEL = "dall-e-3"
DALLE_QUALITY = "standard"
DALLE_SIZE = "1024x1024"
IMAGE_CACHE_ENABLED = True

# Video Processing Settings
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
VIDEO_BITRATE = "5000k"
AUDIO_BITRATE = "192k"

# Transition Settings
TRANSITION_DURATION = 0.5

# Logging Settings
LOG_LEVEL = "INFO"
LOG_FILE = OUTPUT_DIR / "processing.log"

# Cache Settings
CACHE_TRANSCRIPTION = True
CACHE_ANALYSIS = True
CACHE_IMAGES = True
CACHE_FACE_DETECTION = True

