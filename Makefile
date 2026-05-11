.PHONY: install lint format test extract load reports pipeline check-team-season check-season clean-db clean

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

check-team-season:
	@if [ -z "$(TEAM)" ] || [ -z "$(SEASON)" ]; then \
		echo "Usage: make <target> TEAM=<team_abbrev> SEASON=<season>"; \
		echo "Example: make extract TEAM=SJS SEASON=20242025"; \
		echo "Example: make load TEAM=TOR SEASON=20252026"; \
		echo "Example: make pipeline TEAM=TOR SEASON=20252026"; \
		exit 1; \
	fi

check-season:
	@if [ -z "$(SEASON)" ]; then \
		echo "Usage: make reports SEASON=<season>"; \
		echo "Example: make reports SEASON=20242025"; \
		exit 1; \
	fi

extract: check-team-season
	python src/extract/extract_schedule.py --team $(TEAM) --season $(SEASON)

load: check-team-season
	python src/load/load_raw_to_duckdb.py --team $(TEAM) --season $(SEASON)

reports: check-season
	python src/reports/generate_reports.py --season $(SEASON)

pipeline: extract load

clean-db:
	rm -f warehouse/nhl.duckdb
	@echo "Removed warehouse/nhl.duckdb"

clean: clean-db