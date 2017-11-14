# http://www.owenrumney.co.uk/2014/09/13/Update_Bing_Desktop_For_Mac.html
# modified by Alex Berger

import os
import errno
import shutil
import urllib2
import json
import subprocess
import datetime
from os.path import expanduser

# set wallpaper on Mac using AppleScript
SCRIPT = """/usr/bin/osascript<<END
tell application "Finder"
set desktop picture to POSIX file "%s"
end tell
END"""

dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def set_desktop_background(filename):
	subprocess.call(SCRIPT % filename, shell=True)

def ensure_dir(dir_name):
	if not os.path.exists(dir_name):
		try:
			os.makedirs(dir_name)
		except OSError as error:
			if error.errno != errno.EEXIST:
				raise

home = expanduser('~')
dir_src = home+"/Pictures/BingWallpapersNew"
dir_dst = home+"/Pictures/BingWallpapersOld"

ensure_dir(dir_src)
ensure_dir(dir_dst)

for file in os.listdir(dir_src):
	print ("[%s] Archiving current background image %s to %s" % (dt, file, dir_dst))
	src_file = os.path.join(dir_src, file)
	dst_file = os.path.join(dir_dst, file)
	shutil.move(src_file, dst_file)
 
response = urllib2.urlopen("http://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US")
obj = json.load(response)
url = (obj['images'][0]['urlbase'])
name = (obj['images'][0]['fullstartdate'])
url = 'http://www.bing.com' + url + '_1920x1080.jpg'
path = dir_src+'/'+name+'.jpg'

print ("[%s] Downloading %s to %s" % (dt, url, path))
f = open(path, 'w')
pic = urllib2.urlopen(url)
f.write(pic.read())
f.close()

print ("[%s] Setting background to %s\n" % (dt, path))
set_desktop_background(path)

