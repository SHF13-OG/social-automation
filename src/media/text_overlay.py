"""Generate text overlay images using Pillow for video compositing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

OVERLAY_DIR = Path("media/overlays")

# TikTok's UI covers the top ~10% (username, follow button, sound icon)
# and the bottom ~20% (caption, buttons). Keep all content between these zones.
TIKTOK_TOP_SAFE_ZONE = 192     # 10% of 1920
TIKTOK_BOTTOM_SAFE_ZONE = 384  # 20% of 1920

# Theme-based calls to action
THEME_CTAS = {
    "wedding-joy": "Tag someone getting married soon",
    "money-worry": "Drop a prayer request about your finances",
    "closer-to-jesus": "Share what draws you closer to Him",
    "empty-nest": "Tell us how you're filling the quiet",
    "health-scare": "Drop a prayer request if you need healing",
    "losing-loved-one": "Share who you're remembering today",
    "marriage-distance": "Tag your spouse and share this blessing",
    "caring-for-parents": "Share your caregiving story below",
    "child-struggles": "Share a prayer for your children below",
    "retirement-purpose": "What's your new purpose? Tell us below",
    "past-regrets": "Share what God has set you free from",
    "loneliness": "Tell someone you're thinking of them today",
    "grandparent-joy": "Tell us about your grandchildren",
    "purity-struggle": "Share what helps you stay accountable",
    "faith-dry-season": "What question is on your heart today?",
    "new-season-fear": "What new season is God leading you into?",
}


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a font, falling back to default if Georgia not available."""
    if bold:
        font_names = [
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        ]
    else:
        font_names = [
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
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
    hook_text: str = "",
) -> list[dict[str, Any]]:
    """Generate overlay PNG frames for different sections of the video.

    Returns a list of dicts with:
        - file_path: path to the PNG
        - start_sec: when to show this overlay
        - end_sec: when to hide this overlay
    """
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

    # Fonts
    accent_font = _get_font(64, bold=True)
    verse_font = _get_font(56, bold=True)
    prayer_font = _get_font(48, bold=True)

    # Colors
    accent = "#E8D5B7"  # Warm beige for hook & CTA
    verse_color = "#FFFFFF"  # Bright white for verse
    prayer_color = "#FFD700"  # Bold yellow for spoken words

    # Layout constants
    margin = 60
    max_text_width = width - (margin * 2)

    # Split prayer into 3-word chunks
    words = prayer_text.split()
    prayer_chunks = [" ".join(words[i:i + 3]) for i in range(0, len(words), 3)]
    num_chunks = len(prayer_chunks)

    # Calculate timing proportional to word count across the full duration
    word_counts = [len(chunk.split()) for chunk in prayer_chunks]
    total_words = sum(word_counts) or 1

    frames = []
    cta_text = cta_override or THEME_CTAS.get(theme_slug, "Share your prayer in the comments")

    # Fixed layout positions
    hook_y = height // 4
    verse_y = (height // 4 + height // 2) // 2  # midpoint between hook and prayer
    prayer_y = height // 2
    cta_y = 7 * height // 10

    # Generate frame for each prayer chunk
    cumulative_sec = 0.0
    for i, chunk_text in enumerate(prayer_chunks):
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # --- Hook question centered at height // 3 ---
        if hook_text:
            y_cursor = hook_y
            hook_lines = _wrap_text(hook_text, accent_font, max_text_width)
            for line in hook_lines:
                line_bbox = accent_font.getbbox(line)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (width - line_width) // 2
                _draw_text_with_shadow(draw, (line_x, y_cursor), line, accent_font, fill=accent)
                y_cursor += 78

        # --- Verse reference (no box) centered between hook and prayer ---
        if verse_ref:
            ref_bbox = verse_font.getbbox(verse_ref)
            ref_w = ref_bbox[2] - ref_bbox[0]
            ref_x = (width - ref_w) // 2
            _draw_text_with_shadow(draw, (ref_x, verse_y), verse_ref, verse_font, fill=verse_color)

        # --- Prayer text — 3 words centered ---
        chunk_bbox = prayer_font.getbbox(chunk_text)
        chunk_w = chunk_bbox[2] - chunk_bbox[0]
        chunk_x = (width - chunk_w) // 2
        _draw_text_with_shadow(
            draw, (chunk_x, prayer_y), chunk_text, prayer_font,
            fill=prayer_color, shadow_offset=3,
        )

        # --- CTA — fixed position above bottom safe zone ---
        cur_cta_y = cta_y
        cta_lines = _wrap_text(cta_text, accent_font, max_text_width)
        for line in cta_lines:
            line_bbox = accent_font.getbbox(line)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (width - line_width) // 2
            _draw_text_with_shadow(draw, (line_x, cur_cta_y), line, accent_font, fill=accent)
            cur_cta_y += 78

        # Save frame
        frame_path = OVERLAY_DIR / f"overlay_{i}.png"
        img.save(frame_path, "PNG")

        # Timing proportional to word count across the full audio duration
        start_sec = cumulative_sec
        chunk_sec = duration_sec * (word_counts[i] / total_words)
        cumulative_sec += chunk_sec
        end_sec = cumulative_sec
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
    hook_text: str = "",
) -> str:
    """Generate a single overlay image for a specific prayer chunk.

    Returns the file path to the PNG.
    """
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

    # Fonts
    accent_font = _get_font(64, bold=True)
    verse_font = _get_font(56, bold=True)
    prayer_font = _get_font(48, bold=True)

    # Colors
    accent = "#E8D5B7"  # Warm beige for hook & CTA
    verse_color = "#FFFFFF"  # Bright white for verse
    prayer_color = "#FFD700"  # Bold yellow for spoken words

    # Layout constants
    margin = 60
    max_text_width = width - (margin * 2)

    # Split prayer into 3-word chunks and pick the requested one
    words = prayer_text.split()
    all_chunks = [" ".join(words[i:i + 3]) for i in range(0, len(words), 3)]
    chunk_text = all_chunks[chunk_index] if chunk_index < len(all_chunks) else ""

    # Fixed layout positions
    hook_y = height // 4
    verse_y = (height // 4 + height // 2) // 2  # midpoint between hook and prayer
    prayer_y = height // 2
    cta_y_pos = 7 * height // 10

    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # --- Hook question centered at height // 3 ---
    if hook_text:
        y_cursor = hook_y
        hook_lines = _wrap_text(hook_text, accent_font, max_text_width)
        for line in hook_lines:
            line_bbox = accent_font.getbbox(line)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (width - line_width) // 2
            _draw_text_with_shadow(draw, (line_x, y_cursor), line, accent_font, fill=accent)
            y_cursor += 78

    # --- Verse reference (no box) centered between hook and prayer ---
    if verse_ref:
        ref_bbox = verse_font.getbbox(verse_ref)
        ref_w = ref_bbox[2] - ref_bbox[0]
        ref_x = (width - ref_w) // 2
        _draw_text_with_shadow(draw, (ref_x, verse_y), verse_ref, verse_font, fill=verse_color)

    # --- Prayer text — 3 words centered ---
    if chunk_text:
        chunk_bbox = prayer_font.getbbox(chunk_text)
        chunk_w = chunk_bbox[2] - chunk_bbox[0]
        chunk_x = (width - chunk_w) // 2
        _draw_text_with_shadow(
            draw, (chunk_x, prayer_y), chunk_text, prayer_font,
            fill=prayer_color, shadow_offset=3,
        )

    # --- CTA — fixed position above bottom safe zone ---
    cta_text = cta_override or THEME_CTAS.get(theme_slug, "Share your prayer in the comments")
    cur_cta_y = cta_y_pos
    cta_lines = _wrap_text(cta_text, accent_font, max_text_width)
    for line in cta_lines:
        line_bbox = accent_font.getbbox(line)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (width - line_width) // 2
        _draw_text_with_shadow(draw, (line_x, cur_cta_y), line, accent_font, fill=accent)
        cur_cta_y += 78

    frame_path = OVERLAY_DIR / f"overlay_{chunk_index}.png"
    img.save(frame_path, "PNG")

    return str(frame_path)
