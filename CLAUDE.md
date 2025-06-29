# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ABK BingWallpaper is a Python application that downloads daily Bing images and sets them as desktop wallpaper on macOS. The project includes support for Samsung Frame TV integration and image metadata management with SQLite database storage.

## Architecture

- **Entry Point**: `src/abk_bwp/cli.py` - Main CLI entry point that calls `bingwallpaper()`
- **Core Logic**: `src/abk_bwp/bingwallpaper.py` - Main application logic with image processing, reactive streams (RxPy), and multi-platform wallpaper setting
- **Configuration**: `src/abk_bwp/config/` - TOML-based configuration with `bwp_config.toml` and `ftv_data.toml`
- **Database**: `src/abk_bwp/db.py` - SQLite database management for image metadata
- **Samsung TV**: `src/abk_bwp/ftv.py` - Samsung Frame TV integration (work in progress)
- **Command Line**: `src/abk_bwp/clo.py` - Command line option parsing
- **Utilities**: `src/abk_bwp/abk_common.py` and `src/abk_bwp/abk_config.py` - Common utilities and configuration helpers

## Development Commands

### Dependencies and Setup
- `uv sync` - Install dependencies
- `uv pip install --group debug` - Install debug dependencies

### Running the Application
- `uv run bwp` - Run with console traces
- `uv run bwp -q` - Run in quiet mode
- `uv run bwp -l` - Run with file logging
- `make bwp`, `make quiet`, `make log` - Makefile shortcuts

### Testing
- `uv run python -m unittest discover --start-directory tests` - Run all tests
- `uv run python -m unittest discover --start-directory tests --verbose` - Verbose tests
- `uv run python -m unittest discover --start-directory tests --failfast` - Fast fail tests
- `uv run python -m unittest "tests.test_module.TestClass.test_method"` - Run single test
- `make test`, `make test_v`, `make test_ff`, `make test_vff` - Makefile shortcuts
- `make test_1 test_module.TestClass.test_method` - Single test via Makefile

### Code Quality
- `uv run ruff check ./src/abk_bwp/ ./tests/` - Lint code
- `uv run ruff check --fix ./src/abk_bwp/ ./tests/` - Lint and auto-fix
- `uv run ruff format ./src/abk_bwp/ ./tests/` - Format code
- `make lint`, `make lint_fix`, `make format` - Makefile shortcuts

### Coverage
- `uv run coverage run --source src/abk_bwp --omit ./tests/*,./src/abk_bwp/config/*,./src/abk_bwp/fonts,./samsung-tv-ws-api/* -m unittest discover --start-directory tests` - Run coverage
- `uv run coverage report` - Show coverage report
- `make coverage` - Run coverage with report

### Configuration Management
- `make desktop_enable` - Enable automatic wallpaper updates
- `make desktop_disable` - Disable automatic wallpaper updates
- `make ftv_enable` - Enable Samsung Frame TV support (WIP)
- `make ftv_disable` - Disable Samsung Frame TV support (WIP)

## Key Configuration Files

- `src/abk_bwp/config/bwp_config.toml` - Main application configuration (image size, display settings)
- `src/abk_bwp/config/ftv_data.toml` - Samsung Frame TV configuration
- `logging.yaml` - Logging configuration (change levels from CRITICAL to DEBUG for tracing)
- `pyproject.toml` - Project metadata, dependencies, and tool configuration (Ruff, UV)

## Technology Stack

- **Package Manager**: UV (modern Python package manager)
- **Testing**: unittest (Python standard library)
- **Linting/Formatting**: Ruff
- **Image Processing**: Pillow (PIL)
- **HTTP Requests**: requests
- **Reactive Programming**: RxPy (reactivex)
- **Database**: SQLite3
- **Configuration**: TOML (tomlkit)
- **Samsung TV Integration**: samsungtvws

## Build System

Uses `pyproject.toml` with hatchling build backend. The project is managed with UV and includes comprehensive Makefile for common tasks.

## Image Management Details

- Downloads images from peapix
- Renames images based on date
- Image organization depends on Frame TV (FTV) configuration:
  - If FTV is disabled: Images ordered into year/month folders
  - If FTV is enabled (in `@src/abk_bwp/config/bwp_config.toml`):
    - Images ordered by month/day
    - Images from different years will be in the same month/day folder
- Daily image download (once per day)
- Generates new images with EXIF data overlaid

## Samsung Frame TV Integration Notes

- When Frame TV is enabled, the app performs the following actions:
  - Connects to Samsung FrameTV
  - Deletes user-defined images from FrameTV
  - Uploads new images for the current day to FrameTV