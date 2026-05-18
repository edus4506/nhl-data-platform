import argparse
import subprocess
import sys
from pathlib import Path

import duckdb

from src.extract.extract_teams import fetch_teams_for_season
from src.load.pipeline_runs import (
	create_pipeline_runs_table,
	is_already_loaded,
	register_pipeline_run,
)
from src.transform.transform_games import create_staging_schema, transform_regular_season, transform_playoffs
from src.transform.build_team_stats import create_analytics_schema, build_team_stats

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
			print(f"  Extracting {team}...")
			run_extract(team=team, season=args.season)

			connection.close()
			run_load(team=team, season=args.season)
			connection = duckdb.connect(str(WAREHOUSE_PATH))

		register_pipeline_run(connection, args.season)

	print("Running transforms...")
	create_staging_schema(connection)
	transform_regular_season(connection)
	transform_playoffs(connection)
	create_analytics_schema(connection)
	build_team_stats(connection)

	regular = connection.execute(
		"SELECT COUNT(*) FROM staging.regular_season_games WHERE season = ?",
								 [args.season]
	).fetchone()[0]

	playoffs = connection.execute(
		"SELECT COUNT(*) FROM staging.playoff_games WHERE season = ?",
		[args.season]
	).fetchone()[0]

	print(f"Inserted {regular} regular season games into analytics.team_stats")
	print(f"Inserted {playoffs} playoff games into analytics.team_stats")

	connection.close()

	print("Pipeline finished successfully")


if __name__ == "__main__":
	main()
