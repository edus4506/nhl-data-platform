import duckdb
import pytest

from src.transform.build_team_stats import create_analytics_schema, build_team_stats


@pytest.fixture
def connection():
    conn = duckdb.connect(":memory:")
    conn.execute("CREATE SCHEMA IF NOT EXISTS staging;")
    conn.execute("""
        CREATE TABLE staging.regular_season_games (
            game_id BIGINT PRIMARY KEY,
            season INTEGER,
            game_date DATE,
            venue_name VARCHAR,
            home_team_abbrev VARCHAR,
            home_score INTEGER,
            away_team_abbrev VARCHAR,
            away_score INTEGER,
            winner VARCHAR
        )
    """)
    conn.execute("""
        INSERT INTO staging.regular_season_games VALUES
        (1, 20232024, '2023-10-11', 'TD Garden', 'BOS', 3, 'CHI', 1, 'BOS'),
        (2, 20232024, '2023-10-14', 'TD Garden', 'BOS', 2, 'NSH', 4, 'NSH'),
        (3, 20232024, '2023-10-19', 'TD Garden', 'BOS', 5, 'TOR', 2, 'BOS')
    """)
    create_analytics_schema(conn)
    yield conn
    conn.close()


def test_games_played_counts_both_teams(connection):
    build_team_stats(connection)
    result = connection.execute(
        "SELECT games_played FROM analytics.team_stats WHERE team = 'BOS' AND season = 20232024"
    ).fetchone()
    assert result[0] == 3


def test_wins_are_counted_correctly(connection):
    build_team_stats(connection)
    result = connection.execute(
        "SELECT wins FROM analytics.team_stats WHERE team = 'BOS' AND season = 20232024"
    ).fetchone()
    assert result[0] == 2


def test_losses_are_counted_correctly(connection):
    build_team_stats(connection)
    result = connection.execute(
        "SELECT losses FROM analytics.team_stats WHERE team = 'BOS' AND season = 20232024"
    ).fetchone()
    assert result[0] == 1


def test_goals_scored_are_correct(connection):
    build_team_stats(connection)
    result = connection.execute(
        "SELECT goals_scored FROM analytics.team_stats WHERE team = 'BOS' AND season = 20232024"
    ).fetchone()
    assert result[0] == 10


def test_goals_against_are_correct(connection):
    build_team_stats(connection)
    result = connection.execute(
        "SELECT goals_against FROM analytics.team_stats WHERE team = 'BOS' AND season = 20232024"
    ).fetchone()
    assert result[0] == 7
