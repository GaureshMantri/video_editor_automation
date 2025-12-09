"""Video assembler using FFmpeg and MoviePy - WITH AUDIO SYNC FIXES"""
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple

# MoviePy 2.x imports
from moviepy import VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
from PIL import Image

from ..config import settings
from ..utils.logger import setup_logger
from ..utils.text_renderer import TextRenderer

logger = setup_logger(__name__, settings.LOG_FILE, settings.LOG_LEVEL)

class VideoAssembler:
    def __init__(self):
        self.text_renderer = TextRenderer()
        self.temp_dir = settings.TEMP_DIR / "assembly"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg not installed or not in PATH")
        logger.info("Video assembler initialized")
    
    def _check_ffmpeg(self) -> bool:
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def get_video_info(self, video_path: Path) -> Dict:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', str(video_path)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
            if not video_stream:
                raise ValueError("No video stream found")
            info = {
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'fps': eval(video_stream['r_frame_rate']),
                'duration': float(data['format']['duration']),
                'codec': video_stream['codec_name']
            }
            logger.info(f"Video info: {info['width']}x{info['height']} @ {info['fps']}fps, duration: {info['duration']:.2f}s")
            return info
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            raise
    
    def assemble_final_video(self, original_video: Path, timeline: List[Dict], text_segments: List[Dict],
                            safe_zones_map: Dict, output_path: Path) -> Path:
        """FIX: Proper audio sync with moviepy, 1 second images only"""
        logger.info("Starting final video assembly with audio sync fixes")
        video_info = self.get_video_info(original_video)
        video_size = (video_info['width'], video_info['height'])
        fps = video_info['fps']
        
        # Load original video
        video = VideoFileClip(str(original_video))
        
        # Get image segments
        image_segments = [t for t in timeline if t['type'] in ['ai_image', 'custom_image']]
        image_segments.sort(key=lambda x: x['start'])
        
        if not image_segments:
            # No images, just add text overlays
            final_video = self._add_text_overlays_moviepy(video, text_segments, safe_zones_map, output_path)
            video.close()
            return final_video
        
        # Build clips with images replacing exact 1-second sections
        clips = []
        current_time = 0
        
        for segment in image_segments:
            # Add video before image with crossfade
            if segment['start'] > current_time:
                video_clip = video.subclip(current_time, segment['start'])
                clips.append(video_clip)
            
            # Create 1-second image clip with fade transitions
            image_path = Path(segment['data']['image_path'])
            duration = segment['end'] - segment['start']  # Should be 1 second
            
            # Resize image to match video
            img = Image.open(image_path)
            img_resized = img.resize((video_size[0], video_size[1]), Image.Resampling.LANCZOS)
            resized_path = self.temp_dir / f"resized_{segment['start']}.png"
            img_resized.save(resized_path, quality=95)
            
            # Create image clip with fade in/out transitions
            image_clip = ImageClip(str(resized_path), duration=duration)
            image_clip = image_clip.with_fps(fps)
            
            # Add fade in/out effects using moviepy methods
            fade_duration = 0.3
            image_clip = image_clip.crossfadein(fade_duration).crossfadeout(fade_duration)
            
            clips.append(image_clip)
            current_time = segment['end']
        
        # Add remaining video
        if current_time < video.duration:
            clip = video.subclip(current_time, video.duration)
            clips.append(clip)
        
        # Concatenate - THIS MAINTAINS AUDIO SYNC
        logger.info("Concatenating clips with audio sync")
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Add text overlays with sentiment-based styling
        if text_segments:
            text_clips = []
            for i, segment in enumerate(text_segments):
                text = segment['data'].get('text', '')
                start = segment['start']
                end = segment['end']
                duration = end - start
                
                # Get styling from segment data
                sentiment = segment['data'].get('sentiment', 'neutral')
                font_size_mod = segment['data'].get('font_size_modifier', 1.0)
                position_vert = segment['data'].get('position_vertical', 'bottom')
                
                # Create text overlay with dynamic styling
                text_img_path = self.temp_dir / f"text_{i}.png"
                font_size = int(settings.TEXT_FONT_SIZE * font_size_mod)
                
                img = self.text_renderer.create_text_image(
                    text, frame_size=video_size, 
                    font_size=font_size, sentiment=sentiment, position_vertical=position_vert
                )
                if img:
                    img.save(text_img_path)
                    
                    # FIX: Fade in text progressively (moviepy 2.x API)
                    text_clip = (ImageClip(str(text_img_path))
                                .with_duration(duration)
                                .with_start(start)
                                .with_position('center')
                                .crossfadein(0.2))  # Fade in over 0.2 seconds
                    text_clips.append(text_clip)
            
            if text_clips:
                final_clip = CompositeVideoClip([final_clip] + text_clips)
        
        # Write final video
        logger.info("Writing final video with audio")
        final_clip.write_videofile(
            str(output_path),
            codec=settings.VIDEO_CODEC,
            audio_codec=settings.AUDIO_CODEC,
            fps=fps,
            logger=None
        )
        
        # Cleanup
        video.close()
        final_clip.close()
        
        logger.info(f"Video assembly complete: {output_path}")
        return output_path
    
    def _add_text_overlays_moviepy(self, video, text_segments: List[Dict], safe_zones_map: Dict, output_path: Path) -> Path:
        """Add text overlays when no images"""
        if not text_segments:
            video.write_videofile(str(output_path), codec=settings.VIDEO_CODEC, audio_codec=settings.AUDIO_CODEC, logger=None)
            return output_path
        
        frame_size = (video.w, video.h)
        text_clips = []
        
        for i, segment in enumerate(text_segments):
            text = segment['data'].get('text', '')
            start = segment['start']
            end = segment['end']
            duration = end - start
            
            text_img_path = self.temp_dir / f"text_{i}.png"
            position = (frame_size[0] // 2, int(frame_size[1] * 0.85))
            self.text_renderer.save_text_overlay(text, text_img_path, frame_size=frame_size, position=position)
            
            text_clip = ImageClip(str(text_img_path), duration=duration)
            text_clip = text_clip.with_start(start)
            text_clip = text_clip.with_position('center')
            text_clips.append(text_clip)
        
        final = CompositeVideoClip([video] + text_clips)
        final.write_videofile(str(output_path), codec=settings.VIDEO_CODEC, audio_codec=settings.AUDIO_CODEC, fps=video.fps, logger=None)
        final.close()
        return output_path

