"""Cli - entry point to the abk_bwp package."""

from abk_bwp.bingwallpaper import bingwallpaper
from abk_bwp import clo


def main():
    """Main function."""
    command_line_options = clo.CommandLineOptions()
    command_line_options.handle_options()
    bingwallpaper(command_line_options)
