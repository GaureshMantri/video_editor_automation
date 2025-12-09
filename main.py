"""Main CLI interface for Video Editor Automation - WITH ALL FIXES"""
import argparse
import sys
from pathlib import Path

from .config import settings
from .utils.logger import setup_logger, log_section
from .utils.cache_manager import CacheManager
from .core.audio_processor import AudioProcessor
from .core.content_analyzer import ContentAnalyzer
from .core.face_detector import FaceDetector
from .core.image_generator import ImageGenerator
from .core.timeline_manager import TimelineManager
from .core.video_assembler import VideoAssembler

logger = setup_logger(__name__, settings.LOG_FILE, settings.LOG_LEVEL)

class VideoEditorCLI:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.cache = CacheManager(settings.CACHE_DIR)
        logger.info("Video Editor Automation initialized")
    
    def process_video(self, video_path: Path, skip_cache: bool = False) -> Path:
        log_section(logger, f"Processing Video: {video_path.name}")
        
        # Phase 1: Audio Processing (English translation)
        log_section(logger, "Phase 1: Audio Extraction & Translation")
        audio_processor = AudioProcessor(api_key=self.api_key)
        
        cached_transcription = None if skip_cache else self.cache.load_transcription(str(video_path))
        if cached_transcription:
            logger.info("Using cached transcription")
            transcription_data = cached_transcription
        else:
            audio_path = audio_processor.extract_audio(video_path)
            try:
                translation = audio_processor.translate_to_english(audio_path)
                transcription_data = {"hindi": None, "english": translation}
            finally:
                if audio_path.exists():
                    audio_path.unlink()
            if settings.CACHE_TRANSCRIPTION:
                self.cache.save_transcription(str(video_path), transcription_data)
        
        english_segments = transcription_data['english']['segments']
        if not english_segments:
            logger.warning("No segments found")
            phrases = []
        else:
            phrases = audio_processor.get_phrases_from_segments(english_segments)
        logger.info(f"Created {len(phrases)} phrases for display")
        
        # Phase 2: Content Analysis (FIX: max 5 images per 2 minutes)
        log_section(logger, "Phase 2: Content Analysis")
        content_analyzer = ContentAnalyzer(api_key=self.api_key)
        
        if english_segments:
            visualization_results = content_analyzer.batch_analyze_segments(english_segments)
        else:
            visualization_results = []
        logger.info(f"Found {len(visualization_results)} segments needing visualization")
        
        # Phase 3: Face Detection
        log_section(logger, "Phase 3: Face Detection & Safe Zones")
        face_detector = FaceDetector(model=settings.FACE_DETECTION_MODEL)
        
        cached_face_data = None if skip_cache else self.cache.load_face_detection(str(video_path))
        if cached_face_data:
            logger.info("Using cached face detection data")
            safe_zones_map = cached_face_data
        else:
            safe_zones_map = face_detector.process_video(video_path)
            if settings.CACHE_FACE_DETECTION:
                self.cache.save_face_detection(str(video_path), safe_zones_map)
        
        # Phase 4: Image Generation
        log_section(logger, "Phase 4: Image Generation")
        image_generator = ImageGenerator(api_key=self.api_key)
        
        generated_images = {}
        for analysis in visualization_results:
            prompt = analysis.get('image_prompt')
            if not prompt:
                continue
            segment_id = analysis['segment_id']
            cached_image = None if skip_cache else self.cache.load_image(prompt)
            if cached_image:
                logger.info(f"Using cached image for segment {segment_id}")
                generated_images[segment_id] = cached_image
            else:
                image_path = image_generator.generate_from_analysis(analysis)
                if image_path and settings.IMAGE_CACHE_ENABLED:
                    cached_path = self.cache.save_image(prompt, image_path)
                    generated_images[segment_id] = cached_path
                elif image_path:
                    generated_images[segment_id] = image_path
        logger.info(f"Generated/cached {len(generated_images)} images")
        
        # Phase 5: Timeline Management (FIX: 1 second per image)
        log_section(logger, "Phase 5: Timeline Management")
        timeline_manager = TimelineManager()
        
        for phrase in phrases:
            text_data = content_analyzer.summarize_for_text_overlay(phrase)
            display_text = text_data.get('english_text', phrase.get('text', ''))
            timeline_manager.add_text_segment(phrase['start'], phrase['end'], {'text': display_text})
        
        # FIX: Each image exactly 1 second
        for segment_id, image_path in generated_images.items():
            analysis = next((a for a in visualization_results if a['segment_id'] == segment_id), None)
            if analysis:
                start_time = analysis['start_time']
                end_time = start_time + settings.IMAGE_DISPLAY_DURATION  # 1 second
                timeline_manager.add_ai_image_segment(start_time, end_time, image_path, analysis)
        
        stats = timeline_manager.get_statistics()
        logger.info(f"Timeline stats: {stats}")
        
        video_assembler = VideoAssembler()
        video_info = video_assembler.get_video_info(video_path)
        render_timeline = timeline_manager.build_render_timeline(video_info['duration'])
        
        timeline_export_path = settings.OUTPUT_DIR / f"{video_path.stem}_timeline.json"
        timeline_manager.export_timeline(timeline_export_path)
        
        # Phase 6: Video Assembly (FIX: proper audio sync)
        log_section(logger, "Phase 6: Final Video Assembly")
        output_path = settings.OUTPUT_DIR / f"{video_path.stem}_edited.mp4"
        
        text_segments = [{'start': s.start_time, 'end': s.end_time, 'data': s.data}
                        for s in timeline_manager.segments if s.segment_type == 'text']
        
        final_video = video_assembler.assemble_final_video(video_path, render_timeline, text_segments, safe_zones_map, output_path)
        
        log_section(logger, "Processing Complete!")
        logger.info(f"Output video: {final_video}")
        
        # Generate report
        report_path = settings.OUTPUT_DIR / f"{video_path.stem}_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"Video Editor Automation - Processing Report\\n{'='*60}\\n\\n")
            f.write(f"Input: {video_path.name}\\nOutput: {output_path.name}\\n\\n")
            f.write(f"Timeline Stats:\\n")
            for k, v in stats.items():
                f.write(f"- {k}: {v}\\n")
        
        return final_video

def main():
    parser = argparse.ArgumentParser(description="Automated Video Editor with AI")
    parser.add_argument('--input', '-i', type=Path, required=True, help='Input video file')
    parser.add_argument('--api-key', type=str, help='OpenAI API key')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    parser.add_argument('--skip-cache', action='store_true', help='Skip cache')
    
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: Input video not found: {args.input}")
        sys.exit(1)
    
    api_key = args.api_key or settings.OPENAI_API_KEY
    if not api_key:
        print("Error: OpenAI API key is required. Provide via --api-key or OPENAI_API_KEY env variable")
        sys.exit(1)
    
    settings.LOG_LEVEL = args.log_level
    
    cli = VideoEditorCLI(api_key=api_key)
    
    try:
        output_video = cli.process_video(args.input, skip_cache=args.skip_cache)
        print(f"\\n✓ Success! Output video: {output_video}\\n")
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        print(f"\\n✗ Error: {e}\\n")
        sys.exit(1)

if __name__ == '__main__':
    main()

