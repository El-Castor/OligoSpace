SHELL := /bin/sh
API_ENV ?= oligospace-api
BIOINFO_ENV ?= oligospace-bioinfo
PYTHONPATH := apps/api/src
PYTHON_RUNNER ?= conda
API_TOOLING_IMAGE ?= oligospace-api-tooling
BIOINFO_TOOLING_IMAGE ?= oligospace-bioinfo-tooling
WEB_TOOLING_IMAGE ?= oligospace-web-tooling

.PHONY: dev-env dev stop logs python-tooling web-tooling format lint typecheck test test-integration test-e2e test-local migrate seed import-oligos compose-config backup restore-test

ifeq ($(PYTHON_RUNNER),container)
API_RUN = docker run --rm --volume "$(CURDIR):/workspace" --workdir /workspace/apps/api --env PYTHONPATH=/workspace/apps/api/src $(API_TOOLING_IMAGE) micromamba run --name base
BIOINFO_RUN = docker run --rm --volume "$(CURDIR):/workspace" --workdir /workspace/services/bioinfo-worker --env PYTHONPATH=/workspace/services/bioinfo-worker/src $(BIOINFO_TOOLING_IMAGE) micromamba run --name base
WEB_RUN = docker run --rm $(WEB_TOOLING_IMAGE) npm

python-tooling:
	docker build --file infra/docker/api/Dockerfile --tag $(API_TOOLING_IMAGE) .
	docker build --file infra/docker/bioinfo-worker.Dockerfile --tag $(BIOINFO_TOOLING_IMAGE) .

web-tooling:
	docker build --file infra/docker/web/Dockerfile --target tooling --tag $(WEB_TOOLING_IMAGE) .
else
API_RUN = conda run -n $(API_ENV)
BIOINFO_RUN = conda run -n $(BIOINFO_ENV)
WEB_RUN = npm

python-tooling:

web-tooling:
endif

dev-env:
	python scripts/generate_dev_env.py

dev:
	docker compose up --build

stop:
	docker compose down

logs:
	docker compose logs --follow api web bioinfo-worker

format: python-tooling
	cd apps/api && $(API_RUN) ruff check --fix . ../../scripts/migration_excel
	cd apps/api && $(API_RUN) ruff format . ../../scripts/migration_excel
	cd services/bioinfo-worker && $(BIOINFO_RUN) ruff check --fix .
	cd services/bioinfo-worker && $(BIOINFO_RUN) ruff format .

lint: python-tooling web-tooling
	cd apps/api && $(API_RUN) ruff check . ../../scripts/migration_excel
	cd services/bioinfo-worker && $(BIOINFO_RUN) ruff check .
	cd apps/web && $(WEB_RUN) run lint

typecheck: python-tooling web-tooling
	cd apps/api && $(API_RUN) mypy src
	cd services/bioinfo-worker && $(BIOINFO_RUN) mypy src
	cd apps/web && $(WEB_RUN) run typecheck

test: python-tooling web-tooling
	cd apps/api && $(API_RUN) pytest tests
	cd services/bioinfo-worker && $(BIOINFO_RUN) pytest
	cd apps/web && $(WEB_RUN) run test

test-integration:
	docker compose --profile test rm --stop --force postgres-test >/dev/null
	@status=0; docker compose --profile test run --build --rm api-integration-test || status=$$?; docker compose --profile test rm --stop --force postgres-test >/dev/null; exit $$status

test-e2e:
	docker compose up --build --detach caddy
	docker compose --profile test build web-e2e
	docker compose --profile test run --rm --no-deps web-e2e

test-local: python-tooling
	cd apps/api && $(API_RUN) pytest -q tests

migrate:
	docker compose run --rm migrate

seed:
	docker compose run --rm seed

import-oligos:
	@test -n "$(SOURCE)" || (echo "Usage: make import-oligos SOURCE=/absolute/path.xlsx" >&2; exit 2)
	cd apps/api && $(API_RUN) python ../../scripts/migration_excel/preview_import.py "$(SOURCE)"

compose-config:
	docker compose config --quiet

backup:
	docker compose --profile operations run --rm backup

restore-test:
	@echo "Use infra/backup/restore-test.sh with an explicit *_restore_test database; see docs/BACKUP_RESTORE.md."
