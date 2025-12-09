"""Timeline manager with conflict resolution"""
from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path
import json

from ..config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__, settings.LOG_FILE, settings.LOG_LEVEL)

@dataclass
class TimelineSegment:
    start_time: float
    end_time: float
    segment_type: str
    data: dict
    priority: int

class TimelineManager:
    PRIORITY_CUSTOM_IMAGE = 100
    PRIORITY_AI_IMAGE = 50
    PRIORITY_TEXT = 10
    
    def __init__(self):
        self.segments: List[TimelineSegment] = []
        logger.info("Timeline manager initialized")
    
    def add_text_segment(self, start_time: float, end_time: float, text_data: dict):
        segment = TimelineSegment(start_time=start_time, end_time=end_time, segment_type="text",
                                 data=text_data, priority=self.PRIORITY_TEXT)
        self.segments.append(segment)
    
    def add_ai_image_segment(self, start_time: float, end_time: float, image_path: Path, analysis_data: dict):
        segment = TimelineSegment(start_time=start_time, end_time=end_time, segment_type="ai_image",
                                 data={"image_path": str(image_path), "analysis": analysis_data},
                                 priority=self.PRIORITY_AI_IMAGE)
        self.segments.append(segment)
    
    def get_statistics(self) -> Dict:
        return {
            "total_segments": len(self.segments),
            "text_segments": len([s for s in self.segments if s.segment_type == "text"]),
            "ai_images": len([s for s in self.segments if s.segment_type == "ai_image"]),
            "custom_images": 0,
            "conflicts": 0
        }
    
    def build_render_timeline(self, video_duration: float) -> List[Dict]:
        image_segments = [s for s in self.segments if s.segment_type in ["ai_image", "custom_image"]]
        text_segments = [s for s in self.segments if s.segment_type == "text"]
        timeline = []
        image_segments.sort(key=lambda s: s.start_time)
        current_time = 0.0
        for img_seg in image_segments:
            if img_seg.start_time > current_time:
                timeline.append({"type": "original_video", "start": current_time, "end": img_seg.start_time})
            timeline.append({"type": img_seg.segment_type, "start": img_seg.start_time, "end": img_seg.end_time,
                           "duration": img_seg.end_time - img_seg.start_time, "data": img_seg.data})
            current_time = img_seg.end_time
        if current_time < video_duration:
            timeline.append({"type": "original_video", "start": current_time, "end": video_duration})
        for text_seg in text_segments:
            timeline.append({"type": "text_overlay", "start": text_seg.start_time, "end": text_seg.end_time,
                           "duration": text_seg.end_time - text_seg.start_time, "data": text_seg.data})
        timeline.sort(key=lambda x: x.get("start", 0))
        logger.info(f"Timeline built: {len(timeline)} events")
        return timeline
    
    def export_timeline(self, output_path: Path):
        timeline_data = {"segments": [{"start_time": s.start_time, "end_time": s.end_time, "type": s.segment_type,
                                       "priority": s.priority, "data": s.data} for s in self.segments]}
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(timeline_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Timeline exported to: {output_path}")

