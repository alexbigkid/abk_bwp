.PHONY:	upgrade_setuptools install install_dev test test_verbose exif_rename exif_rename3 settings help
.SILENT: bwp coverage clean

bwp:
	echo "[ python ./bingwallpaper.py -c ./logging.yaml -v ]"
	echo "------------------------------------------------------------------------------------"
	python ./bingwallpaper.py -c ./logging.yaml -v

upgrade_setuptools:
	pip install --upgrade setuptools

install: upgrade_setuptools
	pip install --requirement requirements.txt

install_dev: upgrade_setuptools
	pip install --requirement requirements_dev.txt

install_nth: upgrade_setuptools
	pip install --requirement requirements_nth.txt

test:
	python -m unittest discover --start-directory tests

test_v:
	python -m unittest discover --start-directory tests --verbose

test_ff:
	python -m unittest discover --start-directory tests --failfast

test_vff:
	python -m unittest discover --start-directory tests --verbose --failfast

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
	@echo "  bwp                - executes the main program"
	@echo "  install            - installs required packages"
	@echo "  install_dev        - installs required development packages"
	@echo "  install_nth        - installs nice-to-have packages"
	@echo "  test               - runs test"
	@echo "  test_v             - runs test with verbose messaging"
	@echo "  test_ff            - runs test fast fail"
	@echo "  test_vff           - runs test fast fail with verbose messaging"
	@echo "--------------------------------------------------------------------------------"
	@echo "  coverage           - runs test, produces coverage and displays it"
	@echo "  settings           - outputs current settings"
	@echo "  help               - outputs this info"
