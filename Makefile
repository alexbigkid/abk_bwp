.PHONY:	upgrade_setuptools install install_dev install_nth test test_v test_ff test_vff settings help
.SILENT: clean
BWP_HOME = abk_bwp

# -----------------------------------------------------------------------------
# BingWallPaper Makefile rules
# -----------------------------------------------------------------------------
abkbwp:
	cd $(BWP_HOME) && python abk_bwp.py -c logging.yaml -v

abk_bwp_ftv_enable:
	cd $(BWP_HOME) && python abk_bwp.py -c logging.yaml -v -f enable

abk_bwp_ftv_disable:
	cd $(BWP_HOME) && python abk_bwp.py -c logging.yaml -v -f disable

abk_bwp_desktop_enable:
	cd $(BWP_HOME) && python abk_bwp.py -c logging.yaml -v -d enable

abk_bwp_desktop_disable:
	cd $(BWP_HOME) && python abk_bwp.py -c logging.yaml -v -d disable

bwp:
	cd $(BWP_HOME) && python bingwallpaper.py

bwp_log:
	cd $(BWP_HOME) && python bingwallpaper.py -c logging.yaml -l bingwallpaper.log -v

bwp_trace:
	cd $(BWP_HOME) && python bingwallpaper.py -c logging.yaml -v

bwp_install:
	cd $(BWP_HOME) && python install.py -v

bwp_uninstall:
	cd $(BWP_HOME) && python uninstall.py -v


# -----------------------------------------------------------------------------
# Dependency installation Makefile rules
# -----------------------------------------------------------------------------
upgrade_setuptools:
	pip install --upgrade pip setuptools wheel

install: upgrade_setuptools
	pip install --requirement requirements.txt

install_test: upgrade_setuptools
	pip install --requirement requirements_test.txt

install_dev: upgrade_setuptools
	pip install --requirement requirements_dev.txt


# -----------------------------------------------------------------------------
# Running tests Makefile rules
# -----------------------------------------------------------------------------
test:
	python -m unittest discover --start-directory tests

test_v:
	python -m unittest discover --start-directory tests --verbose

test_ff:
	python -m unittest discover --start-directory tests --failfast

test_vff:
	python -m unittest discover --start-directory tests --verbose --failfast

%:
	@:

test_1:
	python -m unittest "tests.$(filter-out $@,$(MAKECMDGOALS))"

coverage:
	coverage run --source $(BWP_HOME) --omit ./tests/*,./abk_bwp/config/*,./abk_bwp/fonts,./samsung-tv-ws-api/*  -m unittest discover --start-directory tests
	@echo
	coverage report
	coverage xml


# -----------------------------------------------------------------------------
# Package bulding and deploying Makefile rules
# -----------------------------------------------------------------------------
sdist: upgrade_setuptools
	@echo "[ python setup.py sdist ]"
	@echo "------------------------------------------------------------------------------------"
	python setup.py sdist

build: upgrade_setuptools
	@echo "[ python -m build ]"
	@echo "------------------------------------------------------------------------------------"
	python -m build

wheel: upgrade_setuptools
	@echo "[ python -m build ]"
	@echo "------------------------------------------------------------------------------------"
	python -m build --wheel

testpypi: wheel
	@echo "[ twine upload -r testpypi dist/*]"
	@echo "------------------------------------------------------------------------------------"
	twine upload -r testpypi dist/*

pypi: wheel
	@echo "[ twine upload -r pypi dist/* ]"
	@echo "------------------------------------------------------------------------------------"
	twine upload -r pypi dist/*


# -----------------------------------------------------------------------------
# Clean up Makefile rules
# -----------------------------------------------------------------------------
clean:
	@echo "deleting log files:"
	@echo "___________________"
	@if [ -f logs/* ]; then ls -la logs/*; fi;
	@if [ -f logs/* ]; then rm -rf logs/*; fi;
	@echo
	@echo "deleting dist files:"
	@echo "___________________"
	@if [ -d dist ]; then ls -la dist; fi;
	@if [ -d dist ]; then rm -rf dist; fi;
	@echo
	@echo "deleting build files:"
	@echo "___________________"
	@if [ -d build ]; then ls -la build; fi;
	@if [ -d build ]; then rm -rf build; fi;
	@echo
	@echo "deleting egg-info files:"
	@echo "___________________"
	@if [ -d *.egg-info ]; then ls -la *.egg-info; fi
	@if [ -d *.egg-info ]; then rm -rf *.egg-info; fi
	@echo
	@echo "deleting __pycache__ directories:"
	@echo "___________________"
	find . -name "__pycache__" -type d -prune
	rm -rf  $(find . -name "__pycache__" -type d -prune)


# -----------------------------------------------------------------------------
# Display info Makefile rules
# -----------------------------------------------------------------------------
settings:
	@echo "HOME             = ${HOME}"
	@echo "PWD              = ${PWD}"
	@echo "SHELL            = ${SHELL}"
	@echo "BWP_HOME         = $(BWP_HOME)"

help:
	@echo "Targets:"
	@echo "--------------------------------------------------------------------------------"
	@echo "  bwp                - executes the abk_bwp program"
	@echo "  bwp_log            - executes the abk_bwp program with logging into a file"
	@echo "  bwp_trace          - executes the abk_bwp program with traces in console"
	@echo "  bwp_install        - executes the abk_bwp install.py"
	@echo "  bwp_uninstall      - executes the abk_bwp uninstall.py"
	@echo "  install            - installs required packages"
	@echo "  install_dev        - installs required packages for development"
	@echo "  install_test       - installs required packages for test"
	@echo "  test               - runs test"
	@echo "  test_v             - runs test with verbose messaging"
	@echo "  test_ff            - runs test fast fail"
	@echo "  test_vff           - runs test fast fail with verbose messaging"
	@echo "  test_1 <file.class.test> - runs a single test"
	@echo "  coverage           - runs test, produces coverage and displays it"
	@echo "--------------------------------------------------------------------------------"
	@echo "  settings           - outputs current settings"
	@echo "  help               - outputs this info"
