import sys
from pathlib import Path

import duckdb

WAREHOUSE_PATH = Path("warehouse") / "nhl.duckdb"

FIRST_SEASON = 20102011
LAST_SEASON = 20252026

CHECKS = {
	"seasons in raw.games": (
		"SELECT COUNT(DISTINCT season) FROM raw.games WHERE season BETWEEN ? AND ?",
		16,
	),
	"finished games without boxscore": (
		"""
        SELECT COUNT(*) FROM raw.games g
        WHERE g.game_state = 'OFF' AND g.game_type IN (2, 3)
        AND g.game_id NOT IN (SELECT game_id FROM raw.boxscore_team)
        AND g.season BETWEEN ? AND ?
        """,
		0,
	),
	"boxscore teams per game != 2": (
		"""
        SELECT COUNT(*) FROM (
            SELECT game_id FROM raw.boxscore_team GROUP BY game_id HAVING COUNT(*) != 2
        )
        """,
		0,
	),
	"boxscore goals != schedule score": (
		"""
        SELECT COUNT(*) FROM raw.boxscore_team b
        JOIN raw.games g ON g.game_id = b.game_id
        WHERE (b.is_home AND b.goals != g.home_score)
           OR (NOT b.is_home AND b.goals != g.away_score)
        """,
		0,
	),
	"duplicate skater rows": (
		"""
        SELECT COUNT(*) FROM (
            SELECT game_id, player_id FROM analytics.skater_game_log
            GROUP BY game_id, player_id HAVING COUNT(*) > 1
        )
        """,
		0,
	),
	"games without goalie rows": (
		"""
        SELECT COUNT(*) FROM raw.boxscore_team
        WHERE game_id NOT IN (SELECT game_id FROM raw.boxscore_goalies)
        """,
		0,
	),
	"team_game_log rows != 2 x boxscore games": (
		"""
        SELECT ABS(
            (SELECT COUNT(*) FROM analytics.team_game_log)
            - 2 * (SELECT COUNT(DISTINCT game_id) FROM raw.boxscore_team)
        )
        """,
		0,
	),
}


def run_checks(connection: duckdb.DuckDBPyConnection) -> bool:
	all_ok = True
	for name, (query, expected) in CHECKS.items():
		params = [FIRST_SEASON, LAST_SEASON] if "?" in query else []
		actual = connection.execute(query, params).fetchone()[0]
		status = "OK  " if actual == expected else "FAIL"
		if actual != expected:
			all_ok = False
		print(f"[{status}] {name}: {actual} (expected {expected})")
	return all_ok


def main() -> None:
	connection = duckdb.connect(str(WAREHOUSE_PATH), read_only=True)
	ok = run_checks(connection)
	connection.close()
	sys.exit(0 if ok else 1)


if __name__ == "__main__":
	main()
