# :octocat: bingWallPaper4Mac - Bing images :octocat:
Downloads daily images from bing.com and sets them as background

## Triggers
- user logs in or
- at a specific time (defined in the plist file).

### Manually:
If you like to set desktop background manually,
just execute 'python3 bingwallpaper.py' in your terminal.

### Install:
To schedule the download of the bing image daily,
execute 'python3 install.py' in your terminal.

### Uninstall:
To delete the schedule of the download of the bing image,
execute 'python3 uninstall.py' in your terminal.

### Config:
config.json - is file for configuration.
By default the job for downloading the bing image is set to 8:30am.
In order to change the time, please modify the config.json file.
If you like to keep more images you can increase the number of images to keep
Default is 365 days - 1 year of images

### Python tracing:
In order to debug python scripts, you could enable the traces in the
logging.conf file by changing levels from CRITICAL to DEBUG

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
- [x] MacOS Big Sur (local machine) / Python 3.8.9
- [ ] Linux Ubuntu 20.04  / Python 3.8.9
- [ ] Windows 10 / Python 3.8.9

![Tests](https://github.com/alexbigkid/bingWallPaper/actions/workflows/pipeline.yml/badge.svg)
