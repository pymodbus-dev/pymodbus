# Makefile for the `pymodbus' package.

WORKON_HOME ?= $(HOME)/.virtualenvs
VIRTUAL_ENV ?= $(WORKON_HOME)/pymodbus
PATH := $(VIRTUAL_ENV)/bin:$(PATH)
MAKE := $(MAKE) --no-print-directory
SHELL = bash

default:
	@echo 'Makefile for pymodbus'
	@echo
	@echo 'Usage:'
	@echo
	@echo '    make install    install the package in a virtual environment'
	@echo '    make reset      recreate the virtual environment'
	@echo '    make check      check coding style (PEP-8, PEP-257)'
	@echo '    make test       run the test suite, report coverage'
	@echo '    make tox        run the tests on all Python versions'
	@echo '    make docs        creates sphinx documentation in html'
	@echo '    make clean        cleanup all temporary files'
	@echo

install:
	@test -d "$(VIRTUAL_ENV)" || mkdir -p "$(VIRTUAL_ENV)"
	@test -x "$(VIRTUAL_ENV)/bin/python" || virtualenv --quiet "$(VIRTUAL_ENV)"
	@test -x "$(VIRTUAL_ENV)/bin/pip" || easy_install pip
	@pip install --quiet --requirement=requirements.txt
	@pip uninstall --yes pymodbus &>/dev/null || true
	@pip install --quiet --no-deps --ignore-installed .

reset:
	$(MAKE) clean
	rm -Rf "$(VIRTUAL_ENV)"
	$(MAKE) install

check: install
	@pip install --upgrade --quiet --requirement=requirements-checks.txt
	@flake8

test: install
	@pip install --quiet --requirement=requirements-tests.txt
	@pytest --cov=pymodbus/ --cov-report term-missing
	@coverage report --fail-under=90

tox: install
	@pip install --quiet tox && tox

docs: install
	@pip install --quiet --requirement=requirements-docs.txt
	@cd doc && make clean && make html

publish: install
	git push origin && git push --tags origin
	$(MAKE) clean
	pip install --quiet twine wheel
	python setup.py sdist bdist_wheel
	twine upload dist/*
	$(MAKE) clean

clean:
	@rm -Rf *.egg .eggs *.egg-info *.db .cache .coverage .tox build dist docs/build htmlcov doc/_build test/.Python test/pip-selfcheck.json test/lib/ test/include/ test/bin/
	@find . -depth -type d -name __pycache__ -exec rm -Rf {} \;
	@find . -type f -name '*.pyc' -delete

.PHONY: default install reset check test tox docs publish clean
