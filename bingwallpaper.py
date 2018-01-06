# http://www.owenrumney.co.uk/2014/09/13/Update_Bing_Desktop_For_Mac.html
# Modified by Alex Berger @ http://www.ABKphoto.com

import os
import errno
import argparse
import shutil
import urllib2
import json
import subprocess
import logging
from sys import platform as _platform
import abkPackage
from abkPackage import abkCommon

configFile = 'config.json'

class BingWallPaper:
	def __init__(self, logLevel):
		self.logger = logging.getLogger(__name__)
		#print("logLevel = %s", logLevel)
		if logLevel != "NONE":
			self.logger.setLevel(logLevel)
		else:
			self.logger.disabled = True

		formatter = logging.Formatter('%(name)s:%(levelname)s:%(message)s')
		handler = logging.StreamHandler()
		handler.setFormatter(formatter)
	
		self.logger.addHandler(handler)
		self.logger.debug("-> BingWallPaper")

	def __del__(self):
		self.logger.debug("<- BingWallPaper")

	def readLinkConfigFile(self, confFile):
		self.logger.debug("-> readLinkConfigFile(%s)", confFile)
		if os.path.islink(__file__):
			linkFile = os.readlink(__file__)
			linkPath = os.path.dirname(linkFile)
			self.logger.info("linkPath = %s", linkPath)
			confFile = os.path.join(linkPath, confFile)
			self.logger.info("confFile = %s", confFile)
		with open(confFile) as jsonData:
			config = json.load(jsonData)
		jsonData.close()
		self.logger.debug("<- readLinkConfigFile(numOfImages2Keep=%d)", config['numOfImages2Keep'])
		return config['numOfImages2Keep']

	def DefinePixDirs(self):
		self.logger.debug("-> DefinePixDirs")
		homeDir = abkCommon.GetHomeDir()
		self.logger.info("homeDir: %s", homeDir)
		srcDir = homeDir+"/Pictures/BingWallpapersNew"
		dstDir = homeDir+"/Pictures/BingWallpapersOld"

		abkCommon.EnsureDir(srcDir)
		abkCommon.EnsureDir(dstDir)
		self.logger.debug("<- DefinePixDirs(srcDir=%s, dstDir=%s)", srcDir, dstDir)
		return srcDir, dstDir

	def MoveOldBackgroundPix(self, src, dst, num):
		self.logger.debug("-> MoveOldBackgroundPix(%s, %s, %d)", src, dst, num)
		for srcFile in os.listdir(src):
			self.logger.info("srcFile to move %s", srcFile)
			srcFile = os.path.join(src, srcFile)
			dstFile = os.path.join(dst, srcFile)
			shutil.move(srcFile, dstFile)
		
		listOfFiles = []
		for f in os.listdir(dst):
			if f.endswith('.jpg'):
				listOfFiles.append(f)
		listOfFiles.sort()
		self.logger.debug("listOfFile = [%s]" % ', '.join(map(str, listOfFiles)))
		numberOfJpgs = len(listOfFiles)
		self.logger.info("numberOfJpgs = %d", numberOfJpgs)
		if numberOfJpgs > num:
			jpgs2delete =  listOfFiles[0:numberOfJpgs-num]
			self.logger.info("jpgs2delete = [%s]" % ', '.join(map(str, jpgs2delete)))
			num2delete = len(jpgs2delete)
			self.logger.info("jpgs2delete = %d", num2delete)
			for delFile in jpgs2delete:
				self.logger.info("deleting file = %s", delFile)
				try:
					os.unlink(os.path.join(dst, delFile))
				except:
					self.logger.error("deleting %s failed", delFile)
		else:
			self.logger.info("no images to delete")
			

		self.logger.debug("<- MoveOldBackgroundPix")
	
	def DownloadBingImage(self, dstDir):
		self.logger.debug("-> DownloadBingImage(%s)", dstDir)
		response = urllib2.urlopen("http://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US")
		obj = json.load(response)
		url = (obj['images'][0]['urlbase'])
		name = (obj['images'][0]['fullstartdate'])
		url = 'http://www.bing.com' + url + '_1920x1080.jpg'
		fullFileName = os.path.join(dstDir, name+'.jpg')

		self.logger.info("Downloading %s to %s", url, fullFileName)
		f = open(fullFileName, 'w')
		pic = urllib2.urlopen(url)
		f.write(pic.read())
		f.close()
		self.logger.debug("<- DownloadBingImage(fullFileName=%s)", fullFileName)
		return fullFileName

	def setDesktopBackground(self, fileName):
		self.logger.debug("-> setDesktopBackground(%s)", fileName)
		#----- Start platform dependency  -----
		if _platform == "darwin":
			# MAC OS X ------------------------
			self.logger.info("Mac OS X environment")
			SCRIPT_MAC = """/usr/bin/osascript<<END
tell application "Finder"
set desktop picture to POSIX file "%s"
end tell
END"""
			subprocess.call(SCRIPT_MAC%fileName, shell=True)

		elif _platform == "linux" or _platform == "linux2":
			# linux ---------------------------
			self.logger.info("Linux environment")

		elif _platform == "win32" or _platform == "win64":
			# Windows or Windows 64-bit -----
			self.logger.info("Windows environment")
		#----- End platform dependency  -----
		else:
			self.logger.error("Not known OS environment")
			raise NameError("Not known OS environment")

		self.logger.info("Set background to %s", fileName)
		self.logger.debug("<- setDesktopBackground()")

def main():
	parser = argparse.ArgumentParser(description='Sets picture from Bing as background')
	parser.add_argument("-l", "--log", dest="logLevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set the logging level")
	args = parser.parse_args()
	if args.logLevel:
		bwp = BingWallPaper(getattr(logging, args.logLevel))
	else:
		bwp = BingWallPaper("NONE")

	(srcDir, dstDir) = bwp.DefinePixDirs()
	numOfImages = bwp.readLinkConfigFile(configFile)
	bwp.MoveOldBackgroundPix(srcDir, dstDir, numOfImages)
	fileName = bwp.DownloadBingImage(srcDir)
	bwp.setDesktopBackground(fileName)

if __name__ == '__main__':
	main()
