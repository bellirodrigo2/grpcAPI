.PHONY: install install_dev test test_coverage lint lint_fix flake8 format build clean upload_pypi

install:
	@echo "Instaling dependencies..."
	pip install .

install_dev:
	@echo "Instaling dev dependencies..."
	pip install .[dev]

test:
	@echo "Running tests..."
	pytest -p no:warnings

test_coverage:
	@echo "Running tests with coverage..."
	pytest -p no:warnings --cov=grpcAPI ./tests

lint:
	@echo "Running linter (ruff)..."
	ruff check . --exclude tests/lib --exclude example/guber/lib

lint_fix:
	@echo "Running linter --fix (ruff)..."
	ruff check --fix . --exclude tests/lib --exclude example/guber/lib

flake8:
	@echo "Running flake8..."
	flake8 grpcAPI

format:
	@echo "Formatting code (black e isort)..."
	black grpcAPI
	isort grpcAPI

clean:
	@echo "Cleaning cache and build/dist related files..."
	@python -c "import shutil, glob, os; [shutil.rmtree(d, ignore_errors=True) for d in ['dist', 'build', '.mypy_cache', '.pytest_cache', '.ruff_cache'] + glob.glob('*.egg-info')]; [shutil.rmtree(os.path.join(r, d), ignore_errors=True) for r, ds, _ in os.walk('.') for d in ds if d == '__pycache__']"

build: clean
	@echo "Building package ..."
	python -m build

upload_pypi: build
	@echo "Uploading package to pypi ..."
	twine upload dist/*