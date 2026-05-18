import duckdb
import pytest

from src.transform.transform_games import create_staging_schema, transform_regular_season, transform_playoffs


@pytest.fixture
def connection():
    conn = duckdb.connect(":memory:")
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    conn.execute("""
        CREATE TABLE raw.games (
            game_id BIGINT PRIMARY KEY,
            season INTEGER,
            game_type INTEGER,
            game_date VARCHAR,
            game_state VARCHAR,
            venue_name VARCHAR,
            home_team_abbrev VARCHAR,
            home_score INTEGER,
            away_team_abbrev VARCHAR,
            away_score INTEGER
        )
    """)
    conn.execute("""
        INSERT INTO raw.games VALUES
        (1, 20232024, 2, '2023-10-11', 'OFF', 'TD Garden',  'BOS', 3, 'CHI', 1),
        (2, 20232024, 2, '2023-10-14', 'OFF', 'TD Garden',  'BOS', 2, 'NSH', 4),
        (3, 20232024, 3, '2024-04-20', 'OFF', 'TD Garden',  'BOS', 5, 'TOR', 2),
        (4, 20232024, 1, '2023-09-24', 'OFF', 'TD Garden',  'BOS', 3, 'NYR', 0),
        (5, 20232024, 2, '2023-10-19', 'LIVE', 'SAP Center', 'SJS', 1, 'BOS', 3)
    """)
    create_staging_schema(conn)
    yield conn
    conn.close()


def test_regular_season_excludes_preseason(connection):
    transform_regular_season(connection)
    result = connection.execute("SELECT game_id FROM staging.regular_season_games").fetchall()
    ids = [r[0] for r in result]
    assert 4 not in ids


def test_regular_season_excludes_live_games(connection):
    transform_regular_season(connection)
    result = connection.execute("SELECT game_id FROM staging.regular_season_games").fetchall()
    ids = [r[0] for r in result]
    assert 5 not in ids


def test_regular_season_excludes_playoffs(connection):
    transform_regular_season(connection)
    result = connection.execute("SELECT game_id FROM staging.regular_season_games").fetchall()
    ids = [r[0] for r in result]
    assert 3 not in ids


def test_regular_season_winner_home_team(connection):
    transform_regular_season(connection)
    result = connection.execute(
        "SELECT winner FROM staging.regular_season_games WHERE game_id = 1"
    ).fetchone()
    assert result[0] == "BOS"


def test_regular_season_winner_away_team(connection):
    transform_regular_season(connection)
    result = connection.execute(
        "SELECT winner FROM staging.regular_season_games WHERE game_id = 2"
    ).fetchone()
    assert result[0] == "NSH"


def test_playoffs_only_contains_game_type_3(connection):
    transform_playoffs(connection)
    result = connection.execute("SELECT game_id FROM staging.playoff_games").fetchall()
    ids = [r[0] for r in result]
    assert ids == [3]
