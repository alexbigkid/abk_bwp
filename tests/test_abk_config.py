"""Unit tests for abk_config.py."""

# Standard library imports
from typing import Union
import unittest
from unittest.mock import patch

# Third party imports
from parameterized import parameterized

# local  modules imports
from context import config
from context import abk_config


class TestAbkBwp(unittest.TestCase):
    """TestAbkBwp."""

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
        self, ftv_input: Union[str, None], ftv_enabled: bool, exp_ftv_enabled: bool
    ) -> None:
        """test__handle_ftv_option__calls_update_enable_field_in_toml_file.

        Args:
            ftv_input (Union[str, None]): FTV input
            ftv_enabled (bool): FTV enabled
            exp_ftv_enabled (bool): expected FTV enabled
        """
        with patch.dict(config.bwp_config, {"ftv": {"enabled": ftv_enabled}}):
            with patch(
                "abk_config.update_enable_field_in_toml_file"
            ) as mock_update_enable_field_in_toml_file:
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
        self, ftv_input: Union[str, None], ftv_enabled: bool, exp_ftv_enabled: bool
    ) -> None:
        """test__handle_ftv_option__does_not_calls_update_enable_field_in_toml_file.

        Args:
            ftv_input (Union[str, None]): FTV input
            ftv_enabled (bool): FTV enabled
            exp_ftv_enabled (bool): expected FTV enabled
        """
        with patch.dict(config.bwp_config, {"ftv": {"enabled": ftv_enabled}}):
            with patch(
                "abk_config.update_enable_field_in_toml_file"
            ) as mock_update_enable_field_in_toml_file:
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
        desktop_img_input: Union[str, None],
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
        with patch.dict(config.bwp_config, {"desktop_img": {"enabled": desktop_img_enabled}}):
            with patch("abk_config.update_enable_field_in_toml_file") as mock_update_enable_field:
                with patch(f"{func_to_call}.bwp_{func_to_call}") as mock_bwp_install_uninstall:
                    abk_config.handle_desktop_auto_update_option(desktop_img_input)
        mock_update_enable_field.assert_called_once_with(
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
        desktop_img_input: Union[str, None],
        desktop_img_enabled: bool,
        exp_desktop_img_enabled: bool,
    ) -> None:
        """test__handle_desktop_auto_update_option__does_not_calls_update_enable_field_in_toml_file.

        Args:
            desktop_img_input (Union[str, None]): desktop image input
            desktop_img_enabled (bool): desktop image enabled
            exp_desktop_img_enabled (bool): expected desktop image enabled
        """
        with patch.dict(config.bwp_config, {"desktop_img": {"enabled": desktop_img_enabled}}):
            with patch("abk_config.update_enable_field_in_toml_file") as mock_update_enable_field:
                abk_config.handle_desktop_auto_update_option(desktop_img_input)
        mock_update_enable_field.assert_not_called()
        self.assertTrue(desktop_img_enabled == exp_desktop_img_enabled)


if __name__ == "__main__":
    unittest.main()
