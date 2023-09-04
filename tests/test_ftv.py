"""Unit tests for ftv.py"""

# Standard library imports
from logging import Logger
import logging
import os
# from unittest import TestCase, mock
import unittest
from unittest.mock import patch

# local imports
from context import ftv

TEST_FTV_SECRET_CONFIG_FILE = 'tests/test_ftv_secret_config.toml'

class TestFTV(unittest.TestCase):
    def setUp(self):
        self._ftv = ftv.FTV(logger=logging.Logger(__name__), ftv_data_file=TEST_FTV_SECRET_CONFIG_FILE)

    # -------------------------------------------------------------------------
    # Tests for get_environment_variable_value_
    # -------------------------------------------------------------------------
    @patch.dict(os.environ, {'ABK_TEST_ENV_VAR': '[fake_api_key]'})
    def test_get_environment_variable_value_returns_valid_value(self) -> None:
        """
            get_environment_variable_value returns a value from the set environment variable
        """
        actual_value = self._ftv._get_environment_variable_value('ABK_TEST_ENV_VAR')
        self.assertEqual(actual_value, '[fake_api_key]')


    @patch.dict(os.environ, {'ABK_TEST_ENV_VAR': ''})
    def test_get_environment_variable_value_should_return_empty_given_env_var_value_is_empty(self) -> None:
        """
            get_environment_variable_value returns empty string
            given environment variable is set to empty string
        """
        actual_value = self._ftv._get_environment_variable_value('ABK_TEST_ENV_VAR')
        self.assertEqual(actual_value, '')


    def test_get_environment_variable_value_should_return_empty_given_env_var_undefined(self) -> None:
        """
            get_environment_variable_value returns empty string
            given environment variable is not set
        """
        actual_value = self._ftv._get_environment_variable_value('ABK_TEST_ENV_VAR')
        self.assertEqual(actual_value, '')


if __name__ == '__main__':
    unittest.main()
