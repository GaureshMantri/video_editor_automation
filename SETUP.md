# Setup Instructions

## Quick Setup

1. **Set your API key** (one of these methods):
   ```bash
   # Method 1: Environment variable (recommended)
   $env:OPENAI_API_KEY = "your-openai-api-key-here"
   
   # Method 2: Pass as parameter
   python -m video_editor_automation.main --input video.mp4 --api-key "your-key"
   ```

2. **Run the processor**:
   ```bash
   cd C:\Perforce\qa\ScalingDetector
   python -m video_editor_automation.main --input "path\to\video.mp4"
   ```

## What's Currently Running

Your video is processing in the background right now!
Check progress: `c:\Users\gmantri\.cursor\projects\c-Perforce-qa-ScalingDetector\terminals\9.txt`

## Key Fixes Applied
- ✅ Max 5 images per 2 minutes
- ✅ Each image exactly 1 second
- ✅ Proper audio sync with moviepy
- ✅ Text overlays working
- ✅ English translation from Hindi audio

## GitHub Status
- ✅ Repository: https://github.com/GaureshMantri/video_editor_automation
- ✅ Code pushed (commits: initial, moviepy fixes)
- ⚠️ API key blocked by GitHub security (use environment variable instead)

