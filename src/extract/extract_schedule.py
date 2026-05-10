import argparse
import json
from pathlib import Path

import requests

BASE_URL = "https://api-web.nhle.com/v1"


def fetch_team_schedule(team: str, season: str) -> dict:
	team = team.upper()
	url = f"{BASE_URL}/club-schedule-season/{team}/{season}"

	response = requests.get(url, timeout=30)
	response.raise_for_status()

	return response.json()


def save_raw_schedule(data: dict, team: str, season: str) -> Path:
	team = team.upper()

	output_dir = Path("data") / "raw" / f"season={season}" / f"team={team}"

	output_dir.mkdir(parents=True, exist_ok=True)

	output_path = output_dir / "schedule.json"

	with output_path.open("w", encoding="utf-8") as file:
		json.dump(data, file, indent=2, ensure_ascii=False)

	return output_path


def main() -> None:
	parser = argparse.ArgumentParser(description="Extract NHL team schedule data.")
	parser.add_argument("--season", required=True, help="Season in YYYYYYYY format, e.g. 20242025")
	parser.add_argument("--team", default="SJS", help="Three-letter NHL team abreviation, e.g. SJS")
	args = parser.parse_args()
	data = fetch_team_schedule(team=args.team, season=args.season)
	output_path = save_raw_schedule(data=data, team=args.team, season=args.season)
	print(f"Saved raw schedule to {output_path}")


if __name__ == "__main__":
	main()