# http://www.owenrumney.co.uk/2014/09/13/Update_Bing_Desktop_For_Mac.html
# modified by Alex Berger

import os
import errno
from os.path import expanduser
from sys import platform as _platform


if _platform == "linux" or _platform == "linux2":
	# linux
	from bingwallpaper_lnx import set_bing_wallpaper
elif _platform == "darwin":
	# MAC OS X
	from bingwallpaper_mac import set_bing_wallpaper   
elif _platform == "win32" or _platform == "win64":
	# Windows or Windows 64-bit
	from bingwallpaper_win import set_bing_wallpaper


set_bing_wallpaper()


