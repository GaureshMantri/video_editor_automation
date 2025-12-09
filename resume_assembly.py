"""Resume video assembly from cached data without re-running expensive API calls"""
import pickle
import sys
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from video_editor_automation.core.video_assembler import VideoAssembler
from video_editor_automation.utils.logger import setup_logger
from video_editor_automation.config import settings

logger = setup_logger(__name__, settings.LOG_FILE, settings.LOG_LEVEL)

def resume_assembly(video_path: Path, timeline_json: Path, face_cache_pkl: Path):
    """Resume video assembly using cached data"""
    
    # Load timeline
    with open(timeline_json, 'r') as f:
        timeline_data = json.load(f)
    
    # Load face detection cache
    with open(face_cache_pkl, 'rb') as f:
        safe_zones_map = pickle.load(f)
    
    # Extract segments from JSON structure and convert to expected format
    segments = timeline_data.get('segments', timeline_data)
    
    # Convert timeline format: 'start_time' -> 'start', 'end_time' -> 'end'
    render_timeline = []
    text_segments = []
    
    for seg in segments:
        converted_seg = {
            'start': seg['start_time'],
            'end': seg['end_time'],
            'type': seg['type'],
            'data': seg['data']
        }
        
        if seg['type'] in ['video', 'ai_image', 'custom_image']:
            render_timeline.append(converted_seg)
        elif seg['type'] == 'text':
            text_segments.append(converted_seg)
    
    logger.info(f"Loaded timeline: {len(render_timeline)} render segments, {len(text_segments)} text segments")
    
    # Assemble video
    video_assembler = VideoAssembler()
    output_path = settings.OUTPUT_DIR / f"{video_path.stem}_edited.mp4"
    
    logger.info("Starting video assembly from cached data...")
    final_video = video_assembler.assemble_final_video(
        video_path, render_timeline, text_segments, safe_zones_map, output_path
    )
    
    logger.info(f"✓ Video assembled: {final_video}")
    return final_video

if __name__ == "__main__":
    video_path = Path(r"C:\Users\gmantri\Downloads\WhatsApp Video 2025-12-06 at 22.53.28.mp4")
    timeline_json = Path("output/WhatsApp Video 2025-12-06 at 22.53.28_timeline.json")
    face_cache = Path("cache/face_detection/9497bf1bd64965b38d7b01f2302e1592.pkl")
    
    resume_assembly(video_path, timeline_json, face_cache)

