.PHONY:	upgrade_setuptools install install_dev test test_verbose exif_rename exif_rename3 settings help
.SILENT: bwp coverage clean

# python is sometimes linked to python v2 and sometimes to python v3
# So to make sure make rules work on other computers 2nd set of rules are created
upgrade_setuptools:
	pip install --upgrade setuptools

install: upgrade_setuptools
	pip install --requirement requirements.txt

install_user: upgrade_setup
	pip install --user --requirement requirements.txt

install_dev: upgrade_setuptools
	pip install --requirement requirements_dev.txt

install_dev_user: upgrade_setup
	pip install --user --requirement requirements_dev.txt

test:
	python -m unittest discover --start-directory tests

test_ff:
	python -m unittest discover --start-directory tests --failfast

test_verbose:
	python -m unittest discover --start-directory tests --verbose

bwp:
	echo "[ python ./bingwallpaper.py -c ./logging.yaml -v ]"
	echo "------------------------------------------------------------------------------------"
	python ./bingwallpaper.py -c ./logging.yaml -v

clean:
	@echo "deleting log files:"
	@echo "___________________"
	ls -la *.log*
	rm *.log*

# ----------------------------
# those rules should be universal
# ----------------------------
coverage:
	coverage run --source ./,abkPackage --omit abkPackage/__init__.py,./tests/* -m unittest discover --start-directory tests
	@echo
	coverage report
	coverage xml

settings:
	@echo "HOME             = ${HOME}"
	@echo "PWD              = ${PWD}"
	@echo "SHELL            = ${SHELL}"

help:
	@echo "Targets:"
	@echo "--------------------------------------------------------------------------------"
	@echo "  exif_rename        - executes the main program"
	@echo "  install            - installs required packages"
	@echo "  install_user       - installs required packages in user's dir"
	@echo "  install_venv       - installs required packages in virtual env dir"
	@echo "  install_dev        - installs required development packages"
	@echo "  install_dev_user   - installs required development packages in user's dir"
	@echo "  install_dev_venv   - installs required development packages in virtual env dir"
	@echo "  test               - runs test"
	@echo "  test_verbose       - runs test with verbose messaging"
	@echo "--------------------------------------------------------------------------------"
	@echo "  coverage           - runs test, produces coverage and displays it"
	@echo "  settings           - outputs current settings"
	@echo "  help               - outputs this info"
