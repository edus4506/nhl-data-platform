import argparse
import subprocess
import sys
from pathlib import Path

import duckdb

from src.extract.extract_boxscores import extract_boxscores_for_season
from src.extract.extract_teams import fetch_teams_for_season
from src.load.load_boxscores_to_duckdb import load_boxscores_for_season
from src.load.pipeline_runs import (
	create_pipeline_runs_table,
	is_already_loaded,
	register_pipeline_run,
)
from src.transform.build_game_logs import build_game_logs
from src.transform.build_team_stats import build_team_stats, create_analytics_schema
from src.transform.transform_games import (
	create_staging_schema,
	transform_playoffs,
	transform_regular_season,
)

WAREHOUSE_PATH = Path("warehouse") / "nhl.duckdb"


def run_extract(team: str, season: str) -> None:
	subprocess.run(
		[
			sys.executable,
			"src/extract/extract_schedule.py",
			"--team",
			team,
			"--season",
			season,
		],
		check=True,
	)


def run_load(team: str, season: str) -> None:
	subprocess.run(
		[
			sys.executable,
			"src/load/load_raw_to_duckdb.py",
			"--team",
			team,
			"--season",
			season,
		],
		check=True,
	)


def main() -> None:
	parser = argparse.ArgumentParser(description="Run NHL data pipeline.")
	parser.add_argument("--season", required=True)

	args = parser.parse_args()

	connection = duckdb.connect(str(WAREHOUSE_PATH))
	create_pipeline_runs_table(connection)

	if is_already_loaded(connection, args.season):
		print(f"Season {args.season} already loaded — skipping extract and load")
	else:
		teams = fetch_teams_for_season(args.season)
		print(f"Season: {args.season} — {len(teams)} teams")

		for team in teams:
			print(f"  Extracting {team} {args.season}...")
			run_extract(team=team, season=args.season)

			connection.close()
			run_load(team=team, season=args.season)
			connection = duckdb.connect(str(WAREHOUSE_PATH))

		loaded_games = connection.execute(
			"SELECT COUNT(*) FROM raw.games WHERE season = ?", [args.season]
		).fetchone()[0]
		if loaded_games == 0:
			raise RuntimeError(f"No games loaded for season {args.season}; not marking as loaded")

		register_pipeline_run(connection, args.season)

	print("Running staging transforms...")
	create_staging_schema(connection)
	transform_regular_season(connection)
	transform_playoffs(connection)
	create_analytics_schema(connection)
	build_team_stats(connection)

	connection.close()
	extract_boxscores_for_season(args.season)
	connection = duckdb.connect(str(WAREHOUSE_PATH))

	load_boxscores_for_season(connection, args.season)
	build_game_logs(connection)

	regular = connection.execute(
		"SELECT COUNT(*) FROM staging.regular_season_games WHERE season = ?",
		[args.season],
	).fetchone()[0]

	playoffs = connection.execute(
		"SELECT COUNT(*) FROM staging.playoff_games WHERE season = ?", [args.season]
	).fetchone()[0]

	print(f"Season {args.season}: {regular} regular season games in staging")
	print(f"Season {args.season}: {playoffs} playoff games in staging")

	connection.close()

	print("Pipeline finished successfully")


if __name__ == "__main__":
	main()
