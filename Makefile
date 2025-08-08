.PHONY: run test lint format precommit ci setup

run:
	python app.py

test:
	pytest -q

lint:
	pre-commit run --all-files

format:
	black .
	isort . --profile black

precommit:
	pip install pre-commit
	pre-commit install
	pre-commit run --all-files

setup:
	pip install -r requirements.txt
	pip install pre-commit
