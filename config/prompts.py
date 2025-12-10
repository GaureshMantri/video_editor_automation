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

TEXT_SUMMARIZATION_PROMPT = """You are creating impactful on-screen captions for a video (Instagram Reels format).

Speech segment: "{segment_text}"

IMPORTANT: Create meaningful captions that capture the ESSENCE and KEY MESSAGE, NOT word-by-word subtitles.

Examples:
- If speech is "Thank you so much Rucha ma'am, I couldn't have done this without you" → Caption: "Thank You Rucha Ma'am"
- If speech is "I was so confused and didn't know what to do" → Caption: "Lost & Confused"
- If speech is "After attending your workshop, I studied for 14 hours" → Caption: "14 Hours After Workshop!"

Guidelines:
- Maximum {max_length} characters
- Extract the KEY MESSAGE or emotion
- Make it punchy and memorable
- Use sentence case or title case
- 1-2 short lines maximum

Also analyze the sentiment (this determines background color):
- sad/angry/worried = RED background
- happy/excited/grateful/important = GREEN background  
- neutral = NO background

Respond in JSON format:
{{
    "english_text": "Key message or emotion (NOT subtitles)",
    "sentiment": "important/happy/sad/angry/neutral/excited/grateful/worried",
    "font_size_modifier": 1.0-1.5,
    "emphasis_words": ["word1", "word2"],
    "text_position": "bottom"
}}
"""

