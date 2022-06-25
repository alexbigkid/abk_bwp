"""Unit tests for abkCommon.py"""

# Standard library imports
import getpass
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Third party imports
from optparse import OptionParser, Values
from abkPackage import abkCommon
from abkPackage.abkCommon import CommandLineOptions



@unittest.skipIf(sys.platform.startswith("win"), "should not run on Windows")
@mock.patch('os.environ')
class TestGetpassGetuser(unittest.TestCase):
    """Tests for GetUserName function"""

    def test_Getuser__username_takes_username_from_env(self, environ):
        expected_user_name = 'user_name_001'
        environ.get.return_value = expected_user_name
        actual_user_name = abkCommon.GetUserName()
        self.assertEqual(actual_user_name, expected_user_name, 'ERROR: unexpected user name')


    def test_Getuser__username_priorities_of_env_values(self, environ):
        environ.get.return_value = None
        abkCommon.GetUserName()
        self.assertEqual(
            [mock.call(x) for x in ('LOGNAME', 'USER', 'LNAME', 'USERNAME')],
            environ.get.call_args_list
        )


    def test_Getuser__username_falls_back_to_pwd(self, environ):
        expected_user_name = 'user_name_003'
        environ.get.return_value = None
        with mock.patch('os.getuid') as uid, mock.patch('pwd.getpwuid') as getpw:
            uid.return_value = 42
            getpw.return_value = [expected_user_name]
            self.assertEqual(abkCommon.GetUserName(), expected_user_name)
            getpw.assert_called_once_with(42)




class TestGetHomeDir(unittest.TestCase):
    """Tests for GetHomeDir function"""

    @mock.patch.dict(os.environ, {'HOME': 'users_home_dir_001'})
    def test_GetHomeDir__returns_users_homedir_from_env(self):
        exp_home_dir = 'users_home_dir_001'
        act_home_dir = abkCommon.GetHomeDir()
        self.assertEqual(exp_home_dir, act_home_dir, 'ERROR: unexpected home dir returned')


class TestCommandLineOptions(unittest.TestCase):
    """Tests for abkCommon CommandLineOptions class"""
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


    def test_CommandLineOptions__setup_logger_throws_given_invalid_yaml_file(self) -> None:
        with mock.patch("builtins.open", mock.mock_open(read_data='{"notValid": 2}')) as mock_file:
            with self.assertRaises(ValueError) as context:
                self.clo.options.config_log_file = 'valid.yaml'
                self.clo._setup_logging()
            self.assertEqual('valid.yaml is not a valid yaml format', str(context.exception))
            mock_file.assert_called_with('valid.yaml', 'r')
            self.assertEqual(self.clo.logger, None)




if __name__ == '__main__':
    unittest.main()
