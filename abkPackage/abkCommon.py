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

def GetParentDir(fileName):
	return os.path.dirname(os.path.dirname(fileName))

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
	if not os.path.islink(dst):
		logger.info("creating link %s to %s" % (dst, src))
		try:
			os.symlink(src, dst)
			logger.info("created link %s to %s" % (dst, src))
		except OSError as error:
			if error.errno != errno.EEXIST:
				logger.error("create link failed with error =%d", error.errno)
				raise
	else:
		logger.info("link %s exists, do nothing" % (dst) )
	logger.debug("<- EnsureLinkExists")

def RemoveLink(fileName):
	logger.debug("-> RemoveLink(fileName=%s)", fileName)
	if os.path.islink(fileName):
		try:
			os.unlink(fileName)
			logger.info("deleted link %s", fileName )
		except OSError as error:
			logger.error("failed to delete link %s, with error=%d", fileName, error.errno)
			pass
	else:
		logger.info("link %s does not exist, do nothing", fileName )
	logger.debug("<- RemoveLink")

def DeleteDir(dir2delete):
	logger.debug("-> DeleteDir(dir2delete=%s)", dir2delete)
	if os.path.isdir(dir2delete):
		if len(os.listdir(dir2delete)) == 0:
			try:
				os.rmdir(dir2delete)
				logger.info("deleted dir %s", dir2delete)
			except OSError as ex:
				if ex.errno == errno.ENOTEMPTY:
					logger.error("directory %s is not empty", dir2delete)
		else:
			logger.debug("dir %s is not empty", dir2delete)
			for fileName in os.listdir(dir2delete):
				logger.debug("file=%s", fileName)
	logger.debug("<- DeleteDir")
