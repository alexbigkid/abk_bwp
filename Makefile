.PHONY:	upgrade_setuptools install install_dev install_nth test test_v test_ff test_vff settings help
.SILENT: clean
BWP_HOME = src/abk_bwp

# -----------------------------------------------------------------------------
# BingWallPaper Makefile rules
# -----------------------------------------------------------------------------
ftv_enable:
	cd $(BWP_HOME) && uv run abk_config.py -f enable

ftv_disable:
	cd $(BWP_HOME) && uv run abk_config.py -f disable

ftv_auth:
	cd $(BWP_HOME)/config && uv run frame_tv_authenticator.py

desktop_enable:
	cd $(BWP_HOME) && uv run abk_config.py -d enable

desktop_disable:
	cd $(BWP_HOME) && uv run abk_config.py -d disable

quiet:
	uv run bwp -q

log:
	uv run bwp -l

bwp:
	uv run bwp


# -----------------------------------------------------------------------------
# Dependency installation Makefile rules
# -----------------------------------------------------------------------------
install:
	uv sync

install_debug:
	uv pip install --group debug


# -----------------------------------------------------------------------------
# Running tests Makefile rules
# -----------------------------------------------------------------------------
test:
	uv run python -m unittest discover --start-directory tests

test_v:
	uv run python -m unittest discover --start-directory tests --verbose

test_ff:
	uv run python -m unittest discover --start-directory tests --failfast

test_vff:
	uv run python -m unittest discover --start-directory tests --verbose --failfast

%:
	@:

test_1:
	uv run python -m unittest "tests.$(filter-out $@,$(MAKECMDGOALS))"

coverage:
	uv run coverage run --source $(BWP_HOME) --omit ./tests/*,./src/abk_bwp/config/*,./src/abk_bwp/fonts,./samsung-tv-ws-api/*  -m unittest discover --start-directory tests
	@echo
	uv run coverage report
	uv run coverage xml


# -----------------------------------------------------------------------------
# Running tests Makefile rules
# -----------------------------------------------------------------------------
lint:
	uv run ruff check ./src/abk_bwp/ ./tests/

lint_fix:
	uv run ruff check --fix ./src/abk_bwp/ ./tests/

format:
	uv run ruff format ./src/abk_bwp/ ./tests/


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
	uv clean cache


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
	@echo "  bwp                - executes the abk_bwp with traces in console"
	@echo "  quiet              - executes the abk_bwp in quiet mode (no logs)"
	@echo "  log                - executes the abk_bwp with logging into a file: logs/bingwallpaper.log"
	@echo "  desktop_enable     - enables auto download (time configured in bwp_config.toml)"
	@echo "  desktop_disable    - disables auto download (time configured in bwp_config.toml)"
	@echo "  ftv_enable         - WIP: enables Samsung frame TV support (Not working yet)"
	@echo "  ftv_disable        - WIP: disables Samsung frame TV support (Not working yet)"
	@echo "  install            - installs required packages"
	@echo "  install_debug      - installs required packages for debug session"
	@echo "  test               - runs test"
	@echo "  test_v             - runs test with verbose messaging"
	@echo "  test_ff            - runs test fast fail"
	@echo "  test_vff           - runs test fast fail with verbose messaging"
	@echo "  test_1 <file.class.test> - runs a single test"
	@echo "  coverage           - runs test, produces coverage and displays it"
	@echo "  clean              - cleans some auto generated build files"
	@echo "--------------------------------------------------------------------------------"
	@echo "  settings           - outputs current settings"
	@echo "  help               - outputs this info"
