# Bing Wallpaper (currently MacOS only) ![Tests](https://github.com/alexbigkid/bingWallPaper/actions/workflows/pipeline.yml/badge.svg)
Downloads daily images from bing.com and sets them as background


### Manually:
If you like to set desktop background manually,
just execute 'python bingwallpaper.py' in your terminal.


### Install:
To schedule the download of the bing image daily,
execute 'python install.py' in your terminal.


### Uninstall:
To delete the schedule of the download of the bing image,
execute 'python uninstall.py' in your terminal.


### Config:
config/bwp_config.toml - is file for configuration.

| config field                 | description                                                                            |
| :--------------------------- | :------------------------------------------------------------------------------------- |
| time_to_fetch                | time to download the bing wall paper image (every day). format is important: hh:mm:ss  |
| app_name                     | python script name to execute for downlaoding the bing images                          |
| image_dir                    | directory where images will be saved usually $HOME/Pictures/BingWallpapers             |
| number_of_images to_keep     | once this number is reached the oldest picture will be deleted                         |
| set_desk_top_image           | if true, script will try to set the image as wall paper, otherwise it just stores them |
| retain_images                | if true images will be kept, when uninstalling bingwallpaper environment               |
| region                       | region from which bing images will be downloaded                                       |
| constant.alternative_regions | available valid regions                                                                |
| ftv.set_image                | if true, app will try to set images for today on frame TV                              |
| ftv.ip_address               | frame TV ip address                                                                    |
| ftv.port                     | frame TV port                                                                          |
| ftv.image_change_frequency   | how often image should be changed, this is time in seconds                             |


### Python tracing:
In order to debug python scripts, you could enable the traces in the
logging.yaml file by changing levels from CRITICAL to DEBUG


#### Scheduler / plist tracing / Troubleshooting
The project contains com.abk.bingwallpaper_debug.py.plist file, which can be used to debug scheduler problems.
1. Copy com.abk.bingwallpaper_debug.py.plist to ~/Library/LaunchAgents/ directory.
2. change to directory: cd ~/Labrary/LaunchAgents
3. load the scheduler with: launchctl load -w com.abk.bingwallpaper_debug.py.plist
4. start the job with: launchctl start com.abk.bingwallpaper_debug.py
5. check the job run: launchctl list | grep com.abk.bingwallpaper_debug.py
   if it return 0 the job ran successfully
6. the traces will be available in
   /tmp/com.abk.bingwallpaper_debug.py.stderr
   and
   /tmp/com.abk.bingwallpaper_debug.py.stdout
7. after troubleshooting don't forget to disable the job for the debug scheduler
8. execute following
   launchctl stop com.abk.bingwallpaper_debug.py
   launchctl unload -w com.abk.bingwallpaper_debug.py.plist
9. delete the debug file from ~/Labrary/LaunchAgents
   rm com.abk.bingwallpaper_debug.py.plist in: ~/Labrary/LaunchAgents


#### tested running on:
- [x] MacOS Monterey (local machine) / Python 3.10.6
- [ ] Linux Ubuntu 20.04  / Python 3.8.9
- [ ] Windows 10 / Python 3.8.9


#### Pipeline Unit Tests ran on:
- [x] Linux latest / Python 3.8.x
- [x] MacOS latest / Python 3.8.x
- [x] Windows latest / Python 3.8.x
