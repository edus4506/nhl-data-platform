.PHONY: install lint format test extract load boxscores pipeline all-seasons validate check-team-season check-season clean-db clean

install:
	pip install -r requirements.txt
	pip install -e .

lint:
	ruff check .
	ruff format --check .

format:
	ruff check . --fix
	ruff format .

test:
	pytest

SEASONS = 20102011 20112012 20122013 20132014 20142015 20152016 20162017 20172018 20182019 20192020 20202021 20212022 20222023 20232024 20242025 20252026

check-team-season:
	@if [ -z "$(TEAM)" ] || [ -z "$(SEASON)" ]; then \
		echo "Usage: make <target> TEAM=<team_abbrev> SEASON=<season>"; \
		echo "Example: make extract TEAM=SJS SEASON=20242025"; \
		echo "Example: make load TEAM=TOR SEASON=20252026"; \
		exit 1; \
	fi

check-season:
	@if [ -z "$(SEASON)" ]; then \
		echo "Usage: make <target> SEASON=<season>"; \
		echo "Example: make pipeline SEASON=20242025"; \
		exit 1; \
	fi

extract: check-team-season
	python src/extract/extract_schedule.py --team $(TEAM) --season $(SEASON)

load: check-team-season
	python src/load/load_raw_to_duckdb.py --team $(TEAM) --season $(SEASON)

boxscores: check-season
	python src/extract/extract_boxscores.py --season $(SEASON)
	python src/load/load_boxscores_to_duckdb.py --season $(SEASON)

pipeline: check-season
	python -m src.pipeline.run_pipeline --season $(SEASON)

all-seasons:
	for season in $(SEASONS); do python -m src.pipeline.run_pipeline --season $$season || exit 1; done

validate:
	python -m src.pipeline.validate

clean-db:
	rm -f warehouse/nhl.duckdb
	@echo "Removed warehouse/nhl.duckdb"

clean: clean-db