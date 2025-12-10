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
                         sentiment: str = "neutral", position_vertical: str = "bottom") -> Image:
        width, height = frame_size
        font_size = font_size or settings.TEXT_FONT_SIZE
        
        # FIX: Use sentiment-based color
        text_color = text_color or settings.SENTIMENT_COLORS.get(sentiment, settings.SENTIMENT_COLORS["neutral"])
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
        
        # FIX: Position for portrait/reels format - always bottom center for captions
        if position is None:
            position = (width // 2, int(height * 0.85))  # Bottom center (caption style)
        
        # FIX: Wrap text to multiple lines for better readability
        words = text.split()
        lines = []
        current_line = []
        max_width = int(width * 0.85)  # Use 85% of width for captions
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        wrapped_text = '\n'.join(lines)
        
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align='center')
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = position[0] - text_width // 2
        y = position[1] - text_height // 2
        
        if settings.TEXT_BACKGROUND_OPACITY > 0:
            padding = 20
            bg_opacity = int(255 * settings.TEXT_BACKGROUND_OPACITY)
            draw.rectangle([(x - padding, y - padding), (x + text_width + padding, y + text_height + padding)],
                         fill=(0, 0, 0, bg_opacity))
        
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

