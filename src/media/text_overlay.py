"""Generate text overlay images using Pillow for video compositing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

OVERLAY_DIR = Path("media/overlays")

# TikTok's UI covers the bottom ~20% of a 1920px-tall video.
# Nothing important should render below (height - TIKTOK_BOTTOM_SAFE_ZONE).
TIKTOK_BOTTOM_SAFE_ZONE = 384  # 20% of 1920

# Theme-based calls to action
THEME_CTAS = {
    "grief": "Share who you're remembering today",
    "retirement": "What's your new purpose? Tell us below",
    "health": "Drop a prayer request if you need healing",
    "faith-doubts": "What question is on your heart today?",
    "adult-children": "Share a prayer for your children below",
    "marriage-renewal": "Tag your spouse and share this blessing",
    "legacy": "What legacy are you building? Share below",
    "grandparenting": "Tell us about your grandchildren",
}


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a font, falling back to default if Georgia not available."""
    font_names = [
        "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ]

    for font_path in font_names:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            continue

    # Fallback to default
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines


def _draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str = "#FFFFFF",
    shadow_color: str = "#000000",
    shadow_offset: int = 3,
) -> None:
    """Draw text with a drop shadow for better readability."""
    x, y = position
    # Draw shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
    # Draw main text
    draw.text((x, y), text, font=font, fill=fill)


def generate_overlay_frames(
    verse_ref: str,
    verse_text: str,
    prayer_text: str,
    theme_slug: str,
    duration_sec: float,
    width: int = 1080,
    height: int = 1920,
    cta_override: str | None = None,
) -> list[dict[str, Any]]:
    """Generate overlay PNG frames for different sections of the video.

    Returns a list of dicts with:
        - file_path: path to the PNG
        - start_sec: when to show this overlay
        - end_sec: when to hide this overlay
    """
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

    # Fonts
    brand_font = _get_font(52, bold=True)
    verse_ref_font = _get_font(52, bold=True)
    verse_text_font = _get_font(42, bold=True)
    prayer_font = _get_font(38)
    cta_font = _get_font(32)

    # Colors
    accent = "#E8D5B7"  # Warm beige for branding

    # Layout constants
    margin = 60
    max_text_width = width - (margin * 2)

    # Split prayer into chunks (roughly 3-4 sections based on duration)
    prayer_words = prayer_text.split()
    num_chunks = 4
    words_per_chunk = len(prayer_words) // num_chunks

    prayer_chunks = []
    for i in range(num_chunks):
        start_idx = i * words_per_chunk
        if i == num_chunks - 1:
            # Last chunk gets remaining words
            chunk = ' '.join(prayer_words[start_idx:])
        else:
            chunk = ' '.join(prayer_words[start_idx:start_idx + words_per_chunk])
        prayer_chunks.append(chunk)

    # Calculate timing for each chunk
    verse_duration = 6  # First 6 seconds for verse
    prayer_duration = duration_sec - verse_duration - 4  # Leave 4 sec for CTA
    chunk_duration = prayer_duration / num_chunks

    frames = []
    cta_text = cta_override or THEME_CTAS.get(theme_slug, "Share your prayer in the comments")

    # Safe zone boundary: nothing below this y value
    safe_zone_y = height - TIKTOK_BOTTOM_SAFE_ZONE

    # Generate frame for each prayer chunk
    for i, chunk in enumerate(prayer_chunks):
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        y_cursor = margin + 40

        # Brand: "2nd half faith" (always visible)
        brand_text = "2nd half faith"
        brand_bbox = brand_font.getbbox(brand_text)
        brand_width = brand_bbox[2] - brand_bbox[0]
        brand_x = (width - brand_width) // 2
        _draw_text_with_shadow(draw, (brand_x, y_cursor), brand_text, brand_font, fill=accent)
        y_cursor += 80

        # Verse reference
        verse_ref_bbox = verse_ref_font.getbbox(verse_ref)
        verse_ref_width = verse_ref_bbox[2] - verse_ref_bbox[0]
        verse_ref_x = (width - verse_ref_width) // 2
        _draw_text_with_shadow(draw, (verse_ref_x, y_cursor), verse_ref, verse_ref_font)
        y_cursor += 60

        # Verse text (wrapped)
        verse_lines = _wrap_text(verse_text, verse_text_font, max_text_width)
        for line in verse_lines:
            line_bbox = verse_text_font.getbbox(line)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (width - line_width) // 2
            _draw_text_with_shadow(draw, (line_x, y_cursor), line, verse_text_font)
            y_cursor += 50

        # Space before prayer
        y_cursor += 60

        # Prayer text box background (semi-transparent)
        prayer_lines = _wrap_text(chunk, prayer_font, max_text_width - 40)
        prayer_height = len(prayer_lines) * 55 + 40
        prayer_box_top = y_cursor
        prayer_box_bottom = y_cursor + prayer_height

        # Clamp prayer box so it doesn't extend into the safe zone
        max_prayer_bottom = safe_zone_y - 80  # leave gap for CTA
        if prayer_box_bottom > max_prayer_bottom:
            shift = prayer_box_bottom - max_prayer_bottom
            prayer_box_top -= shift
            prayer_box_bottom -= shift
            y_cursor = prayer_box_top

        # Draw rounded rectangle background for prayer
        draw.rounded_rectangle(
            [margin - 20, prayer_box_top, width - margin + 20, prayer_box_bottom],
            radius=20,
            fill=(0, 0, 0, 160)  # Semi-transparent black
        )

        y_cursor += 20
        for line in prayer_lines:
            _draw_text_with_shadow(draw, (margin, y_cursor), line, prayer_font, shadow_offset=2)
            y_cursor += 55

        # CTA at bottom — above the TikTok UI safe zone
        cta_y = safe_zone_y
        cta_lines = _wrap_text(cta_text, cta_font, max_text_width)
        # Position CTA so its last line ends at safe_zone_y
        cta_total_height = len(cta_lines) * 45
        cta_y = safe_zone_y - cta_total_height
        for line in cta_lines:
            line_bbox = cta_font.getbbox(line)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (width - line_width) // 2
            _draw_text_with_shadow(draw, (line_x, cta_y), line, cta_font, fill=accent)
            cta_y += 45

        # Save frame
        frame_path = OVERLAY_DIR / f"overlay_{i}.png"
        img.save(frame_path, "PNG")

        # Calculate timing
        if i == 0:
            start_sec = 0
        else:
            start_sec = verse_duration + (i * chunk_duration)

        end_sec = verse_duration + ((i + 1) * chunk_duration)
        if i == num_chunks - 1:
            end_sec = duration_sec

        frames.append({
            "file_path": str(frame_path),
            "start_sec": start_sec,
            "end_sec": end_sec,
            "chunk_index": i,
        })

    return frames


