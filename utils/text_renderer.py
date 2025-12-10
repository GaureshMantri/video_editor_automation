"""Text rendering for video overlays"""
from pathlib import Path
from typing import Tuple, Optional

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None

from ..config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__, settings.LOG_FILE, settings.LOG_LEVEL)

class TextRenderer:
    def __init__(self):
        if Image is None:
            raise ImportError("Pillow required. Install: pip install Pillow")
        self.font_path = self._get_font_path()
        logger.info(f"Text renderer initialized with font: {self.font_path}")
    
    def _get_font_path(self) -> Optional[Path]:
        font_locations = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
        for font_path in font_locations:
            if Path(font_path).exists():
                return Path(font_path)
        return None
    
    def create_text_image(self, text: str, frame_size: Tuple[int, int], position: Tuple[int, int] = None,
                         font_size: int = None, text_color: Tuple[int, int, int] = None,
                         stroke_color: Tuple[int, int, int] = None, stroke_width: int = None,
                         sentiment: str = "neutral", position_vertical: str = "bottom",
                         add_background: bool = True) -> Image:
        width, height = frame_size
        font_size = font_size or settings.TEXT_FONT_SIZE
        
        # FIX: Always use white text color (sentiment only affects background)
        text_color = (255, 255, 255)  # Always white
        stroke_color = (0, 0, 0)  # Always black stroke for readability
        stroke_width = stroke_width or settings.TEXT_STROKE_WIDTH
        
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            if self.font_path:
                font = ImageFont.truetype(str(self.font_path), font_size)
            else:
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    logger.warning("No Unicode font, skipping text")
                    return img
        except Exception as e:
            logger.warning(f"Font load failed: {e}, skipping text")
            return img
        
        # FIX: Position for portrait/reels format - bottom area with room for multi-line
        if position is None:
            position = (width // 2, int(height * 0.75))  # Higher up to accommodate multi-line staggered text
        
        # FIX: Text is already formatted with newlines and indentation
        # Just use it as-is for multi-line staggered display
        wrapped_text = text
        
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align='center')
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # FIX: Ensure text stays within frame boundaries (strict)
        x = position[0] - text_width // 2
        y = position[1] - text_height // 2
        
        # Clamp to safe boundaries (5% margin from edges)
        margin = int(width * 0.05)
        x = max(margin, min(x, width - text_width - margin))
        y = max(margin, min(y, height - text_height - margin))
        
        # FIX: Draw emotion-based background FIRST
        if add_background and sentiment != "neutral":
            padding = 15
            bg_opacity = 180
            
            # Choose color based on sentiment
            if sentiment in ["sad", "angry", "worried"]:
                bg_color = (200, 50, 50, bg_opacity)  # Red for negative
            elif sentiment in ["happy", "excited", "important", "grateful"]:
                bg_color = (50, 180, 50, bg_opacity)  # Green for positive
            else:
                bg_color = (40, 40, 40, bg_opacity)  # Dark grey fallback
            
            draw.rounded_rectangle(
                [(x - padding, y - padding), (x + text_width + padding, y + text_height + padding)],
                fill=bg_color,
                radius=10
            )
        
        # Draw text shadow
        if settings.TEXT_SHADOW:
            shadow_x = x + settings.TEXT_SHADOW_OFFSET[0]
            shadow_y = y + settings.TEXT_SHADOW_OFFSET[1]
            draw.multiline_text((shadow_x, shadow_y), wrapped_text, font=font, fill=(0, 0, 0, 180), align='center')
        
        # Draw text on top
        draw.multiline_text((x, y), wrapped_text, font=font, fill=(*text_color, 255), 
                            stroke_width=stroke_width, stroke_fill=(*stroke_color, 255), align='center')
        
        return img
    
    def save_text_overlay(self, text: str, output_path: Path, **kwargs) -> Path:
        img = self.create_text_image(text, **kwargs)
        if img:
            img.save(output_path)
            logger.debug(f"Text overlay saved: {output_path.name}")
        else:
            logger.warning(f"Failed to create text image for: {text[:30]}")
        return output_path

