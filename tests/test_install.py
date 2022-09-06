"""Unit tests for install.py"""

# Standard library imports
import os
import sys
import unittest
from unittest.mock import mock_open, patch, call

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../abk_bwp')))

# Third party imports
# from install import BingWallPaper


class TestAbkCommon(unittest.TestCase):
    mut = None

    def setUp(self) -> None:
        self.maxDiff = None
        return super().setUp()


    def test_install_001(self) -> None:
        self.assertTrue(True)



if __name__ == '__main__':
    unittest.main()
