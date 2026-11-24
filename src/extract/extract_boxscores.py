import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import duckdb
import requests

BASE_URL = "https://api-web.nhle.com/v1"
WAREHOUSE_PATH = Path("warehouse") / "nhl.duckdb"


MAX_RETRIES = 6
MAX_WORKERS = 2


def fetch_boxscores(game_id: str) -> dict:
	url = f"{BASE_URL}/gamecenter/{game_id}/boxscore"
	for attempt in range(1, MAX_RETRIES + 1):
		try:
			response = requests.get(url, timeout=30)
			response.raise_for_status()
			return response.json()
		except requests.RequestException:
			if attempt == MAX_RETRIES:
				raise
			time.sleep(5 * attempt)


def save_raw_boxscore(data: dict, season: str, game_id: int) -> Path:
	output_dir = Path("data") / "raw" / f"season={season}" / "boxscores"
	output_dir.mkdir(parents=True, exist_ok=True)
	output_path = output_dir / f"{game_id}.json"
	temp_path = output_path.with_suffix(".json.tmp")
	with temp_path.open("w", encoding="utf-8") as file:
		json.dump(data, file, indent=2, ensure_ascii=False)
	temp_path.replace(output_path)
	return output_path


def get_game_ids_for_season(season: str) -> list[int]:
	connection = duckdb.connect(str(WAREHOUSE_PATH))
	result = connection.execute(
		"SELECT game_id FROM raw.games "
		"WHERE season = ? AND game_state = 'OFF' AND game_type IN (2, 3) ORDER BY game_id",
		[season],
	).fetchall()
	connection.close()
	return [row[0] for row in result]


def extract_one_boxscore(season: str, game_id: int) -> None:
	data = fetch_boxscores(game_id)
	save_raw_boxscore(data, season, game_id)


def extract_boxscores_for_season(season: str) -> None:
	game_ids = get_game_ids_for_season(season)
	print(f"Extracting boxscores for season {season}: {len(game_ids)} games")

	boxscores_dir = Path("data") / "raw" / f"season={season}" / "boxscores"
	missing = [game_id for game_id in game_ids if not (boxscores_dir / f"{game_id}.json").exists()]
	skipped = len(game_ids) - len(missing)

	with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
		list(executor.map(lambda game_id: extract_one_boxscore(season, game_id), missing))

	print(f"Done - {len(missing)} extracted {skipped} skipped")


def main() -> None:
	parser = argparse.ArgumentParser(description="Extract NHL boxscores for data.")
	parser.add_argument("--season", required=True)
	args = parser.parse_args()
	extract_boxscores_for_season(args.season)


if __name__ == "__main__":
	main()
