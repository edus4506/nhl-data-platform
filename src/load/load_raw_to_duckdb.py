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

	return {
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


def create_raw_games_table(connection: duckdb.DuckDBPyConnection) -> None:
	connection.execute("""
        CREATE SCHEMA IF NOT EXISTS raw;

        CREATE TABLE IF NOT EXISTS raw.games (
            game_id BIGINT PRIMARY KEY,
            season INTEGER,
            game_type INTEGER,
            game_date VARCHAR,
            start_time_utc VARCHAR,
            game_state VARCHAR,
            game_schedule_state VARCHAR,
            venue_name VARCHAR,
            neutral_site BOOLEAN,
            home_team_id INTEGER,
            home_team_abbrev VARCHAR,
            home_score INTEGER,
            away_team_id INTEGER,
            away_team_abbrev VARCHAR,
            away_score INTEGER,
            game_center_link VARCHAR
        );
    """)


def insert_raw_game(connection: duckdb.DuckDBPyConnection, game: dict) -> None:
	connection.execute(
		"""
        DELETE FROM raw.games
        WHERE game_id = ?
        """,
		[game["game_id"]],
	)

	connection.execute(
		"""
        INSERT INTO raw.games (
            game_id,
            season,
            game_type,
            game_date,
            start_time_utc,
            game_state,
            game_schedule_state,
            venue_name,
            neutral_site,
            home_team_id,
            home_team_abbrev,
            home_score,
            away_team_id,
            away_team_abbrev,
            away_score,
            game_center_link
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
		[
			game["game_id"],
			game["season"],
			game["game_type"],
			game["game_date"],
			game["start_time_utc"],
			game["game_state"],
			game["game_schedule_state"],
			game["venue_name"],
			game["neutral_site"],
			game["home_team_id"],
			game["home_team_abbrev"],
			game["home_score"],
			game["away_team_id"],
			game["away_team_abbrev"],
			game["away_score"],
			game["game_center_link"],
		],
	)


def insert_raw_games(connection: duckdb.DuckDBPyConnection, games: list[dict]) -> None:
	for game in games:
		insert_raw_game(connection, game)
