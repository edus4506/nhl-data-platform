from pathlib import Path

import duckdb

WAREHOUSE_PATH = Path("warehouse") / "nhl.duckdb"


def create_pipeline_runs_table(connection: duckdb.DuckDBPyConnection) -> None:
	connection.execute("CREATE SCHEMA IF NOT EXISTS raw;")
	connection.execute("""
        CREATE TABLE IF NOT EXISTS raw.pipeline_runs (
            team VARCHAR,
            season VARCHAR,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (team, season)
        )
    """)


def is_already_loaded(connection: duckdb.DuckDBPyConnection, team: str, season: str) -> bool:
	result = connection.execute(
		"SELECT COUNT(*) FROM raw.pipeline_runs WHERE team = ? AND season = ?",
		[team, season],
	).fetchone()
	return result[0] > 0


def register_pipeline_run(connection: duckdb.DuckDBPyConnection, team: str, season: str) -> None:
	connection.execute(
		"INSERT INTO raw.pipeline_runs (team, season) VALUES (?, ?)",
		[team, season],
	)
