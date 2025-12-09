"""GPT-4 prompts for content analysis"""

CONTENT_ANALYSIS_PROMPT = """You are an expert video editor analyzing speech content to determine what should be visualized.

Analyze the following speech segment and determine:
1. Should this segment have a visual image overlay?
2. How important is visualization for this segment? (1-10 score)
3. If visualization is needed, what should the image show?

Speech segment: "{segment_text}"
Context (previous): "{context_before}"
Context (next): "{context_after}"

Consider:
- Is something concrete being described (people, places, objects, concepts)?
- Would an image significantly enhance viewer understanding?
- Is this moment important enough to warrant replacing video frames?
- Avoid generating images for abstract concepts or simple statements

Respond in JSON format:
{{
    "needs_visualization": true/false,
    "importance_score": 1-10,
    "reasoning": "brief explanation",
    "image_prompt": "detailed DALL-E prompt in English" or null,
    "image_description": "what the image should show" or null
}}

Be conservative - only suggest images that truly add value.
"""

TEXT_SUMMARIZATION_PROMPT = """You are creating on-screen text for a video (Instagram Reels format).

Speech segment: "{segment_text}"

Create a concise, impactful on-screen text that:
- Captures the key point in {max_length} characters or less
- Is easy to read quickly
- Split into 2-3 short lines max
- Emphasizes the most important information

Also analyze the sentiment and visual styling:

Respond in JSON format:
{{
    "english_text": "summarized text in English",
    "sentiment": "important/happy/sad/angry/neutral/excited",
    "font_size_modifier": 1.0-1.5,
    "emphasis_words": ["word1", "word2"],
    "text_position": "top/middle/bottom"
}}
"""

