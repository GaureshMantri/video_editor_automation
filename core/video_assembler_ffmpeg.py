"""FFmpeg-based video assembler with proper transitions and continuous audio"""
import subprocess
import shutil
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont

from ..config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__, settings.LOG_FILE, settings.LOG_LEVEL)

class FFmpegVideoAssembler:
    """Video assembler using FFmpeg for transitions and OpenCV for text"""
    
    def __init__(self):
        self.temp_dir = settings.TEMP_DIR / "ffmpeg_assembly"
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        logger.info("FFmpeg video assembler initialized")
    
    def get_video_info(self, video_path: Path) -> Dict:
        """Get video metadata using FFprobe"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,r_frame_rate,duration',
            '-of', 'json',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        import json
        data = json.loads(result.stdout)
        stream = data['streams'][0]
        
        # Parse frame rate
        fps_parts = stream['r_frame_rate'].split('/')
        fps = float(fps_parts[0]) / float(fps_parts[1])
        
        return {
            'width': int(stream['width']),
            'height': int(stream['height']),
            'fps': fps,
            'duration': float(stream.get('duration', 0))
        }
    
    def create_video_segment_with_fade(self, video_path: Path, start: float, end: float, 
                                       output_path: Path, fade_in: bool = False, 
                                       fade_out: bool = False) -> Path:
        """Extract video segment with optional fade effects"""
        duration = end - start
        fade_duration = 0.15
        
        # Build filter complex for fades
        filters = []
        if fade_in:
            filters.append(f"fade=t=in:st={start}:d={fade_duration}")
        if fade_out:
            filters.append(f"fade=t=out:st={end-fade_duration}:d={fade_duration}")
        
        filter_str = ','.join(filters) if filters else "null"
        
        cmd = [
            'ffmpeg', '-y', '-i', str(video_path),
            '-ss', str(start), '-t', str(duration),
            '-vf', filter_str,
            '-an',  # No audio
            '-c:v', 'libx264', '-preset', 'fast',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    
    def create_image_segment_with_transition(self, image_path: Path, duration: float, 
                                             video_size: Tuple[int, int], fps: float,
                                             output_path: Path, transition_type: str = "fade") -> Path:
        """Create video from image with various transitions"""
        trans_duration = 0.2
        
        # Resize image to match video
        img = Image.open(image_path)
        img_resized = img.resize(video_size, Image.Resampling.LANCZOS)
        temp_img = self.temp_dir / f"temp_{output_path.stem}.png"
        img_resized.save(temp_img)
        
        # Choose transition filter based on type
        if transition_type == "fade":
            vf = f"fade=t=in:st=0:d={trans_duration},fade=t=out:st={duration-trans_duration}:d={trans_duration}"
        elif transition_type == "slide_left":
            # Slide from right to left
            vf = f"split[main][tmp];[tmp]crop=iw:ih:0:0,fade=t=in:st=0:d={trans_duration}[fg];[main][fg]overlay=x='if(lt(t,{trans_duration}),W*(1-t/{trans_duration}),0)':y=0,fade=t=out:st={duration-trans_duration}:d={trans_duration}"
        elif transition_type == "slide_right":
            # Slide from left to right
            vf = f"split[main][tmp];[tmp]crop=iw:ih:0:0,fade=t=in:st=0:d={trans_duration}[fg];[main][fg]overlay=x='if(lt(t,{trans_duration}),-W*(1-t/{trans_duration}),0)':y=0,fade=t=out:st={duration-trans_duration}:d={trans_duration}"
        elif transition_type == "zoom":
            # Zoom in effect
            vf = f"zoompan=z='if(lt(time,{trans_duration}),1+(time/{trans_duration})*0.2,1.2)':d={int(duration*fps)}:s={video_size[0]}x{video_size[1]},fade=t=out:st={duration-trans_duration}:d={trans_duration}"
        elif transition_type == "wipe":
            # Wipe from top
            vf = f"fade=t=in:st=0:d={trans_duration},fade=t=out:st={duration-trans_duration}:d={trans_duration}"
        else:
            vf = f"fade=t=in:st=0:d={trans_duration},fade=t=out:st={duration-trans_duration}:d={trans_duration}"
        
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', str(temp_img),
            '-vf', vf,
            '-t', str(duration),
            '-r', str(fps),
            '-c:v', 'libx264', '-preset', 'fast', '-pix_fmt', 'yuv420p',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    
    def concatenate_videos(self, video_paths: List[Path], output_path: Path) -> Path:
        """Concatenate videos using FFmpeg concat demuxer"""
        concat_file = self.temp_dir / "concat_list.txt"
        
        with open(concat_file, 'w') as f:
            for vp in video_paths:
                f.write(f"file '{vp.absolute()}'\n")
        
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    
    def add_audio_to_video(self, video_path: Path, audio_path: Path, output_path: Path) -> Path:
        """Add audio track to video (audio plays continuously)"""
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-i', str(audio_path),
            '-c:v', 'copy',
            '-c:a', 'aac', '-b:a', '192k',
            '-map', '0:v:0', '-map', '1:a:0',
            '-shortest',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    
    def render_text_on_frames(self, video_path: Path, text_segments: List[Dict], 
                              safe_zones_map: Dict, output_path: Path) -> Path:
        """Render word-by-word animated text using OpenCV"""
        from ..utils.text_renderer import TextRenderer
        
        text_renderer = TextRenderer()
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # FIX: Pre-calculate fixed position for each text segment (avoid jumping)
        segment_positions = {}
        for segment in text_segments:
            segment_id = id(segment)
            # Use middle of segment for position calculation
            mid_time = (segment['start'] + segment['end']) / 2
            segment_positions[segment_id] = self._get_safe_position(mid_time, safe_zones_map, (width, height))
            logger.debug(f"Text segment {segment['start']:.1f}-{segment['end']:.1f}: fixed position {segment_positions[segment_id]}")
        
        # Create writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        temp_output = self.temp_dir / f"temp_text_{output_path.name}"
        out = cv2.VideoWriter(str(temp_output), fourcc, fps, (width, height))
        
        frame_idx = 0
        
        logger.info(f"Rendering word-by-word text on {total_frames} frames")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            current_time = frame_idx / fps
            
            # Find which text segments are active and how many words to show
            for segment in text_segments:
                if segment['start'] <= current_time <= segment['end']:
                    text = segment['data'].get('text', '')
                    sentiment = segment['data'].get('sentiment', 'neutral')
                    font_size_mod = segment['data'].get('font_size_modifier', 1.0)
                    
                    # FIX: Build up text cumulatively (2 words at a time, keeping previous)
                    time_in_segment = current_time - segment['start']
                    words = text.split()
                    word_delay = settings.TEXT_WORD_DELAY
                    words_per_chunk = settings.TEXT_WORDS_PER_CHUNK
                    
                    # Calculate how many words to show (cumulative)
                    current_chunk = int(time_in_segment / word_delay)
                    total_words_to_show = min(len(words), (current_chunk + 1) * words_per_chunk)
                    
                    if total_words_to_show > 0:
                        # Build staggered multi-line text with indentation
                        visible_words = words[:total_words_to_show]
                        
                        # Create staggered lines (2 words per line with increasing indent)
                        lines = []
                        for i in range(0, len(visible_words), words_per_chunk):
                            line_words = visible_words[i:i+words_per_chunk]
                            indent = "    " * (i // words_per_chunk)  # Add indent for each line
                            lines.append(indent + ' '.join(line_words))
                        
                        partial_text = '\n'.join(lines)
                        
                        # FIX: Use pre-calculated fixed position for entire segment
                        safe_position = segment_positions[id(segment)]
                        
                        # Create text overlay
                        font_size = int(settings.TEXT_FONT_SIZE * font_size_mod)
                        text_img = text_renderer.create_text_image(
                            partial_text, (width, height), safe_position,
                            font_size=font_size, sentiment=sentiment
                        )
                        
                        if text_img:
                            # Convert PIL to OpenCV
                            text_overlay = np.array(text_img)
                            text_overlay = cv2.cvtColor(text_overlay, cv2.COLOR_RGBA2BGRA)
                            
                            # Blend with frame
                            alpha = text_overlay[:, :, 3] / 255.0
                            for c in range(3):
                                frame[:, :, c] = (1 - alpha) * frame[:, :, c] + alpha * text_overlay[:, :, c]
            
            out.write(frame)
            frame_idx += 1
            
            if frame_idx % 100 == 0:
                logger.info(f"Processed {frame_idx}/{total_frames} frames ({frame_idx*100//total_frames}%)")
        
        cap.release()
        out.release()
        
        # Re-encode to proper format
        cmd = [
            'ffmpeg', '-y', '-i', str(temp_output),
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        
        return output_path
    
    def _get_safe_position(self, timestamp: float, safe_zones_map: Dict, 
                          frame_size: Tuple[int, int]) -> Tuple[int, int]:
        """Get safe position - bottom area, avoiding faces"""
        # FIX: Use bottom 20% of frame for text, centered
        # This ensures text stays below faces even with multi-line staggered layout
        return (frame_size[0] // 2, int(frame_size[1] * 0.82))
    
    def assemble_final_video(self, original_video: Path, timeline: List[Dict],
                            text_segments: List[Dict], safe_zones_map: Dict,
                            output_path: Path) -> Path:
        """Assemble final video with continuous audio, transitions, and word-by-word text"""
        logger.info("Starting FFmpeg-based video assembly")
        
        video_info = self.get_video_info(original_video)
        video_size = (video_info['width'], video_info['height'])
        fps = video_info['fps']
        
        # Extract audio from original video
        audio_path = self.temp_dir / "original_audio.aac"
        cmd = ['ffmpeg', '-y', '-i', str(original_video), '-vn', '-c:a', 'copy', str(audio_path)]
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info("Extracted original audio")
        
        # Get image segments
        image_segments = [t for t in timeline if t['type'] in ['ai_image', 'custom_image']]
        image_segments.sort(key=lambda x: x['start'])
        
        # Build video segments with varied transitions
        segment_paths = []
        current_time = 0.0
        transitions = ["fade", "zoom", "slide_left", "slide_right", "wipe"]
        
        for i, img_seg in enumerate(image_segments):
            # Video before image
            if img_seg['start'] > current_time:
                logger.info(f"Creating video segment {current_time:.1f}s - {img_seg['start']:.1f}s")
                seg_path = self.temp_dir / f"video_seg_{i}.mp4"
                self.create_video_segment_with_fade(
                    original_video, current_time, img_seg['start'], seg_path,
                    fade_in=(i==0), fade_out=True
                )
                segment_paths.append(seg_path)
            
            # Image segment with varied transitions
            transition_type = transitions[i % len(transitions)]
            logger.info(f"Creating image segment {img_seg['start']:.1f}s - {img_seg['end']:.1f}s with {transition_type} transition")
            img_seg_path = self.temp_dir / f"image_seg_{i}.mp4"
            self.create_image_segment_with_transition(
                Path(img_seg['data']['image_path']),
                img_seg['end'] - img_seg['start'],
                video_size, fps, img_seg_path, transition_type
            )
            segment_paths.append(img_seg_path)
            current_time = img_seg['end']
        
        # Remaining video
        if current_time < video_info['duration']:
            logger.info(f"Creating final video segment {current_time:.1f}s - {video_info['duration']:.1f}s")
            seg_path = self.temp_dir / f"video_seg_final.mp4"
            self.create_video_segment_with_fade(
                original_video, current_time, video_info['duration'], seg_path,
                fade_in=True, fade_out=False
            )
            segment_paths.append(seg_path)
        
        # Concatenate all segments
        logger.info("Concatenating video segments")
        video_no_audio = self.temp_dir / "concatenated_no_audio.mp4"
        self.concatenate_videos(segment_paths, video_no_audio)
        
        # Add continuous audio
        logger.info("Adding continuous audio")
        video_with_audio = self.temp_dir / "with_audio.mp4"
        self.add_audio_to_video(video_no_audio, audio_path, video_with_audio)
        
        # Render word-by-word text overlays
        logger.info("Rendering word-by-word text overlays")
        self.render_text_on_frames(video_with_audio, text_segments, safe_zones_map, output_path)
        
        logger.info(f"✓ Final video assembled: {output_path}")
        return output_path

