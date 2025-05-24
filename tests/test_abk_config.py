"""Unit tests for abk_config.py."""

# Standard library imports
import unittest
from unittest import mock
from unittest.mock import MagicMock, mock_open, patch

# Third party imports
from parameterized import parameterized

# local  modules imports
from abk_bwp import config, abk_config


class TestAbkConfig(unittest.TestCase):
    """TestAbkConfig."""

    def setUp(self) -> None:
        """Set up."""
        self.maxDiff = None
        return super().setUp()

    @parameterized.expand(
        [
            # input         ftv confg       # result
            ["enable", False, True],
            ["disable", True, False],
        ]
    )
    def test__handle_ftv_option__calls_update_enable_field_in_toml_file(
        self, ftv_input: str | None, ftv_enabled: bool, exp_ftv_enabled: bool
    ) -> None:
        """test__handle_ftv_option__calls_update_enable_field_in_toml_file.

        Args:
            ftv_input (Union[str, None]): FTV input
            ftv_enabled (bool): FTV enabled
            exp_ftv_enabled (bool): expected FTV enabled
        """
        with (
            patch.dict(config.bwp_config, {"ftv": {"enabled": ftv_enabled}}),
            patch(
                "abk_bwp.abk_config.update_enable_field_in_toml_file"
            ) as mock_update_enable_field_in_toml_file,
        ):
            abk_config.handle_ftv_option(ftv_input)
        mock_update_enable_field_in_toml_file.assert_called_once_with(
            key_to_update=config.FTV_KW.FTV.value, update_to=exp_ftv_enabled
        )
        self.assertTrue(ftv_enabled != exp_ftv_enabled)

    @parameterized.expand(
        [
            # input         ftv config       result
            [None, True, True],
            [None, False, False],
            ["enable", True, True],
            ["disable", False, False],
            ["NotValid", True, True],
            ["NotValid", False, False],
            ["", True, True],
            ["", False, False],
        ]
    )
    def test__handle_ftv_option__does_not_calls_update_enable_field_in_toml_file(
        self, ftv_input: str | None, ftv_enabled: bool, exp_ftv_enabled: bool
    ) -> None:
        """test__handle_ftv_option__does_not_calls_update_enable_field_in_toml_file.

        Args:
            ftv_input (Union[str, None]): FTV input
            ftv_enabled (bool): FTV enabled
            exp_ftv_enabled (bool): expected FTV enabled
        """
        with (
            patch.dict(config.bwp_config, {"ftv": {"enabled": ftv_enabled}}),
            patch(
                "abk_bwp.abk_config.update_enable_field_in_toml_file"
            ) as mock_update_enable_field_in_toml_file,
        ):
            abk_config.handle_ftv_option(ftv_input)
        mock_update_enable_field_in_toml_file.assert_not_called()
        self.assertTrue(ftv_enabled == exp_ftv_enabled)

    @parameterized.expand(
        [
            # input         desktop_img confg   # result
            ["enable", False, True],
            ["disable", True, False],
        ]
    )
    def test__handle_desktop_auto_update_option__calls_update_enable_field_in_toml_file(
        self,
        desktop_img_input: str | None,
        desktop_img_enabled: bool,
        exp_desktop_img_enabled: bool,
    ) -> None:
        """test__handle_desktop_auto_update_option__calls_update_enable_field_in_toml_file.

        Args:
            desktop_img_input (Union[str, None]): desktop image input
            desktop_img_enabled (bool): desktop image enabled
            exp_desktop_img_enabled (bool): expected desktop image enabled
        """
        func_to_call = ("uninstall", "install")[exp_desktop_img_enabled]
        with (
            patch.dict(config.bwp_config, {"desktop_img": {"enabled": desktop_img_enabled}}),
            patch("abk_bwp.abk_config.update_enable_field_in_toml_file") as mock_update_enable,
            patch(f"abk_bwp.{func_to_call}.bwp_{func_to_call}") as mock_bwp_install_uninstall,
        ):
            abk_config.handle_desktop_auto_update_option(desktop_img_input)
        mock_update_enable.assert_called_once_with(
            key_to_update=config.DESKTOP_IMG_KW.DESKTOP_IMG.value,
            update_to=exp_desktop_img_enabled,
        )
        mock_bwp_install_uninstall.assert_called_once_with()
        self.assertTrue(desktop_img_enabled != exp_desktop_img_enabled)

    @parameterized.expand(
        [
            # input         ftv confg       # result
            [None, True, True],
            [None, False, False],
            ["enable", True, True],
            ["disable", False, False],
            ["NotValid", True, True],
            ["NotValid", False, False],
            ["", True, True],
            ["", False, False],
        ]
    )
    def test__handle_desktop_auto_update_option__does_not_calls_update_enable_field_in_toml_file(
        self,
        desktop_img_input: str | None,
        desktop_img_enabled: bool,
        exp_desktop_img_enabled: bool,
    ) -> None:
        """test__handle_desktop_auto_update_option__does_not_calls_update_enable_field_in_toml_file.

        Args:
            desktop_img_input (Union[str, None]): desktop image input
            desktop_img_enabled (bool): desktop image enabled
            exp_desktop_img_enabled (bool): expected desktop image enabled
        """
        with (
            patch.dict(config.bwp_config, {"desktop_img": {"enabled": desktop_img_enabled}}),
            patch("abk_bwp.abk_config.update_enable_field_in_toml_file") as mock_update_enable,
        ):
            abk_config.handle_desktop_auto_update_option(desktop_img_input)
        mock_update_enable.assert_not_called()
        self.assertTrue(desktop_img_enabled == exp_desktop_img_enabled)


