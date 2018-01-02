# http://www.owenrumney.co.uk/2014/09/13/Update_Bing_Desktop_For_Mac.html
# modified by Alex Berger

import os
import errno
import argparse
import shutil
import urllib2
import json
import subprocess
import logging
#import logging.config
from sys import platform as _platform
import abkPackage
from abkPackage import abkCommon

#logging_conf = 'logging.conf'
class BingWallPaper:
	def __init__(self, logLevel):
		# Create the Logger
		self.logger = logging.getLogger(__name__)
		#print("logLevel = %s", logLevel)
		if logLevel != "NONE":
			self.logger.setLevel(logLevel)

		# Create a Formatter for formatting the log messages
		formatter = logging.Formatter('%(name)s: %(levelname)s: %(message)s')

		# Create Handler
		handler = logging.StreamHandler()
		# Add the Formatter to the Handler
		handler.setFormatter(formatter)
	
		# Add the Handler to the Logger
		self.logger.addHandler(handler)
		self.logger.debug("-> BingWallPaper")

	def __del__(self):
		self.logger.debug("<- BingWallPaper")


	def DefinePixDirs(self):
		self.logger.debug("-> DefinePixDirs")
		home_dir = abkCommon.get_home_dir()
		self.logger.info("home dir: %s", home_dir)
		srcDir = home_dir+"/Pictures/BingWallpapersNew"
		dstDir = home_dir+"/Pictures/BingWallpapersOld"

		abkCommon.ensure_dir(srcDir)
		abkCommon.ensure_dir(dstDir)
		self.logger.debug("<- DefinePixDirs(srcDir=%s, dstDir=%s)", srcDir, dstDir)
		return srcDir, dstDir

	def MoveOldBackgroundPix(self, src, dst):
		self.logger.debug("-> MoveOldBackgroundPix(%s, %s)", src, dst)
		for file in os.listdir(src):
			self.logger.info("file to move %s", file)
			src_file = os.path.join(src, file)
			dst_file = os.path.join(dst, file)
			shutil.move(src_file, dst_file)
		self.logger.debug("<- MoveOldBackgroundPix")
	
	def DownloadBingImage(self, dst_dir):
		self.logger.debug("-> DownloadBingImage(%s)", dst_dir)
		response = urllib2.urlopen("http://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US")
		obj = json.load(response)
		url = (obj['images'][0]['urlbase'])
		name = (obj['images'][0]['fullstartdate'])
		url = 'http://www.bing.com' + url + '_1920x1080.jpg'
		fullFileName = os.path.join(dst_dir, name+'.jpg')

		self.logger.info("Downloading %s to %s", url, fullFileName)
		f = open(fullFileName, 'w')
		pic = urllib2.urlopen(url)
		f.write(pic.read())
		f.close()
		self.logger.debug("<- DownloadBingImage(fullFileName=%s)", fullFileName)
		return fullFileName

	def set_desktop_background(self, filename):
		self.logger.debug("-> set_desktop_background(%s)", filename)
		#----- Start platform dependency  -----
		if _platform == "darwin":
			# MAC OS X ------------------------
			self.logger.info("Mac OS X environment")
			SCRIPT_MAC = """/usr/bin/osascript<<END
tell application "Finder"
set desktop picture to POSIX file "%s"
end tell
END"""
			subprocess.call(SCRIPT_MAC%filename, shell=True)

		elif _platform == "linux" or _platform == "linux2":
			# linux ---------------------------
			self.logger.info("Linux environment")

		elif _platform == "win32" or _platform == "win64":
			# Windows or Windows 64-bit -----
			self.logger.info("Windows environment")
		#----- End platform dependency  -----
		
		self.logger.info("Set background to %s", filename)
		self.logger.debug("<- set_desktop_background()")

def main():
	parser = argparse.ArgumentParser(description='Sets picture from Bing as background')
	parser.add_argument("-l", "--log", dest="logLevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set the logging level")
	args = parser.parse_args()
	if args.logLevel:
		bwp = BingWallPaper(getattr(logging, args.logLevel))
	else:
		bwp = BingWallPaper("NONE")

	(srcDir, dstDir) = bwp.DefinePixDirs()
	bwp.MoveOldBackgroundPix(srcDir, dstDir)
	fileName = bwp.DownloadBingImage(srcDir)
	bwp.set_desktop_background(fileName)

if __name__ == '__main__':
	main()
