"""Cli - entry point to the abk_bwp package."""

from abk_bwp import clo
from abk_bwp.bingwallpaper import bingwallpaper


def main():
    """Main function."""
    command_line_options = clo.CommandLineOptions()
    command_line_options.handle_options()
    bingwallpaper(command_line_options)
