# NHL Data Platform

A personal data engineering project that extracts, transforms, and analyzes NHL data — with the goal of building ML models to predict game outcomes and player performance.

## Overview

This project follows a modern data pipeline architecture:

```
NHL API → Extract → Raw (JSON) → Load → DuckDB (raw) → Transform → DuckDB (staging + analytics)
```

**Current state:** schedule data for all NHL teams (dynamically fetched per season), with game results and team statistics per season.

**Planned:** player stats, box scores, visualizations, and ML models.

## Project Structure

```
nhl-data-platform/
├── data/
│   └── raw/                   # raw JSON files from the NHL API
│       └── season=XXXX/
│           └── team=XXX/
│               └── schedule.json
├── src/
│   ├── extract/
│   │   ├── extract_schedule.py    # fetch schedule data from NHL API
│   │   └── extract_teams.py       # fetch teams for a given season from NHL API
│   ├── load/
│   │   ├── load_raw_to_duckdb.py  # load raw JSON into DuckDB
│   │   └── pipeline_runs.py       # track which teams/seasons have been loaded
│   ├── transform/
│   │   ├── transform_games.py     # raw → staging (regular season + playoffs)
│   │   └── build_team_stats.py    # staging → analytics (wins, losses, goals)
│   └── pipeline/
│       └── run_pipeline.py        # orchestrates extract, load and transform for a full season
├── warehouse/
│   └── nhl.duckdb             # local DuckDB database
└── Makefile                   # common commands
```

## Database Layers

| Schema | Description |
|--------|-------------|
| `raw` | Data as-is from the NHL API |
| `staging` | Cleaned and typed data (regular season + playoffs separated) |
| `analytics` | Aggregated stats ready for analysis and ML |

## Getting Started

**Install dependencies:**
```bash
make install
```

**Run the full pipeline for a season:**
```bash
make pipeline SEASON=20232024
```

This fetches all teams for the season, extracts and loads schedule data, runs all transforms, and prints a summary of regular season and playoff games loaded. Already-loaded seasons are skipped automatically.

## Available Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make pipeline SEASON=X` | Run full pipeline for a season (extract + load + transform) |
| `make extract TEAM=X SEASON=X` | Extract only (single team) |
| `make load TEAM=X SEASON=X` | Load only (single team) |
| `make format` | Format code with ruff |
| `make lint` | Lint code with ruff |
| `make test` | Run tests |
| `make clean-db` | Delete the local DuckDB database |

## Season Format

Seasons follow the NHL format: `YYYYYYYY` (e.g., `20232024` for the 2023-24 season).

## Tech Stack

- **Python** — data extraction and pipeline orchestration
- **DuckDB** — local analytical database
- **NHL API** — public API at `https://api-web.nhle.com/v1`
