# Bing Wallpaper (currently MacOS only) ![Tests](https://github.com/alexbigkid/abk_bwp/actions/workflows/pipeline.yml/badge.svg)
Downloads daily Bing images and sets them as desktop wallpaper


## Disclaimer
Please do not download or use any image that violates its copyright terms.


## Installation
Recommended option:
```html
git clone https://github.com/alexbigkid/abk_bwp
cd abk_bwp
```
or
```html
pip install abk_bwp
```


## Usage
```html
make install
make bwp
```


## Configuring the app
Please see the file abk_bwp/config/bwp_config.toml file. There are some setting you might want to change.
Like the image size, which should ideally correspond to the size of your display.
In the config file you will find also detailed explanation, what exactly each configuration item is for.


## Installing python dependencies:
### Installing with pyenv + virtual environment (Recommended)
If you are like me and don't want to mix your python packages, you want to create python virtual environment before installing dependencies.
I use pyenv tool for that. Here are the steps on MacOS:
1. install brew. Google for it if you don't have it already
2. brew install pyenv - will install pyenv tool
3. brew install pyenv-virtualenv - installs virtualenv pyenv version
4. pyenv versions - will show you currently installed python versions and virtual envs on your system
5. pyenv install --list - will show you all available python versions you could install.
6. pyenv install 3.8.9 - installs python 3.8.9 version
7. pyenv virtualenv 3.8.9 bwp - creates virtual environment [bing wall paper] with python 3.8.9
8. cd <your_project_dir> - change into your project directory e.g.: cd abk_bwp
9. pyenv local bwp - setting the current directory to use [bwp] virtual environment
10. make install - will install all needed python dependency packages into [bwp] virtual environment.
11. make bwp - will download bing image and add title to the image


### Installing without pyenv or python virtual environmet. Note the app does not run with python 2.7
If it is too many steps for you and just want to get it working "quick and dirty".
Warning: there might be some python packages, which might collide with already installed packages.
1. cd abk_bwp - change to the project directory
2. make install - to install python dependency packages in default location
3. make bwp - will download bing image and add title to the image


### Makefile rules
There are some Makefile rules, which are created for your convinience. For more help with rules type: make help
Here are some described in the table

| makefile rule            | description                                                                                |
| :----------------------- | :----------------------------------------------------------------------------------------- |
| make bwp                 | executes the abk_bwp program, which dowloads Bing images and creates a desktop image       |
| make bwp_log             | executes the abk_bwp program, with tracing to the console and log file                     |
| make bwp_trace           | executes the abk_bwp program, with tracing to the console                                  |
| make bwp_desktop_enable  | executes the abk_bwp program, enables auto download (time configured in bwp_config.toml)   |
| make bwp_desktop_disable | executes the abk_bwp program, disables auto download (time configured in bwp_config.toml)  |
| make bwp_ftv_enable      | WIP: executes the abk_bwp program, enables Samsung frame TV support (Not working yet)      |
| make bwp_ftv_disable     | WIP: executes the abk_bwp program, disables Samsung frame TV support (Not working yet)     |
| make install             | installs all required python packages for the app                                          |
| make install_test        | installs all required python packages for app and additional packages to run the unit test |
| make install_dev         | installs all required python packages for app and additional for test and development      |
| make test                | runs unit tests                                                                            |
| make test_v              | runs unit tests with verbosity enabled                                                     |
| make test_ff             | runs unit tests and fails fast on the first broken test                                    |
| make test_vff            | runs unit tests fails fast on the first broken test with verbosity enabled                 |
| make test_1 <test>       | runs one specific unit test                                                                |
| make coverage            | runs unit tests with coverage                                                              |
| make coverage            | runs unit tests with coverage                                                              |
| make clean               | cleans some auto generated build files                                                     |
| make settings            | displays some Makefile settings                                                            |
| make help                | displays Makefile help                                                                     |


### Python tracing:
In order to debug python scripts, you could enable the traces in the
logging.yaml file by changing levels from CRITICAL to DEBUG


#### Scheduler / plist tracing / Troubleshooting
The project contains com.abk.bingwallpaper_debug.sh.plist file, which can be used to debug scheduler problems.
1. Copy com.abk.bingwallpaper_debug.sh.plist to ~/Library/LaunchAgents/ directory.
2. change to directory: cd ~/Labrary/LaunchAgents
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
9. delete the debug file from ~/Labrary/LaunchAgents
   rm com.abk.bingwallpaper_debug.sh.plist in: ~/Labrary/LaunchAgents


#### App runs on:
- [x] MacOS Monterey (local machine) / Python 3.10.6
- [ ] Linux Ubuntu 20.04  / Python 3.8.9
- [ ] Windows 10 / Python 3.8.9


#### Pipeline Unit Tests ran on:
- [x] Linux latest / Python 3.8.x, 3.9.x, 3.10.x
- [x] MacOS latest / Python 3.8.x, 3.9.x, 3.10.x
- [x] Windows latest / Python 3.8.x, 3.9.x, 3.10.x
