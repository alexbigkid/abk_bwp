.PHONY:	upgrade_setuptools install install_dev install_nth test test_v test_ff test_vff settings help
.SILENT: abk_bwp bwp bwp_log bwp_trace bwp_install bwp_uninstall coverage clean abk_bwp_ftv
BWP_HOME = abk_bwp

abk_bwp:
	echo "[ python $(BWP_HOME)/abk_bwp.py -c $(BWP_HOME)/logging.yaml -v ]"
	echo "------------------------------------------------------------------------------------"
	python $(BWP_HOME)/abk_bwp.py -c $(BWP_HOME)/logging.yaml -v

abk_bwp_ftv_enable:
	echo "[ python $(BWP_HOME)/abk_bwp.py -c $(BWP_HOME)/logging.yaml -v -f enable ]"
	echo "------------------------------------------------------------------------------------"
	python $(BWP_HOME)/abk_bwp.py -c $(BWP_HOME)/logging.yaml -v -f enable

abk_bwp_ftv_disable:
	echo "[ python $(BWP_HOME)/abk_bwp.py -c $(BWP_HOME)/logging.yaml -v -f disable ]"
	echo "------------------------------------------------------------------------------------"
	python $(BWP_HOME)/abk_bwp.py -c $(BWP_HOME)/logging.yaml -v -f disable

abk_bwp_desktop_enable:
	echo "[ python $(BWP_HOME)/abk_bwp.py -c $(BWP_HOME)/logging.yaml -v -d enable ]"
	echo "------------------------------------------------------------------------------------"
	python $(BWP_HOME)/abk_bwp.py -c $(BWP_HOME)/logging.yaml -v -d enable

abk_bwp_desktop_disable:
	echo "[ python $(BWP_HOME)/abk_bwp.py -c $(BWP_HOME)/logging.yaml -v -d disable ]"
	echo "------------------------------------------------------------------------------------"
	python $(BWP_HOME)/abk_bwp.py -c $(BWP_HOME)/logging.yaml -v -d disable

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

install_test: upgrade_setuptools
	pip install --requirement requirements_test.txt

install_dev: upgrade_setuptools
	pip install --requirement requirements_dev.txt

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
