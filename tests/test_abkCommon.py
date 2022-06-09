"""Unit tests for abkCommon.py"""

# Standard library imports
import os
import sys
import unittest
from unittest.mock import mock_open, patch, call

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Third party imports
from optparse import OptionParser, Values
from abkPackage.abkCommon import CommandLineOptions


class TestAbkCommon(unittest.TestCase):
    mut = None
    yaml_file = """version: 1
disable_existing_loggers: True
formatters:
    abkFormatterShort:
        format: '[%(asctime)s]:[%(funcName)s]:[%(levelname)s]: %(message)s'
        datefmt: '%Y%m%d %H:%M:%S'
handlers:
    consoleHandler:
        class: logging.StreamHandler
        level: DEBUG
        formatter: abkFormatterShort
        stream: ext://sys.stdout
loggers:
    consoleLogger:
        level: DEBUG
        handlers: [consoleHandler]
        qualname: consoleLogger
        propagate: no
"""


    def setUp(self) -> None:
        self.maxDiff = None
        values = Values()
        values.verbose = False
        values.log_into_file = False
        self.clo = CommandLineOptions(options=values)
        return super().setUp()


    def test_CommandLineOptions__setup_logger_throws_given_yaml_config_file_does_not_exist(self) -> None:
        with self.assertRaises(IOError) as context:
            self.clo.options.config_log_file = 'NotValidFile.yaml'
            self.clo._setup_logging()
        self.assertEqual('NotValidFile.yaml does not exist.', str(context.exception))


if __name__ == '__main__':
    unittest.main()
