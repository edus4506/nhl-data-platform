import duckdb
import pytest

from src.load.load_boxscores_to_duckdb import create_boxscore_tables
from src.transform.build_game_logs import build_game_logs


@pytest.fixture
def connection():
	conn = duckdb.connect(":memory:")
	create_boxscore_tables(conn)
	conn.execute("""
        INSERT INTO raw.boxscore_team VALUES
        (1, 20232024, 2, '2023-10-11', 1, 'BOS', 'CHI', true, 3, 30, 'REG'),
        (1, 20232024, 2, '2023-10-11', 2, 'CHI', 'BOS', false, 1, 20, 'REG'),
        (2, 20232024, 2, '2023-10-14', 1, 'BOS', 'NSH', true, 2, 28, 'SO'),
        (2, 20232024, 2, '2023-10-14', 3, 'NSH', 'BOS', false, 3, 25, 'SO'),
        (3, 20232024, 3, '2024-04-20', 1, 'BOS', 'TOR', true, 1, 22, 'REG'),
        (3, 20232024, 3, '2024-04-20', 4, 'TOR', 'BOS', false, 2, 30, 'REG')
    """)
	conn.execute("""
        INSERT INTO raw.boxscore_skaters (game_id, team_abbrev, player_id, player_name, goals)
        VALUES (1, 'BOS', 10, 'A. Skater', 2), (1, 'CHI', 20, 'B. Skater', 1)
    """)
	conn.execute("""
        INSERT INTO raw.boxscore_goalies (game_id, team_abbrev, player_id, player_name, saves)
        VALUES (1, 'BOS', 30, 'C. Goalie', 19)
    """)
	build_game_logs(conn)
	yield conn
	conn.close()


def test_team_game_log_has_two_rows_per_game(connection):
	assert connection.execute("SELECT COUNT(*) FROM analytics.team_game_log").fetchone()[0] == 6


def test_results_distinguish_overtime_losses(connection):
	rows = dict(
		connection.execute(
			"SELECT team, result FROM analytics.team_game_log WHERE game_id = 2"
		).fetchall()
	)
	assert rows == {"BOS": "OTL", "NSH": "W"}


def test_points_follow_nhl_rules(connection):
	rows = dict(
		connection.execute(
			"SELECT team, points FROM analytics.team_game_log WHERE game_id = 1"
		).fetchall()
	)
	assert rows == {"BOS": 2, "CHI": 0}


def test_goals_against_come_from_opponent(connection):
	row = connection.execute(
		"SELECT goals_for, goals_against, sog_against FROM analytics.team_game_log "
		"WHERE game_id = 1 AND team = 'BOS'"
	).fetchone()
	assert row == (3, 1, 20)


def test_skater_and_goalie_logs_link_to_team_game(connection):
	skater = connection.execute(
		"SELECT opponent, is_home, game_date FROM analytics.skater_game_log WHERE player_id = 10"
	).fetchone()
	assert skater[0] == "CHI" and skater[1] is True
	assert str(skater[2]) == "2023-10-11"
	assert connection.execute("SELECT COUNT(*) FROM analytics.goalie_game_log").fetchone()[0] == 1


def test_team_season_stats_only_counts_regular_season(connection):
	row = connection.execute(
		"SELECT games_played, wins, regulation_losses, overtime_losses, points "
		"FROM analytics.team_season_stats WHERE team = 'BOS'"
	).fetchone()
	assert row == (2, 1, 0, 1, 3)
