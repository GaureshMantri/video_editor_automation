"""Face detector for smart text placement"""
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

from ..config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__, settings.LOG_FILE, settings.LOG_LEVEL)

@dataclass
class SafeZone:
    x: int
    y: int
    width: int
    height: int
    score: float

class FaceDetector:
    def __init__(self, model: str = "opencv"):
        self.model_type = model
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        logger.info("Face detector initialized: OpenCV Haar Cascade")
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        return [(x, y, w, h) for (x, y, w, h) in faces]
    
    def calculate_safe_zones(self, frame: np.ndarray, faces: List[Tuple[int, int, int, int]]) -> List[SafeZone]:
        h, w = frame.shape[:2]
        grid_h = h // 3
        grid_w = w // 3
        zones = []
        for row in range(3):
            for col in range(3):
                x = col * grid_w
                y = row * grid_h
                zone = SafeZone(x, y, grid_w, grid_h, score=100.0)
                for (fx, fy, fw, fh) in faces:
                    if self._rectangles_overlap(x, y, grid_w, grid_h, fx, fy, fw, fh):
                        overlap = self._calculate_overlap_percentage(x, y, grid_w, grid_h, fx, fy, fw, fh)
                        zone.score -= overlap
                if row == 1 and col == 1:
                    zone.score -= 10
                if row == 2:
                    zone.score += 15
                zone.score = max(0, min(100, zone.score))
                zones.append(zone)
        zones.sort(key=lambda z: z.score, reverse=True)
        return zones
    
    def _rectangles_overlap(self, x1: int, y1: int, w1: int, h1: int, x2: int, y2: int, w2: int, h2: int) -> bool:
        return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)
    
    def _calculate_overlap_percentage(self, x1: int, y1: int, w1: int, h1: int, x2: int, y2: int, w2: int, h2: int) -> float:
        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        intersection = x_overlap * y_overlap
        area1 = w1 * h1
        if area1 == 0:
            return 0
        return (intersection / area1) * 100
    
    def process_video(self, video_path: Path, interval: int = None) -> Dict[float, List[SafeZone]]:
        interval = interval or settings.FACE_DETECTION_INTERVAL
        logger.info(f"Processing video for face detection: {video_path.name}")
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        safe_zones_map = {}
        frame_count = 0
        processed_count = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count % interval == 0:
                    timestamp = frame_count / fps
                    faces = self.detect_faces(frame)
                    safe_zones = self.calculate_safe_zones(frame, faces)
                    safe_zones_map[timestamp] = safe_zones
                    processed_count += 1
                    if processed_count % 20 == 0:
                        logger.info(f"Processed {processed_count} frames ({(frame_count/total_frames)*100:.1f}%)")
                frame_count += 1
        finally:
            cap.release()
        logger.info(f"Face detection complete: analyzed {processed_count} frames")
        return safe_zones_map

