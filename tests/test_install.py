"""Unit tests for install.py."""

# Standard library imports
import unittest

# Third party imports

# Local imports
# from context import install


class TestInstall(unittest.TestCase):
    """TestInstall."""
    mut = None

    def setUp(self) -> None:
        """Set up tests for install."""
        self.maxDiff = None
        return super().setUp()


    def test_install_001(self) -> None:
        """test_install_001."""
        self.assertTrue(True)



if __name__ == '__main__':
    unittest.main()
