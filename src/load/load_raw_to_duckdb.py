import argparse
import json
from pathlib import Path

import duckdb

WAREHOUSE_PATH = Path("warehouse") / "nhl.duckdb"


def get_raw_schedule_path(team: str, season: str) -> Path:
    team = team.upper()
    return Path("data") / "raw" / f"season={season}" / f"team={team}" / "schedule.json"


def read_raw_schedule(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def parse_game(game: dict) -> dict:
    home_team = game["homeTeam"]
    away_team = game["awayTeam"]

    return{
        "game_id": game["id"],
        "season": game["season"],
        "game_type": game["gameType"],
        "game_date": game["gameDate"],
        "start_time_utc": game["startTimeUTC"],
        "game_state": game["gameState"],
        "game_schedule_state": game["gameScheduleState"],
        "venue_name": game["venue"]["default"],
        "neutral_site": game["neutralSite"],
        "home_team_id": home_team["id"],
        "home_team_abbrev": home_team["abbrev"],
        "home_score": home_team.get("score"),
        "away_team_id": away_team["id"],
        "away_team_abbrev": away_team["abbrev"],
        "away_score": away_team.get("score"),
        "game_center_link": game["gameCenterLink"],       
    }