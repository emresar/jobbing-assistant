.PHONY: format
format:
	black src test
	isort src test

.PHONY: lint
lint:
	pylint src
	mypy src

.PHONY: test
test:
	python -m pytest .

.PHONY: setupdev
setupdev:
	pip install --upgrade pip setuptools wheel
	pip install -e .[dev,testing]
	pre-commit install

.PHONY: all
all: format lint test
