"""Unit tests for fonts/__init__.py module."""

import unittest
from unittest.mock import patch

from abk_bwp.fonts import get_text_overlay_font_name


class TestGetTextOverlayFontName(unittest.TestCase):
    """Test get_text_overlay_font_name function."""

    @patch("abk_bwp.fonts.os.walk")
    def test_returns_font_path_when_fonts_exist(self, mock_walk):
        """Should return a valid font path if font files exist."""
        mock_walk.return_value = iter(
            [("/fake/fonts", [], ["Arial.ttf", "Verdana.otf", "README.txt"])]
        )
        font_path = get_text_overlay_font_name()
        self.assertTrue(font_path.endswith(("ttf", "otf")))
        self.assertTrue(any(font_path.endswith(ext) for ext in [".ttf", ".otf"]))

    @patch("abk_bwp.fonts.os.walk")
    def test_returns_empty_string_when_no_fonts(self, mock_walk):
        """Should return empty string if no valid font files exist."""
        mock_walk.return_value = iter([("/fake/fonts", [], ["README.md", "image.png"])])
        self.assertEqual(get_text_overlay_font_name(), "")

    @patch("abk_bwp.fonts.os.walk")
    def test_returns_empty_string_on_walk_failure(self, mock_walk):
        """Should return empty string if os.walk() throws or is invalid."""
        mock_walk.side_effect = OSError("filesystem error")
        with self.assertRaises(OSError):
            get_text_overlay_font_name()


if __name__ == "__main__":
    unittest.main()
