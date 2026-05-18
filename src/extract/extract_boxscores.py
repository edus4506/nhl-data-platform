import json
import requests
import argparse
import duckdb
from pathlib import Path

BASE_URL = "https://api-web.nhle.com/v1"
WAREHOUSE_PATH = Path("warehouse") / "nhl.duckdb"

def fetch_boxscores(game_id: str) -> dict:
    url = f"{BASE_URL}/gamecenter/{game_id}/boxscore"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def save_raw_boxscore(data: dict, season: str, game_id: int) -> Path:
    output_dir = Path("data")/"raw"/f"season={season}"/"boxscores"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir/f"{game_id}.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
    return output_path


def get_game_ids_for_season(season: str) -> list[int]:
    connection = duckdb.connect(str(WAREHOUSE_PATH))
    result = connection.execute(
        "SELECT game_id FROM staging.regular_season_games WHERE season = ?",
        [season]
    ).fetchall()
    connection.close()
    return [row[0] for row in result]


def extract_boxscores_for_season(season: str) -> None:
    game_ids = get_game_ids_for_season(season)
    print(f"Extracting boxscores for season {season}: {len(game_ids)} games")

    skipped = 0
    extracted = 0

    for game_id in game_ids:
        output_path = Path("data")/"raw"/f"season={season}"/"boxscores"/f"{game_id}.json"

        if output_path.exists():
            skipped += 1
            continue

        data = fetch_boxscores(game_id)
        save_raw_boxscore(data, season, game_id)
        extracted += 1

    print(f"Done - {extracted} extracted {skipped} skipped")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract NHL boxscores for data.")
    parser.add_argument("--season", required=True)
    args = parser.parse_args()
    extract_boxscores_for_season(args.season)


if __name__ == "__main__":
    main()
