"""Test for constants.py."""

import io
import unittest
from unittest import mock
from pathlib import Path
from importlib.metadata import PackageNotFoundError

import abk_bwp.constants as constants


class TestConstants(unittest.TestCase):
    """Test Constants class."""

    # -------------------------------------------------------------------------
    # _Const.__init__
    # -------------------------------------------------------------------------
    @mock.patch("abk_bwp.constants.get_version", side_effect=PackageNotFoundError)
    @mock.patch.object(constants._Const, "_load_from_pyproject")
    def test_package_not_found_uses_fallbacks(self, mock_load, mock_version):
        """Test test_package_not_found_uses_fallbacks."""
        const = constants._Const()
        self.assertEqual(const.VERSION, "0.0.0-dev")
        self.assertEqual(const.NAME, "unknown")
        mock_load.assert_called_once()
        mock_version.assert_called_once()

    @mock.patch.object(constants._Const, "_load_from_pyproject")
    def test_properties_have_expected_defaults(self, mock_load):
        """Test test_properties_have_expected_defaults."""
        const = constants._Const()

        # Manually set internal attributes (allowed only during initialization)
        object.__setattr__(const, "_version", "1.2.3")
        object.__setattr__(const, "_name", "abk_bwp")
        object.__setattr__(const, "_license", {"text": "MIT"})
        object.__setattr__(const, "_keywords", ["wallpaper", "bing"])
        object.__setattr__(const, "_authors", [{"name": "ABK", "email": "test@example.com"}])
        object.__setattr__(const, "_maintainers", [{"name": "ABK", "email": "maint@example.com"}])
        self.assertEqual(const.VERSION, "1.2.3")
        self.assertEqual(const.NAME, "abk_bwp")
        self.assertEqual(const.LICENSE, "MIT")
        self.assertEqual(const.KEYWORDS, ["wallpaper", "bing"])
        self.assertEqual(const.AUTHORS, [{"name": "ABK", "email": "test@example.com"}])
        self.assertEqual(const.MAINTAINERS, [{"name": "ABK", "email": "maint@example.com"}])

    def test_setattr_blocks_overwrites(self):
        """Test test_setattr_blocks_overwrites."""
        const = constants._Const()
        with self.assertRaises(AttributeError):
            const._version = "999.999.999"

    @mock.patch("abk_bwp.constants.get_version", return_value="9.9.9")
    @mock.patch("tomllib.load")
    @mock.patch("pathlib.Path.open")
    @mock.patch("abk_bwp.constants._Const._find_project_root")
    def test_load_from_pyproject_success(self, mock_find_root, mock_open, mock_load, mock_version):
        """Test test_load_from_pyproject_success."""
        fake_project_data = {
            "project": {
                "version": "9.9.9",
                "name": "custom_name",
                "license": {"text": "GPL"},
                "keywords": ["custom", "keywords"],
                "authors": [{"name": "Jane"}],
                "maintainers": [{"name": "John"}],
            }
        }
        # Setup mocks
        mock_find_root.return_value = Path("/fake/project")
        mock_load.return_value = fake_project_data
        # Simulate file-like object with TOML content (though unused due to mock_load)
        toml_content = "[project]\nversion = '9.9.9'\nname = 'custom_name'"
        mock_open.return_value.__enter__.return_value = io.StringIO(toml_content)

        const = constants._Const()

        self.assertEqual(const.VERSION, "9.9.9")
        self.assertEqual(const.NAME, "custom_name")
        self.assertEqual(const.LICENSE, "GPL")
        self.assertEqual(const.KEYWORDS, ["custom", "keywords"])
        self.assertEqual(const.AUTHORS, [{"name": "Jane"}])
        self.assertEqual(const.MAINTAINERS, [{"name": "John"}])
        mock_version.assert_called_once()

    @mock.patch("builtins.print")
    @mock.patch("pathlib.Path.exists", return_value=False)
    def test_find_project_root_raises(self, mock_exists, mock_print):
        """Test test_find_project_root_raises."""
        const = constants._Const()
        with self.assertRaises(FileNotFoundError):
            const._find_project_root(start=Path("/nonexistent"))
        mock_exists.assert_called()
        mock_print.assert_called_once_with("Warning: failed to load pyproject.toml metadata: pyproject.toml not found")


if __name__ == "__main__":
    unittest.main()
