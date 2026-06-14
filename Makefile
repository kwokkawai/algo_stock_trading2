.PHONY: install install-dev lint test check compile ci-help daily-run weekly-report monthly-report install-scheduler uninstall-scheduler

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
	@echo "Automation: make daily-run | weekly-report | monthly-report"
	@echo "Scheduler:  make install-scheduler"

daily-run:
	@chmod +x scripts/daily_run.sh scripts/lib/common.sh
	@./scripts/daily_run.sh

weekly-report:
	@chmod +x scripts/weekly_report.sh scripts/lib/common.sh
	@./scripts/weekly_report.sh

monthly-report:
	@chmod +x scripts/monthly_report.sh scripts/lib/common.sh
	@./scripts/monthly_report.sh

install-scheduler:
	@chmod +x scripts/install_launchd.sh scripts/daily_run.sh scripts/weekly_report.sh scripts/monthly_report.sh scripts/lib/common.sh
	@./scripts/install_launchd.sh install

uninstall-scheduler:
	@./scripts/install_launchd.sh uninstall
