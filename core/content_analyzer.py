"""Content analyzer using GPT-4o"""
import json
from typing import Dict, List

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from ..config import settings, prompts
from ..utils.logger import setup_logger

logger = setup_logger(__name__, settings.LOG_FILE, settings.LOG_LEVEL)

class ContentAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        if OpenAI is None:
            raise ImportError("openai package required")
        self.client = OpenAI(api_key=self.api_key)
        logger.info("Content analyzer initialized")
    
    def analyze_segment(self, segment: Dict, context_before: str = "", context_after: str = "") -> Dict:
        segment_text = segment.get("text", "")
        logger.debug(f"Analyzing segment: {segment_text[:50]}...")
        prompt = prompts.CONTENT_ANALYSIS_PROMPT.format(
            segment_text=segment_text,
            context_before=context_before,
            context_after=context_after
        )
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert video editor analyzing content for visualization opportunities."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            result = json.loads(response.choices[0].message.content)
            result["segment_id"] = segment.get("id")
            result["start_time"] = segment.get("start")
            result["end_time"] = segment.get("end")
            result["original_text"] = segment_text
            logger.debug(f"Analysis result - Needs viz: {result.get('needs_visualization')}, Score: {result.get('importance_score')}")
            return result
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return {
                "needs_visualization": False,
                "importance_score": 0,
                "reasoning": f"Analysis failed: {str(e)}",
                "image_prompt": None,
                "image_description": None,
                "segment_id": segment.get("id"),
                "start_time": segment.get("start"),
                "end_time": segment.get("end"),
                "original_text": segment_text
            }
    
    def summarize_for_text_overlay(self, segment: Dict, max_length: int = None) -> Dict:
        max_length = max_length or settings.MAX_TEXT_LENGTH
        segment_text = segment.get("text", "")
        logger.debug(f"Summarizing text: {segment_text[:50]}...")
        prompt = prompts.TEXT_SUMMARIZATION_PROMPT.format(
            segment_text=segment_text,
            max_length=max_length
        )
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at creating concise on-screen text."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5
            )
            result = json.loads(response.choices[0].message.content)
            logger.debug(f"Text summarized: {result.get('english_text', '')[:30]}...")
            return result
        except Exception as e:
            logger.error(f"Text summarization failed: {e}")
            return {
                "english_text": segment_text[:max_length],
                "emphasis_words": []
            }
    
    def batch_analyze_segments(self, segments: List[Dict], context_window: int = 2) -> List[Dict]:
        logger.info(f"Batch analyzing {len(segments)} segments")
        results = []
        for i, segment in enumerate(segments):
            context_before = ""
            context_after = ""
            if i > 0:
                context_segments = segments[max(0, i-context_window):i]
                context_before = " ".join([s.get("text", "") for s in context_segments])
            if i < len(segments) - 1:
                context_segments = segments[i+1:min(len(segments), i+context_window+1)]
                context_after = " ".join([s.get("text", "") for s in context_segments])
            analysis = self.analyze_segment(segment, context_before, context_after)
            results.append(analysis)
            if (i + 1) % 10 == 0:
                logger.info(f"Analyzed {i+1}/{len(segments)} segments")
        
        # Sort by importance
        results.sort(key=lambda x: x.get("importance_score", 0), reverse=True)
        
        # FIX: Take top 5 if many suggested, minimum 3 guaranteed
        visualization_candidates = [r for r in results if r.get("needs_visualization")]
        
        if len(visualization_candidates) >= settings.MAX_IMAGES_TOTAL:
            # Take top 5
            filtered_results = visualization_candidates[:settings.MAX_IMAGES_TOTAL]
        elif len(visualization_candidates) >= settings.MIN_IMAGES_GUARANTEED:
            # Take what we have (between 3-5)
            filtered_results = visualization_candidates
        else:
            # Guarantee minimum 3 even if scores are low
            filtered_results = results[:settings.MIN_IMAGES_GUARANTEED]
        
        logger.info(f"Analysis complete: {len(filtered_results)} images selected (from {len(visualization_candidates)} candidates)")
        return filtered_results

