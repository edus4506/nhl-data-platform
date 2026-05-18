import duckdb
from pathlib import Path

WAREHOUSE_PATH = Path("warehouse") / "nhl.duckdb"

def create_staging_schema(connection):
    connection.execute("CREATE SCHEMA IF NOT EXISTS staging;")


def transform_regular_season(connection):
    connection.execute("""
        CREATE OR REPLACE TABLE staging.regular_season_games AS
        SELECT game_id, season, game_date::DATE AS game_date, venue_name,
            home_team_abbrev, home_score, away_team_abbrev, away_score,
            CASE WHEN home_score > away_score THEN home_team_abbrev
                 WHEN away_score > home_score THEN away_team_abbrev
            END AS winner
        FROM raw.games
        WHERE game_type = 2
        AND game_state = 'OFF';
    """)


def transform_playoffs(connection):
	connection.execute("""
        CREATE OR REPLACE TABLE staging.playoff_games AS
        SELECT game_id, season, game_date::DATE AS game_date, venue_name,
            home_team_abbrev, home_score, away_team_abbrev, away_score,
            CASE WHEN home_score > away_score THEN home_team_abbrev
                 WHEN away_score > home_score THEN away_team_abbrev
            END AS winner
        FROM raw.games
        WHERE game_type = 3
        AND game_state = 'OFF';
    """)

def main():
    connection = duckdb.connect(str(WAREHOUSE_PATH))
    
    create_staging_schema(connection)
    
    transform_regular_season(connection)

    transform_playoffs(connection)

    connection.close()

    print("Staging tables created successfully")


if __name__ == "__main__":
    main()