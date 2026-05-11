import argparse
import subprocess
import sys
from pathlib import Path

TEAMS_FILE = Path("config") / "nhl_teams.txt"


def read_teams(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as file:
        return [
            line.strip().upper()
            for line in file
            if line.strip()
        ]


def get_target_teams(team: str) -> list[str]:
    team = team.upper()

    if team == "ALL":
        return read_teams(TEAMS_FILE)
    
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

    teams = get_target_teams(args.team)

    requested_team = args.team.upper()

    print(f"Season: {args.season}")

    if requested_team == "ALL":
        print(f"Teams to process: All {len(teams)} teams")
    else:
        print(f"Team to process: {teams[0]}")
    
    for team in teams:
        print(f"Processing {team} {args.season}")

        run_extract(team=team, season=args.season)
        run_load(team=team, season=args.season)
    
    print("Pipeline finished successfully")


if __name__ == "__main__":
    main()