class TestAbkBwp(unittest.TestCase):
    """TestAbkBwp."""

    def setUp(self):
        """Patch the resolve method used by lazy_logger."""
        # Mock CommandLineOptions object with needed attributes
        self.mock_clo = MagicMock()
        self.mock_clo.options.desktop_auto_update = True
        self.mock_clo.options.frame_tv = False
        self.mock_clo._args = []
        self.mock_clo.options = MagicMock(desktop_auto_update=True, frame_tv=False)

        patcher = mock.patch("abk_bwp.abk_config.logger._resolve", return_value=mock.MagicMock())
        self.mock_resolve = patcher.start()
        self.addCleanup(patcher.stop)

        # Import abk_config after patch
        import abk_bwp.abk_config as abk_config

        self.abk_config = abk_config

    @patch("abk_bwp.abk_config.sys.exit")
    @patch("abk_bwp.abk_config.handle_desktop_auto_update_option")
    @patch("abk_bwp.abk_config.handle_ftv_option")
    @patch("abk_bwp.abk_config.logger")
    def test_abk_bwp_success(self, mock_logger, mock_ftv, mock_desktop, mock_exit):
        """Test normal execution path."""
        self.abk_config.abk_bwp(self.mock_clo)

        mock_desktop.assert_called_once_with(True)
        mock_ftv.assert_called_once_with(False)
        mock_exit.assert_called_once_with(0)
        mock_logger.error.assert_not_called()

    @patch("abk_bwp.abk_config.sys.exit")
    @patch("abk_bwp.abk_config.handle_desktop_auto_update_option")
    @patch("abk_bwp.abk_config.handle_ftv_option")
    @patch("abk_bwp.abk_config.logger")
    def test_abk_bwp_exception(self, mock_logger, mock_ftv, mock_desktop, mock_exit):
        """Simulate exception in one of the handlers."""
        mock_desktop.side_effect = Exception("fail desktop")

        self.abk_config.abk_bwp(self.mock_clo)

        mock_desktop.assert_called_once()
        mock_ftv.assert_not_called()  # Because exception stops execution before this call
        mock_exit.assert_called_once_with(1)
        mock_logger.error.assert_called()
        mock_logger.exception.assert_called()

    @patch("abk_bwp.abk_config.tomlkit.load")
    @patch("abk_bwp.abk_config.tomlkit.dump")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="[desktop_img]\nenabled = false\n[ftv]\nenabled = false\n",
    )
    def test_update_enable_field(self, mock_file, mock_dump, mock_load):
        """Test update enable filed in toml file."""
        # Prepare fake config data returned by tomlkit.load
        config_data = {"desktop_img": {"enabled": False}, "ftv": {"enabled": False}}
        mock_load.return_value = config_data
        # Call the function to update desktop_img.enabled to True
        self.abk_config.update_enable_field_in_toml_file("desktop_img", True)

        # Check tomlkit.load was called once with the open file handle
        mock_load.assert_called_once()
        # Check the "enabled" field was updated in the config_data dict
        self.assertTrue(config_data["desktop_img"]["enabled"])
        # Check tomlkit.dump was called once with the updated config_data and file handle
        mock_dump.assert_called_once()
        dumped_data, dumped_file_handle = mock_dump.call_args[0]
        self.assertEqual(dumped_data, config_data)
        # Check open was called twice: once for reading, once for writing
        self.assertEqual(mock_file.call_count, 2)

    @patch("abk_bwp.abk_config.tomlkit.load")
    @patch("abk_bwp.abk_config.tomlkit.dump")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="[desktop_img]\nenabled = true\n[ftv]\nenabled = true\n",
    )
    def test_update_ftv_disable(self, mock_file, mock_dump, mock_load):
        """Test update disable filed in toml file."""
        config_data = {"desktop_img": {"enabled": True}, "ftv": {"enabled": True}}
        mock_load.return_value = config_data

        self.abk_config.update_enable_field_in_toml_file("ftv", False)

        mock_load.assert_called_once()
        self.assertFalse(config_data["ftv"]["enabled"])
        mock_dump.assert_called_once()
        self.assertEqual(mock_file.call_count, 2)


if __name__ == "__main__":
    unittest.main()
