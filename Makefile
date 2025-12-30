.PHONY: test lint type-check clean

PYTHON = ./.env/bin/python3

test:
	PYTHONPATH=src $(PYTHON) -m coverage run -m unittest discover tests
	PYTHONPATH=src $(PYTHON) -m coverage report -m

lint:
	PYTHONPATH=src $(PYTHON) -m ruff check src tests

type-check:
	PYTHONPATH=src $(PYTHON) -m mypy src tests


clean:
	rm -rf .coverage .mypy_cache .ruff_cache build dist src/*.egg-info

