from setuptools import setup, find_packages
import pathlib
from abk_bwp.__license__ import __version__, __author__, __license__

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="abk_bwp",
    version=__version__,
    description="Bing wallpaper wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/alexbigkid/abk_bwp",
    author=__author__,
    license=__license__,
    author_email="abk.software@outlook.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: MacOS users",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate you support Python 3. These classifiers are *not*
        # checked by 'pip install'. See instead 'python_requires' below.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only"
    ],
    python_requires=">=3.7, <4",
    keywords="Bing images, Desktop images, MacOS, Samsung Frame TV",
    # package_dir={"": "abk_bwp"},
    packages=["config", "fonts", "abk_bwp"],
    install_requires=[
        "colorama",
        "optparse-pretty",
        "pillow",
        "PyYAML",
        "requests",
        "samsungtvws[async,encrypted]",
        "tomli>=1.1.0; python_version<'3.11'",
        "tomlkit",
        "urllib3[secure]"
    ],
    extras_require={  # Optional
        "dev": ["pip-check", "pip-date", "pip-chill", "pipdeptree"],
        "test": ["coverage", "parameterized", "tomli_w"],
    },
    zip_safe=False
)
