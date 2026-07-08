.PHONY: lint format test validate check install-dev

lint:
	ruff check .
	ruff format --check .
	mypy deckflow cli api
	cd web && npm run lint

format:
	ruff format .
	ruff check --fix .

validate:
	deckflow validate examples/python-de-interview

test:
	pytest --cov --cov-report=term-missing --cov-fail-under=75

check: lint validate test
	cd web && npm run typecheck && npm run build

install-dev:
	pip install -e ".[dev]"
	cd web && npm ci
