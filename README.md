# NHL Data Platform

A personal data engineering project that extracts, transforms and analyzes NHL data, with the goal of building ML models to predict game outcomes and player performance.

## Overview

This project follows a modern data pipeline architecture:

```
NHL API → Extract → Raw (JSON) → Load → DuckDB (raw) → Transform → DuckDB (staging + analytics)
```

**Current state:** the data layer is complete for seasons 2010-11 to 2025-26: schedules, team boxscores and player boxscores (skaters and goalies) for regular season and playoffs, organised into tidy per-game logs ready for analysis and ML. See [`docs/data-dictionary.md`](docs/data-dictionary.md) for every table, grain and caveat.

| | |
|---|---|
| Seasons | 16 (2010-11 to 2025-26) |
| Games with full boxscores | 20,591 (regular season + playoffs) |
| Analytics tables | team, skater and goalie game logs, team season stats |
| Tests | 32 (pytest) |

**Planned:** exploratory analysis, feature engineering and ML models (game outcomes, player performance).

## Data Quality

- **Idempotent loads:** `raw.pipeline_runs` records what has been loaded, so the pipeline can be rerun safely and resumes where it stopped.
- **Polite extraction:** boxscores are fetched with 2 parallel workers, retries and atomic writes (more workers trigger HTTP 429 from the API).
- **Validation:** `make validate` checks the warehouse after every load, for example that every finished game has a boxscore, every boxscore has exactly two teams, and boxscore goals match the schedule score.

## Project Structure

```
nhl-data-platform/
├── data/
│   └── raw/                   # raw JSON files from the NHL API
│       └── season=XXXX/
│           ├── team=XXX/
│           │   └── schedule.json
│           └── boxscores/
│               └── {game_id}.json
├── src/
│   ├── extract/
│   │   ├── extract_schedule.py    # fetch schedule data from NHL API
│   │   ├── extract_teams.py       # fetch teams for a given season from NHL API
│   │   └── extract_boxscores.py   # fetch boxscores for every finished game (parallel, retries, skip)
│   ├── load/
│   │   ├── load_raw_to_duckdb.py  # load raw schedule JSON into DuckDB
│   │   ├── load_boxscores_to_duckdb.py  # load boxscores (team, skaters, goalies) into DuckDB
│   │   └── pipeline_runs.py       # track which teams/seasons have been loaded
│   ├── transform/
│   │   ├── transform_games.py     # raw → staging (regular season + playoffs)
│   │   ├── build_team_stats.py    # staging → analytics.team_stats (legacy)
│   │   └── build_game_logs.py     # boxscores → team/skater/goalie game logs + season stats
│   └── pipeline/
│       ├── run_pipeline.py        # orchestrates extract, load and transform for a full season
│       └── validate.py            # consistency checks over the warehouse
├── docs/
│   └── data-dictionary.md     # tables, grain, columns, caveats
├── warehouse/
│   └── nhl.duckdb             # local DuckDB database
└── Makefile                   # common commands
```

## Database Layers

| Schema | Description |
|--------|-------------|
| `raw` | Data as-is from the NHL API |
| `staging` | Cleaned and typed data (regular season + playoffs separated) |
| `analytics` | Per-game logs (team, skater, goalie) and season stats, ready for analysis and ML |

## Getting Started

**Install dependencies:**
```bash
make install
```

**Run the full pipeline for a season:**
```bash
make pipeline SEASON=20232024
```

This fetches all teams for the season, extracts and loads schedule data and boxscores, builds the game logs, and prints a summary of regular season and playoff games loaded. Already-loaded seasons are skipped automatically.

**Build the whole warehouse (2010-11 to 2025-26) and check it:**
```bash
make all-seasons
make validate
```

## Available Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make pipeline SEASON=X` | Run full pipeline for a season (extract + load + transform) |
| `make extract TEAM=X SEASON=X` | Extract only (single team) |
| `make load TEAM=X SEASON=X` | Load only (single team) |
| `make boxscores SEASON=X` | Extract and load boxscores for a season |
| `make all-seasons` | Run the full pipeline for 2010-11 to 2025-26 |
| `make validate` | Run data consistency checks on the warehouse |
| `make format` | Format code with ruff |
| `make lint` | Lint code with ruff |
| `make test` | Run tests |
| `make clean-db` | Delete the local DuckDB database |

## Season Format

Seasons follow the NHL format: `YYYYYYYY` (e.g., `20232024` for the 2023-24 season).

## Tech Stack

- **Python:** data extraction and pipeline orchestration
- **DuckDB:** local analytical database
- **pytest** and **ruff:** tests, linting and formatting
- **NHL API:** public API at `https://api-web.nhle.com/v1`
