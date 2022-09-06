.PHONY:	upgrade_setuptools install install_dev install_nth test test_v test_ff test_vff settings help
.SILENT: main bwp bwp_log bwp_trace bwp_install bwp_uninstall coverage clean
BWP_HOME = abk_bwp

main:
	python $(BWP_HOME)/main.py

bwp:
	python $(BWP_HOME)/bingwallpaper.py

bwp_log:
	echo "[ python $(BWP_HOME)/bingwallpaper.py -c $(BWP_HOME)/logging.yaml -l bingwallpaper.log -v ]"
	echo "------------------------------------------------------------------------------------"
	python $(BWP_HOME)/bingwallpaper.py -c $(BWP_HOME)/logging.yaml -l bingwallpaper.log -v

bwp_trace:
	echo "[ python $(BWP_HOME)/bingwallpaper.py -c $(BWP_HOME)/logging.yaml -v ]"
	echo "------------------------------------------------------------------------------------"
	python $(BWP_HOME)/bingwallpaper.py -c $(BWP_HOME)/logging.yaml -v

bwp_install:
	echo "[ python $(BWP_HOME)/install.py -v ]"
	echo "------------------------------------------------------------------------------------"
	python $(BWP_HOME)/install.py -v

bwp_uninstall:
	echo "[ python $(BWP_HOME)/uninstall.py -v ]"
	echo "------------------------------------------------------------------------------------"
	python $(BWP_HOME)/uninstall.py -v

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

%:
	@:

test_1:
	python -m unittest "tests.$(filter-out $@,$(MAKECMDGOALS))"

clean:
	@echo "deleting log files:"
	@echo "___________________"
	ls -la *.log*
	rm *.log*

# ----------------------------
# those rules should be universal
# ----------------------------
coverage:
	coverage run --source $(BWP_HOME) --omit ./config/*,./tests/*,./fonts,./samsung-tv-ws-api/*  -m unittest discover --start-directory tests
	@echo
	coverage report
	coverage xml

settings:
	@echo "HOME             = ${HOME}"
	@echo "PWD              = ${PWD}"
	@echo "SHELL            = ${SHELL}"
	@echo "BWP_HOME         = $(BWP_HOME)"

help:
	@echo "Targets:"
	@echo "--------------------------------------------------------------------------------"
	@echo "  bwp                - executes the main program"
	@echo "  bwp_log            - executes the main program with logging into a file"
	@echo "  bwp_trace          - executes the main program with traces in console"
	@echo "  bwp_install        - executes the main install.py"
	@echo "  bwp_uninstall      - executes the main uninstall.py"
	@echo "  install            - installs required packages"
	@echo "  install_dev        - installs required development packages"
	@echo "  install_nth        - installs nice-to-have packages"
	@echo "  test               - runs test"
	@echo "  test_v             - runs test with verbose messaging"
	@echo "  test_ff            - runs test fast fail"
	@echo "  test_vff           - runs test fast fail with verbose messaging"
	@echo "  test_1 <file.class.test> - runs a single test"
	@echo "  coverage           - runs test, produces coverage and displays it"
	@echo "--------------------------------------------------------------------------------"
	@echo "  settings           - outputs current settings"
	@echo "  help               - outputs this info"
