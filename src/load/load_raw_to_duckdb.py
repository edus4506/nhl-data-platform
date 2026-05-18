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

	return {
		"game_id": game["id"],
		"season": game["season"],
		"game_type": game["gameType"],
		"game_date": game["gameDate"],
		"start_time_utc": game["startTimeUTC"],
		"game_state": game["gameState"],
		"game_schedule_state": game["gameScheduleState"],
		"venue_name": game.get("venue", {}).get("default"),
		"neutral_site": game["neutralSite"],
		"home_team_id": home_team["id"],
		"home_team_abbrev": home_team["abbrev"],
		"home_score": home_team.get("score"),
		"away_team_id": away_team["id"],
		"away_team_abbrev": away_team["abbrev"],
		"away_score": away_team.get("score"),
		"game_center_link": game.get("gameCenterLink"),
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


def main() -> None:
	parser = argparse.ArgumentParser(description="Load raw NHL schedule data into DuckDB.")

	parser.add_argument("--team", required=True)
	parser.add_argument("--season", required=True)

	args = parser.parse_args()

	path = get_raw_schedule_path(args.team, args.season)
	
	if not path.exists():
		raise FileNotFoundError(
        f"Raw schedule file not found: {path}\n"
        "Run the extract step first for this team and season."
    )

	data = read_raw_schedule(path)

	games = [parse_game(game) for game in data["games"]]

	WAREHOUSE_PATH.parent.mkdir(parents=True, exist_ok=True)

	connection = duckdb.connect(str(WAREHOUSE_PATH))

	create_raw_games_table(connection)

	insert_raw_games(connection, games)

	connection.close()

	print(f"Inserted {len(games)} games into raw.games")


if __name__ == "__main__":
	main()
