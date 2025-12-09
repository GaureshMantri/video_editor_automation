"""Cache manager for storing processed data"""
import json
import pickle
import hashlib
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

class CacheManager:
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.transcription_dir = self.cache_dir / "transcriptions"
        self.analysis_dir = self.cache_dir / "analysis"
        self.images_dir = self.cache_dir / "images"
        self.face_detection_dir = self.cache_dir / "face_detection"
        
        for dir_path in [self.transcription_dir, self.analysis_dir, self.images_dir, self.face_detection_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def _generate_key(self, identifier: str) -> str:
        return hashlib.md5(identifier.encode()).hexdigest()
    
    def save_transcription(self, video_path: str, transcription_data: dict):
        key = self._generate_key(video_path)
        cache_file = self.transcription_dir / f"{key}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({"video_path": video_path, "timestamp": datetime.now().isoformat(), "data": transcription_data}, f, ensure_ascii=False, indent=2)
    
    def load_transcription(self, video_path: str) -> Optional[dict]:
        key = self._generate_key(video_path)
        cache_file = self.transcription_dir / f"{key}.json"
        if not cache_file.exists():
            return None
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)["data"]
    
    def save_image(self, image_prompt: str, image_path: Path) -> Path:
        import shutil
        key = self._generate_key(image_prompt)
        cached_path = self.images_dir / f"{key}{image_path.suffix}"
        shutil.copy2(image_path, cached_path)
        metadata_path = self.images_dir / f"{key}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({"prompt": image_prompt, "timestamp": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
        return cached_path
    
    def load_image(self, image_prompt: str) -> Optional[Path]:
        key = self._generate_key(image_prompt)
        for ext in ['.png', '.jpg', '.jpeg', '.webp']:
            cached_path = self.images_dir / f"{key}{ext}"
            if cached_path.exists():
                return cached_path
        return None
    
    def save_face_detection(self, video_path: str, detection_data: dict):
        key = self._generate_key(video_path)
        cache_file = self.face_detection_dir / f"{key}.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(detection_data, f)
    
    def load_face_detection(self, video_path: str) -> Optional[dict]:
        key = self._generate_key(video_path)
        cache_file = self.face_detection_dir / f"{key}.pkl"
        if not cache_file.exists():
            return None
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    def get_cache_info(self) -> dict:
        return {
            "transcriptions": len(list(self.transcription_dir.glob("*.json"))),
            "analysis": len(list(self.analysis_dir.glob("*.json"))),
            "images": len(list(self.images_dir.glob("*.png"))) + len(list(self.images_dir.glob("*.jpg"))),
            "face_detection": len(list(self.face_detection_dir.glob("*.pkl")))
        }

