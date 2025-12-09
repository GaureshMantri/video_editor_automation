# Video Editor Automation

AI-powered automated video editing with:
- Hindi to English audio translation
- AI-generated images at key moments (max 5 per 2 minutes)
- Each image displays for exactly 1 second
- Smart text overlays avoiding faces
- Proper audio sync maintained

## Quick Start

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-key"
python -m video_editor_automation.main --input video.mp4
```

## Features
- **Audio Translation**: Whisper translates Hindi to English
- **Smart Visualization**: GPT-4o analyzes content, DALL-E generates relevant images
- **Text Overlays**: Auto-positioned English text overlays
- **Audio Sync**: Proper frame replacement without audio issues

## Requirements
- Python 3.11+
- FFmpeg
- OpenAI API key

## Configuration
Edit `config/settings.py`:
- `MAX_IMAGES_PER_2_MINUTES = 5` - Limit images
- `IMAGE_DISPLAY_DURATION = 1.0` - Image duration in seconds
- `MIN_IMPORTANCE_SCORE = 8` - Threshold for image generation

## Output
- Edited video in `output/` folder
- Timeline JSON for review
- Processing log

