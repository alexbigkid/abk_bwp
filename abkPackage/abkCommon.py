import os
import errno
import getpass
import logging
import logging.config
logger = logging.getLogger(__name__)

def GetUserName():
	return getpass.getuser()

def GetHomeDir():
	logger.debug("-> GetHomeDir")
	homeDir = os.environ['HOME']
	logger.info("homeDir = %s", homeDir)
	logger.debug("<- GetHomeDir")
	return homeDir

def GetCurrentDir(fileName):
	return os.path.dirname(os.path.realpath(fileName))

def EnsureDir(dirName):
	logger.debug("-> EnsureDir(%s)", dirName)
	if not os.path.exists(dirName):
		try:
			os.makedirs(dirName)
		except OSError as error:
			if error.errno != errno.EEXIST:
				raise
	logger.debug("<- EnsureDir")

def EnsureLinkExists(src, dst):
	logger.debug("-> EnsureLinkExists(%s, %s)", src, dst)
	logger.info("src=%s, dst=%s", src, dst)
	if not os.path.islink(dst):
		logger.info("creating link %s to %s" % (dst, src) )
		try:
			os.symlink(src, dst)
		except OSError as error:
			if error.errno != errno.EEXIST:
				raise
	else:
		logger.info("link %s exists, do nothing" % (dst) )
	logger.debug("<- EnsureLinkExists")
          
