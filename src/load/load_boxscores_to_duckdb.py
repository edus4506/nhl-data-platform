import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

WAREHOUSE_PATH = Path("warehouse") / "nhl.duckdb"

TEAM_COLUMNS = [
	"game_id",
	"season",
	"game_type",
	"game_date",
	"team_id",
	"team_abbrev",
	"opponent_abbrev",
	"is_home",
	"goals",
	"sog",
	"last_period_type",
]

SKATER_COLUMNS = [
	"game_id",
	"team_abbrev",
	"player_id",
	"player_name",
	"position",
	"sweater_number",
	"goals",
	"assists",
	"points",
	"plus_minus",
	"pim",
	"hits",
	"power_play_goals",
	"sog",
	"faceoff_win_pct",
	"toi_seconds",
	"blocked_shots",
	"shifts",
	"giveaways",
	"takeaways",
]

GOALIE_COLUMNS = [
	"game_id",
	"team_abbrev",
	"player_id",
	"player_name",
	"sweater_number",
	"toi_seconds",
	"starter",
	"decision",
	"shots_against",
	"saves",
	"goals_against",
	"save_pct",
	"even_strength_goals_against",
	"power_play_goals_against",
	"shorthanded_goals_against",
	"pim",
]


def toi_to_seconds(toi: str | None) -> int | None:
	if not toi:
		return None
	minutes, seconds = toi.split(":")
	return int(minutes) * 60 + int(seconds)


def parse_boxscore(data: dict) -> tuple[list[dict], list[dict], list[dict]]:
	game_id = data["id"]
	home = data["homeTeam"]
	away = data["awayTeam"]
	last_period_type = data.get("gameOutcome", {}).get("lastPeriodType")

	team_rows = []
	for team, opponent, is_home in ((home, away, True), (away, home, False)):
		team_rows.append(
			{
				"game_id": game_id,
				"season": data["season"],
				"game_type": data["gameType"],
				"game_date": data["gameDate"],
				"team_id": team["id"],
				"team_abbrev": team["abbrev"],
				"opponent_abbrev": opponent["abbrev"],
				"is_home": is_home,
				"goals": team.get("score"),
				"sog": team.get("sog"),
				"last_period_type": last_period_type,
			}
		)

	skater_rows = []
	goalie_rows = []
	player_stats = data.get("playerByGameStats") or {}

	for side, team in (("homeTeam", home), ("awayTeam", away)):
		side_stats = player_stats.get(side) or {}
		abbrev = team["abbrev"]

		for skater in side_stats.get("forwards", []) + side_stats.get("defense", []):
			skater_rows.append(
				{
					"game_id": game_id,
					"team_abbrev": abbrev,
					"player_id": skater["playerId"],
					"player_name": skater.get("name", {}).get("default"),
					"position": skater.get("position"),
					"sweater_number": skater.get("sweaterNumber"),
					"goals": skater.get("goals"),
					"assists": skater.get("assists"),
					"points": skater.get("points"),
					"plus_minus": skater.get("plusMinus"),
					"pim": skater.get("pim"),
					"hits": skater.get("hits"),
					"power_play_goals": skater.get("powerPlayGoals"),
					"sog": skater.get("sog"),
					"faceoff_win_pct": skater.get("faceoffWinningPctg"),
					"toi_seconds": toi_to_seconds(skater.get("toi")),
					"blocked_shots": skater.get("blockedShots"),
					"shifts": skater.get("shifts"),
					"giveaways": skater.get("giveaways"),
					"takeaways": skater.get("takeaways"),
				}
			)

		for goalie in side_stats.get("goalies", []):
			goalie_rows.append(
				{
					"game_id": game_id,
					"team_abbrev": abbrev,
					"player_id": goalie["playerId"],
					"player_name": goalie.get("name", {}).get("default"),
					"sweater_number": goalie.get("sweaterNumber"),
					"toi_seconds": toi_to_seconds(goalie.get("toi")),
					"starter": goalie.get("starter"),
					"decision": goalie.get("decision"),
					"shots_against": goalie.get("shotsAgainst"),
					"saves": goalie.get("saves"),
					"goals_against": goalie.get("goalsAgainst"),
					"save_pct": goalie.get("savePctg"),
					"even_strength_goals_against": goalie.get("evenStrengthGoalsAgainst"),
					"power_play_goals_against": goalie.get("powerPlayGoalsAgainst"),
					"shorthanded_goals_against": goalie.get("shorthandedGoalsAgainst"),
					"pim": goalie.get("pim"),
				}
			)

	return team_rows, skater_rows, goalie_rows


