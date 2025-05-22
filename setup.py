"""Setup script for abk_bwp package."""

from setuptools import setup, find_packages
import pathlib
from abk_bwp.constants import CONST

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="abk_bwp",
    version=CONST.VERSION,
    description="Bing wallpaper wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/alexbigkid/abk_bwp",
    license=CONST.LICENSE,
    author=CONST.AUTHORS[0]["name"],
    author_email="abk.software@outlook.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: End Users/Desktop",
        "Environment :: MacOS X",
        "Operating System :: MacOS :: MacOS X",
        "Topic :: Desktop Environment",
        "Topic :: Home Automation",
        "Topic :: Multimedia :: Graphics",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate you support Python 3. These classifiers are *not*
        # checked by 'pip install'. See instead 'python_requires' below.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    python_requires=">=3.8, <4",
    keywords="Bing Wallpaper images, Desktop images",
    # package_dir={"": "abk_bwp"},
    # packages=["abk_bwp"],
    # packages=["abk_bwp", "abk_bwp/config", "abk_bwp/fonts"],
    packages=find_packages(where="abk_bwp", include=["config/*", "fonts/*"]),
    install_requires=[
        "colorama",
        "optparse-pretty",
        "pillow",
        "PyYAML",
        "requests",
        "samsungtvws[async,encrypted]",
        "tomli>=1.1.0; python_version<'3.11'",
        "tomlkit",
        "urllib3[secure]",
    ],
    extras_require={  # Optional
        "dev": [
            "build",
            "setuptools",
            "twine",
            "wheel",
            "pip-check",
            "pip-date",
            "pip-chill",
            "pipdeptree",
        ],
        "test": ["coverage", "parameterized", "tox"],
    },
    zip_safe=False,
)
