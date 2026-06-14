.PHONY: install install-dev lint test check compile ci-help

VENV ?= .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
RUFF := $(VENV)/bin/ruff
PYTEST := $(VENV)/bin/pytest

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

install: $(VENV)/bin/activate
	$(PIP) install -r requirements.txt

install-dev: $(VENV)/bin/activate
	$(PIP) install -r requirements.txt -r requirements-dev.txt

lint: install-dev
	$(RUFF) check src tests scripts

test: install-dev
	$(PYTEST)

compile: install-dev
	$(PYTHON) -m compileall -q src scripts

check: lint test compile

ci-help:
	@echo "Setup:  make install-dev"
	@echo "Local CI (same as GitHub Actions): make check"