def create_boxscore_tables(connection: duckdb.DuckDBPyConnection) -> None:
	connection.execute("CREATE SCHEMA IF NOT EXISTS raw;")

	connection.execute("""
        CREATE TABLE IF NOT EXISTS raw.boxscore_team (
            game_id BIGINT,
            season INTEGER,
            game_type INTEGER,
            game_date VARCHAR,
            team_id INTEGER,
            team_abbrev VARCHAR,
            opponent_abbrev VARCHAR,
            is_home BOOLEAN,
            goals INTEGER,
            sog INTEGER,
            last_period_type VARCHAR,
            PRIMARY KEY (game_id, team_abbrev)
        );
    """)

	connection.execute("""
        CREATE TABLE IF NOT EXISTS raw.boxscore_skaters (
            game_id BIGINT,
            team_abbrev VARCHAR,
            player_id BIGINT,
            player_name VARCHAR,
            position VARCHAR,
            sweater_number INTEGER,
            goals INTEGER,
            assists INTEGER,
            points INTEGER,
            plus_minus INTEGER,
            pim INTEGER,
            hits INTEGER,
            power_play_goals INTEGER,
            sog INTEGER,
            faceoff_win_pct DOUBLE,
            toi_seconds INTEGER,
            blocked_shots INTEGER,
            shifts INTEGER,
            giveaways INTEGER,
            takeaways INTEGER,
            PRIMARY KEY (game_id, player_id)
        );
    """)

	connection.execute("""
        CREATE TABLE IF NOT EXISTS raw.boxscore_goalies (
            game_id BIGINT,
            team_abbrev VARCHAR,
            player_id BIGINT,
            player_name VARCHAR,
            sweater_number INTEGER,
            toi_seconds INTEGER,
            starter BOOLEAN,
            decision VARCHAR,
            shots_against INTEGER,
            saves INTEGER,
            goals_against INTEGER,
            save_pct DOUBLE,
            even_strength_goals_against INTEGER,
            power_play_goals_against INTEGER,
            shorthanded_goals_against INTEGER,
            pim INTEGER,
            PRIMARY KEY (game_id, player_id)
        );
    """)


def insert_rows(
	connection: duckdb.DuckDBPyConnection, table: str, columns: list[str], rows: list[dict]
) -> None:
	if not rows:
		return
	frame = pd.DataFrame(rows, columns=columns)
	connection.register("batch_frame", frame)
	column_list = ", ".join(columns)
	connection.execute(f"INSERT INTO {table} ({column_list}) SELECT {column_list} FROM batch_frame")
	connection.unregister("batch_frame")


def load_boxscores_for_season(connection: duckdb.DuckDBPyConnection, season: str) -> int:
	boxscores_dir = Path("data") / "raw" / f"season={season}" / "boxscores"
	if not boxscores_dir.exists():
		print(f"No boxscores directory for season {season}")
		return 0

	create_boxscore_tables(connection)

	team_rows: list[dict] = []
	skater_rows: list[dict] = []
	goalie_rows: list[dict] = []
	game_ids: list[int] = []

	for path in sorted(boxscores_dir.glob("*.json")):
		with path.open(encoding="utf-8") as file:
			data = json.load(file)
		teams, skaters, goalies = parse_boxscore(data)
		game_ids.append(data["id"])
		team_rows.extend(teams)
		skater_rows.extend(skaters)
		goalie_rows.extend(goalies)

	if not game_ids:
		return 0

	connection.execute("BEGIN TRANSACTION")
	try:
		for table in ("boxscore_team", "boxscore_skaters", "boxscore_goalies"):
			connection.execute(
				f"DELETE FROM raw.{table} WHERE game_id IN (SELECT UNNEST(?))", [game_ids]
			)
		insert_rows(connection, "raw.boxscore_team", TEAM_COLUMNS, team_rows)
		insert_rows(connection, "raw.boxscore_skaters", SKATER_COLUMNS, skater_rows)
		insert_rows(connection, "raw.boxscore_goalies", GOALIE_COLUMNS, goalie_rows)
		connection.execute("COMMIT")
	except Exception:
		connection.execute("ROLLBACK")
		raise

	print(
		f"Loaded {len(game_ids)} boxscores for {season}: "
		f"{len(skater_rows)} skater rows, {len(goalie_rows)} goalie rows"
	)
	return len(game_ids)


def main() -> None:
	parser = argparse.ArgumentParser(description="Load raw NHL boxscores into DuckDB.")
	parser.add_argument("--season", required=True)
	args = parser.parse_args()

	WAREHOUSE_PATH.parent.mkdir(parents=True, exist_ok=True)
	connection = duckdb.connect(str(WAREHOUSE_PATH))
	load_boxscores_for_season(connection, args.season)
	connection.close()


if __name__ == "__main__":
	main()
