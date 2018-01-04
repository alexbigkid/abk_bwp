# bingWallPaper4Mac
sets Bing image as a desktop background on a Mac OS X
when user logs in or at a specific time.

Manually:
If you like to set desktop background manually,
just execute 'python bingwallpaper.py' in your terminal.

Install:
To schedule the download of the bing image daily,
execute 'python install.py' in your terminal.

Uninstall:
To delete the schedule of the download of the bing image,
execute 'python uninstall.py' in your terminal.

Config:
By default the job for downloading the bing image is set to 8:30am.
In order to change the the time, please modify the config.json file.

Python tracing:
In order to debug python scripts, you could enable the traces in the
logging.conf file by changing levels from CRITICAL to DEBUG

Scheduler / plist tracing
The project contains com.abk.bingwallpaper_debug.py.plist file, whcih
can be used to debug scheduler problems.
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
7. after troubleshooting don't forget to disable the job for the debig scheduler
8. execute following
   launchctl stop com.abk.bingwallpaper_debug.py
   launchctl unload -w com.abk.bingwallpaper_debug.py.plist
9. delete the debug file from ~/Labrary/LaunchAgents
   rm com.abk.bingwallpaper_debug.py.plist in: ~/Labrary/LaunchAgents
