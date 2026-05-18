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

WAREHOUSE_PATH = Path("warehouse") / "nhl.duckdb"


def get_target_teams(team: str, season: str) -> list[str]:
	team = team.upper()

	if team == "ALL":
		return fetch_teams_for_season(season)

	return [team]


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
	parser.add_argument("--team", required=True)
	parser.add_argument("--season", required=True)

	args = parser.parse_args()

	teams = get_target_teams(args.team, args.season)

	requested_team = args.team.upper()

	print(f"Season: {args.season}")

	if requested_team == "ALL":
		print(f"Teams to process: All {len(teams)} teams")
	else:
		print(f"Team to process: {teams[0]}")

	connection = duckdb.connect(str(WAREHOUSE_PATH))
	create_pipeline_runs_table(connection)

	for team in teams:
		if is_already_loaded(connection, team, args.season):
			print(f"Skipping {team} {args.season} (already loaded)")
			continue

		print(f"Processing {team} {args.season}")
		run_extract(team=team, season=args.season)

		connection.close()
		run_load(team=team, season=args.season)
		connection = duckdb.connect(str(WAREHOUSE_PATH))

		register_pipeline_run(connection, team, args.season)

	print("Pipeline finished successfully")


if __name__ == "__main__":
	main()
