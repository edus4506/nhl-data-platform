.PHONY: install lint format test extract load reports pipeline

install:
	pip install -r requirements.txt

lint:
	ruff check .
	ruff format --check .

format:
	ruff check . --fix
	ruff format .

test:
	pytest

extract:
	python src/extract/extract_schedule.py --season 20242025

load:
	python src/load/load_raw_to_duckdb.py --season 20242025

reports:
	python src/reports/generate_reports.py --season 20242025

pipeline: extract load test reports
