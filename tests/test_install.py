"""Unit tests for install.py"""

# Standard library imports
import unittest
from unittest.mock import mock_open, patch, call

# Third party imports

# Local imports
from context import install



class TestAbkCommon(unittest.TestCase):
    mut = None

    def setUp(self) -> None:
        self.maxDiff = None
        return super().setUp()


    def test_install_001(self) -> None:
        self.assertTrue(True)



if __name__ == '__main__':
    unittest.main()
