"""Unit tests for uninstall.py"""

# Standard library imports
import os
import sys
import unittest
from unittest.mock import mock_open, patch, call

# Third party imports

# Local imports
from context import uninstall



class TestAbkCommon(unittest.TestCase):
    mut = None

    def setUp(self) -> None:
        self.maxDiff = None
        return super().setUp()


    def test_uninstall_001(self) -> None:
        self.assertTrue(True)



if __name__ == '__main__':
    unittest.main()
