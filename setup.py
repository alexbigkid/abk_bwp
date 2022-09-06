from setuptools import setup
from abk_bwp.__license__ import __version__, __author__, __license__

setup(name="abk_bwp",
      version=__version__,
      description="Bing wallpaper wrapper",
      url="http://github.com/alexbigkid/abk_bwp",
      author=__author__,
      author_email='abk.software@outlook.com',
      license=__license__,
      packages=["abk_bwp"],
      zip_safe=False)
