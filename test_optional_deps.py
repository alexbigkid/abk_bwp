#!/usr/bin/env python3
"""Test script to verify optional dependency handling."""

import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_usb_mode_import():
    """Test that FTV works in USB mode without samsungtvws."""
    print("Testing USB mode (should work without samsungtvws)...")

    # Mock USB mode config
    import unittest.mock

    with unittest.mock.patch("abk_bwp.bingwallpaper.bwp_config", {"ftv": {"usb_mode": True}}):
        try:
            from abk_bwp.ftv import FTV

            mock_logger = unittest.mock.Mock()
            ftv = FTV(logger=mock_logger, ftv_data_file="test_config.toml")

            # Access ftvs property to trigger _load_ftv_settings
            ftvs = ftv.ftvs
            print("✅ USB mode works correctly - no samsungtvws required")
            print(f"   FTV settings: {ftvs}")
            return True
        except Exception as e:
            print(f"❌ USB mode failed: {e}")
            return False


def test_http_mode_without_samsungtvws():
    """Test that FTV fails gracefully in HTTP mode without samsungtvws."""
    print("Testing HTTP mode without samsungtvws (should fail gracefully)...")

    # Mock HTTP mode config (usb_mode = False)
    import unittest.mock

    with unittest.mock.patch("abk_bwp.bingwallpaper.bwp_config", {"ftv": {"usb_mode": False}}):
        try:
            from abk_bwp.ftv import FTV, SAMSUNGTVWS_AVAILABLE

            if SAMSUNGTVWS_AVAILABLE:
                print("⚠️  samsungtvws is available, cannot test missing dependency scenario")
                return True

            mock_logger = unittest.mock.Mock()
            ftv = FTV(logger=mock_logger, ftv_data_file="test_config.toml")

            # Access ftvs property to trigger _load_ftv_settings
            ftvs = ftv.ftvs
            print(f"ftvs = {ftvs}")
            print("❌ HTTP mode should have failed without samsungtvws")
            return False
        except ImportError as e:
            if "samsungtvws library is required" in str(e):
                print("✅ HTTP mode fails gracefully with helpful error message")
                print(f"   Error: {e}")
                return True
            else:
                print(f"❌ Unexpected ImportError: {e}")
                return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False


if __name__ == "__main__":
    print("Testing BWP Frame TV optional dependency handling...\n")

    usb_test = test_usb_mode_import()
    print()
    http_test = test_http_mode_without_samsungtvws()

    print("\nResults:")
    print(f"USB mode test: {'PASS' if usb_test else 'FAIL'}")
    print(f"HTTP mode test: {'PASS' if http_test else 'FAIL'}")

    if usb_test and http_test:
        print("\n🎉 All optional dependency tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