def generate_single_overlay(
    verse_ref: str,
    verse_text: str,
    prayer_text: str,
    theme_slug: str,
    chunk_index: int,
    width: int = 1080,
    height: int = 1920,
    cta_override: str | None = None,
) -> str:
    """Generate a single overlay image for a specific prayer chunk.

    Returns the file path to the PNG.
    """
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

    # Fonts
    brand_font = _get_font(52, bold=True)
    verse_ref_font = _get_font(52, bold=True)
    verse_text_font = _get_font(42, bold=True)
    prayer_font = _get_font(38)
    cta_font = _get_font(32)

    # Colors
    accent = "#E8D5B7"  # Warm beige for branding

    # Layout constants
    margin = 60
    max_text_width = width - (margin * 2)

    # Split prayer into chunks
    prayer_words = prayer_text.split()
    num_chunks = 4
    words_per_chunk = len(prayer_words) // num_chunks

    start_idx = chunk_index * words_per_chunk
    if chunk_index == num_chunks - 1:
        chunk = ' '.join(prayer_words[start_idx:])
    else:
        chunk = ' '.join(prayer_words[start_idx:start_idx + words_per_chunk])

    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    y_cursor = margin + 40

    # Brand: "2nd half faith"
    brand_text = "2nd half faith"
    brand_bbox = brand_font.getbbox(brand_text)
    brand_width = brand_bbox[2] - brand_bbox[0]
    brand_x = (width - brand_width) // 2
    _draw_text_with_shadow(draw, (brand_x, y_cursor), brand_text, brand_font, fill=accent)
    y_cursor += 80

    # Verse reference
    verse_ref_bbox = verse_ref_font.getbbox(verse_ref)
    verse_ref_width = verse_ref_bbox[2] - verse_ref_bbox[0]
    verse_ref_x = (width - verse_ref_width) // 2
    _draw_text_with_shadow(draw, (verse_ref_x, y_cursor), verse_ref, verse_ref_font)
    y_cursor += 60

    # Verse text (wrapped)
    verse_lines = _wrap_text(verse_text, verse_text_font, max_text_width)
    for line in verse_lines:
        line_bbox = verse_text_font.getbbox(line)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (width - line_width) // 2
        _draw_text_with_shadow(draw, (line_x, y_cursor), line, verse_text_font)
        y_cursor += 50

    # Space before prayer
    y_cursor += 60

    # Safe zone boundary: nothing below this y value
    safe_zone_y = height - TIKTOK_BOTTOM_SAFE_ZONE

    # Prayer text box background
    prayer_lines = _wrap_text(chunk, prayer_font, max_text_width - 40)
    prayer_height = len(prayer_lines) * 55 + 40
    prayer_box_top = y_cursor
    prayer_box_bottom = y_cursor + prayer_height

    # Clamp prayer box so it doesn't extend into the safe zone
    max_prayer_bottom = safe_zone_y - 80
    if prayer_box_bottom > max_prayer_bottom:
        shift = prayer_box_bottom - max_prayer_bottom
        prayer_box_top -= shift
        prayer_box_bottom -= shift
        y_cursor = prayer_box_top

    draw.rounded_rectangle(
        [margin - 20, prayer_box_top, width - margin + 20, prayer_box_bottom],
        radius=20,
        fill=(0, 0, 0, 160)
    )

    y_cursor += 20
    for line in prayer_lines:
        _draw_text_with_shadow(draw, (margin, y_cursor), line, prayer_font, shadow_offset=2)
        y_cursor += 55

    # CTA at bottom — above the TikTok UI safe zone
    cta_text = cta_override or THEME_CTAS.get(theme_slug, "Share your prayer in the comments")
    cta_lines = _wrap_text(cta_text, cta_font, max_text_width)
    cta_total_height = len(cta_lines) * 45
    cta_y = safe_zone_y - cta_total_height
    for line in cta_lines:
        line_bbox = cta_font.getbbox(line)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (width - line_width) // 2
        _draw_text_with_shadow(draw, (line_x, cta_y), line, cta_font, fill=accent)
        cta_y += 45

    frame_path = OVERLAY_DIR / f"overlay_{chunk_index}.png"
    img.save(frame_path, "PNG")

    return str(frame_path)
