# Bing Wallpaper ![Tests](https://github.com/alexbigkid/abk_bwp/actions/workflows/pipeline.yml/badge.svg) [![codecov](https://codecov.io/gh/alexbigkid/abk_bwp/branch/master/graph/badge.svg)](https://codecov.io/gh/alexbigkid/abk_bwp)
Downloads daily Bing images and sets them as desktop wallpaper

[TOC]


## Disclaimer
Please do not download or use any image that violates its copyright terms.


## Installation

### Prerequisites
In order successfully run <code>abk_bwp</code> app, you would need:
- MacOS
- Python >=3.12
- Install python dependencies

### Python and Python dependencies installation on MacOS.
On you terminal command line
- if you haven't installed <b>Homebrew</b> yet (password probably required):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
- install <b>uv</b> - Python version and Python package manager tool with:
```bash
brew install uv
```
- clone <b>abk_bwp</b> repository:
```bash
git clone https://github.com/alexbigkid/abk_bwp
cd abk_bwp
```
- install Python dependencies
```bash
uv sync
```
- and run:
```bash
uv run bwp
```

## Configuring the app
Please see the file <code>src/abk_bwp/config/bwp_config.toml</code> file. There are some setting you might want to change. Like the image size, which should ideally correspond to the size of your display. In the config file you will find also detailed explanation, what exactly each configuration item is for.

For Uploading the images to TV please see the <code>src/abk_bwp/config/ftv_data.toml</code> configuration.


### Makefile rules
There are some Makefile rules, which are created for your convenience. For more help with rules type: make help
Here are some described in the table

| makefile rule            | description                                                           |
| :----------------------- | :-------------------------------------------------------------------- |
| bwp                      | executes the abk_bwp with traces in console                           |
| quiet                    | executes the abk_bwp in quiet mode (no logs)                          |
| log                      | executes the abk_bwp with logging into a file: logs/bingwallpaper.log |
| desktop_enable           | enables auto download (time configured in bwp_config.toml)            |
| desktop_disable          | disables auto download (time configured in bwp_config.toml)           |
| ftv_enable               | WIP: enables Samsung frame TV support (Not working yet)               |
| ftv_disable              | WIP: disables Samsung frame TV support (Not working yet)              |
| install                  | installs required packages                                            |
| install_debug            | installs required packages for debug session                          |
| test                     | runs test                                                             |
| test_v                   | runs test with verbose messaging                                      |
| test_ff                  | runs test fast fail                                                   |
| test_vff                 | runs test fast fail with verbose messaging                            |
| test_1 <file.class.test> | runs a single test                                                    |
| coverage                 | runs test, produces coverage and displays it                          |
| clean                    | cleans some auto generated build files                                |
| settings                 | outputs current settings                                              |
| help                     | outputs this info                                                     |


### Python tracing:
In order to debug python scripts, you could enable the traces in the
logging.yaml file by changing levels from CRITICAL to DEBUG


#### Scheduler / plist tracing / Troubleshooting
The project contains com.abk.bingwallpaper_debug.sh.plist file, which can be used to debug scheduler problems.
1. Copy com.abk.bingwallpaper_debug.sh.plist to ~/Library/LaunchAgents/ directory.
2. change to directory: cd ~/Library/LaunchAgents
3. load the scheduler with: launchctl load -w com.abk.bingwallpaper_debug.sh.plist
4. start the job with: launchctl start com.abk.bingwallpaper_debug.sh
5. check the job run: launchctl list | grep com.abk.bingwallpaper_debug.sh
   if it return 0 the job ran successfully
6. the traces will be available in
   /tmp/com.abk.bingwallpaper_debug.sh.stderr
   and
   /tmp/com.abk.bingwallpaper_debug.sh.stdout
7. after troubleshooting don't forget to disable the job for the debug scheduler
8. execute following
   launchctl stop com.abk.bingwallpaper_debug.sh
   launchctl unload -w com.abk.bingwallpaper_debug.sh.plist
9. delete the debug file from ~/Library/LaunchAgents
   rm com.abk.bingwallpaper_debug.sh.plist in: ~/Library/LaunchAgents


#### App runs on:
- [x] MacOS Sequoia (local machine) / Python 3.13.3
- [ ] Linux Ubuntu 20.04  / Python 3.12.x
- [ ] Windows 10 / Python 3.12.x


#### Pipeline Unit Tests ran on:
- [x] Linux latest / Python 3.12.x, 3.13.x
- [x] MacOS latest / Python 3.12.x, 3.131.x
- [x] Windows latest / Python 3.12.x, 3.13.x
