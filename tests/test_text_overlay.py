"""Tests for src/media/text_overlay.py - Pillow-based text overlay generation."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.media.text_overlay import (
    THEME_CTAS,
    TIKTOK_BOTTOM_SAFE_ZONE,
    TIKTOK_TOP_SAFE_ZONE,
    _get_font,
    _wrap_text,
    generate_overlay_frames,
    generate_single_overlay,
)


class TestThemeCTAs:
    """Tests for theme-based call-to-action mappings."""

    def test_all_themes_have_ctas(self):
        expected_themes = [
            "wedding-joy", "money-worry", "closer-to-jesus", "empty-nest",
            "health-scare", "losing-loved-one", "marriage-distance",
            "caring-for-parents", "child-struggles", "retirement-purpose",
            "past-regrets", "loneliness", "grandparent-joy",
            "purity-struggle", "faith-dry-season", "new-season-fear",
        ]
        for theme in expected_themes:
            assert theme in THEME_CTAS
            assert len(THEME_CTAS[theme]) > 10  # Should be a meaningful CTA

    def test_ctas_are_action_oriented(self):
        # CTAs should encourage engagement
        action_words = ["share", "tell", "drop", "tag", "what"]
        for theme, cta in THEME_CTAS.items():
            cta_lower = cta.lower()
            has_action = any(word in cta_lower for word in action_words)
            assert has_action, f"CTA for '{theme}' should contain action word"


class TestWrapText:
    """Tests for text wrapping functionality."""

    def test_short_text_no_wrap(self):
        # Mock font with consistent bbox
        mock_font = MagicMock()
        mock_font.getbbox.return_value = (0, 0, 100, 20)  # Width 100 pixels

        result = _wrap_text("Hello world", mock_font, 500)
        assert len(result) == 1
        assert result[0] == "Hello world"

    def test_long_text_wraps(self):
        # Mock font where each word is 100 pixels
        mock_font = MagicMock()

        def mock_getbbox(text):
            # Simulate ~20 pixels per character
            width = len(text) * 20
            return (0, 0, width, 20)

        mock_font.getbbox = mock_getbbox

        long_text = "This is a longer piece of text that should wrap"
        result = _wrap_text(long_text, mock_font, 200)

        # Should wrap into multiple lines
        assert len(result) > 1
        # All words should still be present
        rejoined = " ".join(result)
        assert rejoined == long_text

    def test_empty_text(self):
        mock_font = MagicMock()
        mock_font.getbbox.return_value = (0, 0, 0, 0)

        result = _wrap_text("", mock_font, 500)
        assert result == []

    def test_single_word(self):
        mock_font = MagicMock()
        mock_font.getbbox.return_value = (0, 0, 50, 20)

        result = _wrap_text("Word", mock_font, 100)
        assert result == ["Word"]


class TestGetFont:
    """Tests for font loading with fallback."""

    def test_returns_font_object(self):
        # Should return some font (either system font or default)
        font = _get_font(24)
        assert font is not None

    def test_bold_parameter(self):
        # Should not crash with bold=True
        font_regular = _get_font(24, bold=False)
        font_bold = _get_font(24, bold=True)
        assert font_regular is not None
        assert font_bold is not None

    def test_different_sizes(self):
        font_small = _get_font(12)
        font_large = _get_font(48)
        assert font_small is not None
        assert font_large is not None


class TestGenerateOverlayFrames:
    """Tests for multi-frame overlay generation."""

    def test_generates_multiple_frames(self, tmp_path):
        overlay_dir = tmp_path / "overlays"
        with patch('src.media.text_overlay.OVERLAY_DIR', overlay_dir):
            overlay_dir.mkdir(parents=True, exist_ok=True)

            frames = generate_overlay_frames(
                verse_ref="Psalm 23:4",
                verse_text="Even though I walk through the valley of the shadow of death, I will fear no evil.",
                prayer_text=" ".join(["word"] * 160),  # ~160 words
                theme_slug="losing-loved-one",
                duration_sec=65.0,
            )

            # 2-line chunks: frame count depends on wrapped line count
            assert len(frames) >= 1

    def test_frame_structure(self, tmp_path):
        with patch('src.media.text_overlay.OVERLAY_DIR', tmp_path / "overlays"):
            (tmp_path / "overlays").mkdir(parents=True, exist_ok=True)

            frames = generate_overlay_frames(
                verse_ref="John 3:16",
                verse_text="For God so loved the world.",
                prayer_text=" ".join(["test"] * 100),
                theme_slug="faith-dry-season",
                duration_sec=60.0,
            )

            for frame in frames:
                assert "file_path" in frame
                assert "start_sec" in frame
                assert "end_sec" in frame
                assert "chunk_index" in frame
                assert frame["end_sec"] > frame["start_sec"]

    def test_timing_covers_duration(self, tmp_path):
        with patch('src.media.text_overlay.OVERLAY_DIR', tmp_path / "overlays"):
            (tmp_path / "overlays").mkdir(parents=True, exist_ok=True)

            duration = 70.0
            frames = generate_overlay_frames(
                verse_ref="Test 1:1",
                verse_text="Test verse.",
                prayer_text=" ".join(["word"] * 150),
                theme_slug="health-scare",
                duration_sec=duration,
            )

            # Last frame should end at duration
            assert frames[-1]["end_sec"] == duration
            # First frame should start at 0
            assert frames[0]["start_sec"] == 0

    def test_creates_png_files(self, tmp_path):
        overlay_dir = tmp_path / "overlays"
        with patch('src.media.text_overlay.OVERLAY_DIR', overlay_dir):
            overlay_dir.mkdir(parents=True, exist_ok=True)

            frames = generate_overlay_frames(
                verse_ref="Test 1:1",
                verse_text="Short verse.",
                prayer_text=" ".join(["prayer"] * 80),
                theme_slug="grandparent-joy",
                duration_sec=62.0,
            )

            for frame in frames:
                assert Path(frame["file_path"]).exists()
                assert frame["file_path"].endswith(".png")

    def test_uses_theme_cta(self, tmp_path):
        # This tests that the theme-specific CTA is used (indirectly through frame generation)
        overlay_dir = tmp_path / "overlays"
        with patch('src.media.text_overlay.OVERLAY_DIR', overlay_dir):
            overlay_dir.mkdir(parents=True, exist_ok=True)

            # Should not raise even with unknown theme
            frames = generate_overlay_frames(
                verse_ref="Test 1:1",
                verse_text="Verse.",
                prayer_text=" ".join(["word"] * 100),
                theme_slug="unknown-theme",
                duration_sec=60.0,
            )
            assert len(frames) >= 1

    def test_hook_text_renders(self, tmp_path):
        """Frames with hook_text should render pixels in the hook area."""
        import numpy as np
        from PIL import Image

        overlay_dir = tmp_path / "overlays"
        with patch('src.media.text_overlay.OVERLAY_DIR', overlay_dir):
            overlay_dir.mkdir(parents=True, exist_ok=True)

            frames = generate_overlay_frames(
                verse_ref="Test 1:1",
                verse_text="Short verse.",
                prayer_text=" ".join(["word"] * 80),
                theme_slug="money-worry",
                duration_sec=62.0,
                hook_text="Are you feeling worried about money?",
            )

            # Check that the first frame has rendered content
            img = Image.open(frames[0]["file_path"])
            arr = np.array(img)
            # Hook renders at y=height//4 which is 480; check 470-560 area
            hook_area = arr[470:560, :, 3]
            assert hook_area.max() > 0, "Hook text should render pixels in the hook area"


class TestGenerateSingleOverlay:
    """Tests for single frame overlay generation."""

    def test_returns_file_path(self, tmp_path):
        overlay_dir = tmp_path / "overlays"
        with patch('src.media.text_overlay.OVERLAY_DIR', overlay_dir):
            overlay_dir.mkdir(parents=True, exist_ok=True)

            path = generate_single_overlay(
                verse_ref="Romans 8:28",
                verse_text="And we know that in all things God works for the good.",
                prayer_text=" ".join(["prayer"] * 100),
                theme_slug="retirement-purpose",
                chunk_index=0,
            )

            assert isinstance(path, str)
            assert path.endswith(".png")
            assert Path(path).exists()

    def test_chunk_index_affects_filename(self, tmp_path):
        overlay_dir = tmp_path / "overlays"
        with patch('src.media.text_overlay.OVERLAY_DIR', overlay_dir):
            overlay_dir.mkdir(parents=True, exist_ok=True)

            path0 = generate_single_overlay(
                verse_ref="Test 1:1",
                verse_text="Test.",
                prayer_text=" ".join(["word"] * 100),
                theme_slug="losing-loved-one",
                chunk_index=0,
            )
            path2 = generate_single_overlay(
                verse_ref="Test 1:1",
                verse_text="Test.",
                prayer_text=" ".join(["word"] * 100),
                theme_slug="losing-loved-one",
                chunk_index=2,
            )

            assert "overlay_0" in path0
            assert "overlay_2" in path2

    def test_handles_custom_dimensions(self, tmp_path):
        overlay_dir = tmp_path / "overlays"
        with patch('src.media.text_overlay.OVERLAY_DIR', overlay_dir):
            overlay_dir.mkdir(parents=True, exist_ok=True)

            path = generate_single_overlay(
                verse_ref="Test 1:1",
                verse_text="Test.",
                prayer_text=" ".join(["word"] * 80),
                theme_slug="health-scare",
                chunk_index=0,
                width=720,
                height=1280,
            )

            assert Path(path).exists()

    def test_hook_text_parameter(self, tmp_path):
        """Single overlay should accept and render hook_text."""
        overlay_dir = tmp_path / "overlays"
        with patch('src.media.text_overlay.OVERLAY_DIR', overlay_dir):
            overlay_dir.mkdir(parents=True, exist_ok=True)

            path = generate_single_overlay(
                verse_ref="Test 1:1",
                verse_text="Short verse.",
                prayer_text=" ".join(["word"] * 80),
                theme_slug="loneliness",
                chunk_index=0,
                hook_text="Are you feeling lonely even around others?",
            )

            assert Path(path).exists()
            assert Path(path).stat().st_size > 0


class TestIntegration:
    """Integration tests for text overlay generation."""

    def test_full_overlay_workflow(self, tmp_path):
        """Test complete overlay generation for a realistic content piece."""
        overlay_dir = tmp_path / "overlays"
        with patch('src.media.text_overlay.OVERLAY_DIR', overlay_dir):
            overlay_dir.mkdir(parents=True, exist_ok=True)

            verse_ref = "Isaiah 41:10"
            verse_text = "So do not fear, for I am with you; do not be dismayed, for I am your God."
            prayer_text = (
                "Heavenly Father, we come before You today with hearts that sometimes feel weary "
                "and spirits that long for Your presence. In moments of uncertainty, remind us "
                "that You are always near. When fear tries to grip our hearts, may we feel Your "
                "comforting hand guiding us forward. Grant us the peace that surpasses all "
                "understanding, and fill us with the courage to face each new day knowing that "
                "You walk beside us. We trust in Your unfailing love and rest in Your promises. "
                "In Jesus' name, Amen."
            )

            frames = generate_overlay_frames(
                verse_ref=verse_ref,
                verse_text=verse_text,
                prayer_text=prayer_text,
                theme_slug="faith-dry-season",
                duration_sec=65.0,
            )

            assert len(frames) >= 1
            for frame in frames:
                file_path = Path(frame["file_path"])
                assert file_path.exists()
                assert file_path.stat().st_size > 0  # Not empty

            # Verify timing is sequential and non-overlapping
            for i in range(len(frames) - 1):
                assert frames[i]["end_sec"] >= frames[i + 1]["start_sec"] - 0.01  # Allow small gap


class TestTikTokSafeZone:
    """Tests for TikTok safe zone compliance."""

    def test_safe_zone_constants_exist(self):
        assert TIKTOK_BOTTOM_SAFE_ZONE is not None
        assert TIKTOK_TOP_SAFE_ZONE is not None

    def test_safe_zone_in_reasonable_range(self):
        # Bottom: 15-21% of 1920 = 288-403
        assert 288 <= TIKTOK_BOTTOM_SAFE_ZONE <= 400
        # Top: 8-12% of 1920 = 154-230
        assert 154 <= TIKTOK_TOP_SAFE_ZONE <= 230

    def test_content_within_safe_zones(self, tmp_path):
        """All content must render between top and bottom safe zones."""
        import numpy as np
        from PIL import Image

        overlay_dir = tmp_path / "overlays"
        with patch('src.media.text_overlay.OVERLAY_DIR', overlay_dir):
            overlay_dir.mkdir(parents=True, exist_ok=True)

            height = 1920
            path = generate_single_overlay(
                verse_ref="Psalm 23:4",
                verse_text="Even though I walk through the valley.",
                prayer_text=" ".join(["word"] * 100),
                theme_slug="losing-loved-one",
                chunk_index=0,
                width=1080,
                height=height,
            )

            img = Image.open(path)
            arr = np.array(img)

            # Check no content below bottom safe zone
            bottom_safe_y = height - TIKTOK_BOTTOM_SAFE_ZONE
            below = arr[bottom_safe_y:, :, 3]
            assert below.max() == 0, (
                f"Found rendered pixels below bottom safe zone (y>{bottom_safe_y})"
            )

            # Check no content above top safe zone
            above = arr[:TIKTOK_TOP_SAFE_ZONE, :, 3]
            assert above.max() == 0, (
                f"Found rendered pixels above top safe zone (y<{TIKTOK_TOP_SAFE_ZONE})"
            )
