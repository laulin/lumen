.PHONY: test lint type-check clean integration

PYTHON = ./.env/bin/python3

test:
	PYTHONPATH=src $(PYTHON) -m coverage run -m unittest discover tests
	PYTHONPATH=src $(PYTHON) -m coverage report -m

lint:
	PYTHONPATH=src $(PYTHON) -m ruff check src tests

type-check:
	PYTHONPATH=src $(PYTHON) -m mypy src tests

integration:
	PYTHONPATH=src $(PYTHON) tests/integration/test_suite.py


clean:
	rm -rf .coverage .mypy_cache .ruff_cache build dist src/*.egg-info

