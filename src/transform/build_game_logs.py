from pathlib import Path

import duckdb

from src.transform.build_team_stats import create_analytics_schema

WAREHOUSE_PATH = Path("warehouse") / "nhl.duckdb"


def build_team_game_log(connection: duckdb.DuckDBPyConnection) -> None:
	connection.execute("""
        CREATE OR REPLACE TABLE analytics.team_game_log AS
        SELECT t.game_id, t.season, t.game_type, t.game_date::DATE AS game_date,
            t.team_abbrev AS team, t.opponent_abbrev AS opponent, t.is_home,
            t.goals AS goals_for, o.goals AS goals_against,
            t.sog AS sog_for, o.sog AS sog_against,
            t.last_period_type,
            CASE WHEN t.goals > o.goals THEN 'W'
                 WHEN t.last_period_type IN ('OT', 'SO') THEN 'OTL'
                 ELSE 'L'
            END AS result,
            CASE WHEN t.goals > o.goals THEN 2
                 WHEN t.last_period_type IN ('OT', 'SO') THEN 1
                 ELSE 0
            END AS points
        FROM raw.boxscore_team t
        JOIN raw.boxscore_team o
            ON o.game_id = t.game_id AND o.team_abbrev = t.opponent_abbrev
        ORDER BY t.game_date, t.game_id, t.is_home DESC;
    """)


def build_skater_game_log(connection: duckdb.DuckDBPyConnection) -> None:
	connection.execute("""
        CREATE OR REPLACE TABLE analytics.skater_game_log AS
        SELECT g.game_id, g.season, g.game_type, g.game_date, g.team, g.opponent, g.is_home,
            s.player_id, s.player_name, s.position, s.goals, s.assists, s.points,
            s.plus_minus, s.pim, s.hits, s.power_play_goals, s.sog, s.faceoff_win_pct,
            s.toi_seconds, s.blocked_shots, s.shifts, s.giveaways, s.takeaways
        FROM raw.boxscore_skaters s
        JOIN analytics.team_game_log g
            ON g.game_id = s.game_id AND g.team = s.team_abbrev
        ORDER BY g.game_date, g.game_id, s.player_id;
    """)


def build_goalie_game_log(connection: duckdb.DuckDBPyConnection) -> None:
	connection.execute("""
        CREATE OR REPLACE TABLE analytics.goalie_game_log AS
        SELECT g.game_id, g.season, g.game_type, g.game_date, g.team, g.opponent, g.is_home,
            s.player_id, s.player_name, s.toi_seconds, s.starter, s.decision,
            s.shots_against, s.saves, s.goals_against, s.save_pct,
            s.even_strength_goals_against, s.power_play_goals_against,
            s.shorthanded_goals_against, s.pim
        FROM raw.boxscore_goalies s
        JOIN analytics.team_game_log g
            ON g.game_id = s.game_id AND g.team = s.team_abbrev
        ORDER BY g.game_date, g.game_id, s.player_id;
    """)


def build_team_season_stats(connection: duckdb.DuckDBPyConnection) -> None:
	connection.execute("""
        CREATE OR REPLACE TABLE analytics.team_season_stats AS
        SELECT season, team, COUNT(*) AS games_played,
            COUNT(*) FILTER (WHERE result = 'W') AS wins,
            COUNT(*) FILTER (WHERE result = 'L') AS regulation_losses,
            COUNT(*) FILTER (WHERE result = 'OTL') AS overtime_losses,
            SUM(points) AS points,
            SUM(goals_for) AS goals_for,
            SUM(goals_against) AS goals_against,
            SUM(sog_for) AS sog_for,
            SUM(sog_against) AS sog_against
        FROM analytics.team_game_log
        WHERE game_type = 2
        GROUP BY season, team
        ORDER BY season, points DESC;
    """)


def build_game_logs(connection: duckdb.DuckDBPyConnection) -> None:
	create_analytics_schema(connection)
	build_team_game_log(connection)
	build_skater_game_log(connection)
	build_goalie_game_log(connection)
	build_team_season_stats(connection)


def main() -> None:
	connection = duckdb.connect(str(WAREHOUSE_PATH))
	build_game_logs(connection)
	connection.close()
	print("Game log tables created successfully")


if __name__ == "__main__":
	main()
