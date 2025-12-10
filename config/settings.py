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
MIN_IMPORTANCE_SCORE = 6  # Lower threshold, we'll select top ones
MAX_IMAGES_TOTAL = 5  # Take top 5 images
MIN_IMAGES_GUARANTEED = 3  # Minimum 3 images even if low scores
IMAGE_DISPLAY_DURATION = 2.0  # Each image displays for exactly 2 seconds
CONTEXT_WINDOW_SECONDS = 30
MAX_TEXT_LENGTH = 60

# Text Display Settings
TEXT_FONT_SIZE = 42  # Optimized for phone/reels format
TEXT_STROKE_WIDTH = 3  # Stroke for better visibility
TEXT_SHADOW = True
TEXT_SHADOW_OFFSET = (2, 2)
TEXT_BACKGROUND_OPACITY = 0.8
TEXT_ANIMATION = "word_by_word"  # Animate text appearance
TEXT_WORD_DELAY = 0.35  # Seconds between words appearing (slower, smoother)
TEXT_MAX_WORDS_VISIBLE = 6  # Max words visible at once (rolling window)

# Sentiment-based colors (RGB)
SENTIMENT_COLORS = {
    "important": (255, 215, 0),      # Gold/Yellow
    "happy": (0, 255, 127),          # Green
    "sad": (100, 149, 237),          # Blue
    "angry": (255, 69, 0),           # Red
    "neutral": (255, 255, 255),      # White
    "excited": (255, 105, 180)       # Pink
}

# Vertical positioning for portrait videos (reels format)
TEXT_POSITION_TOP = 0.15     # 15% from top
TEXT_POSITION_BOTTOM = 0.75  # 75% from top (leaving space for bottom UI)
TEXT_POSITION_MIDDLE = 0.5   # Middle

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

