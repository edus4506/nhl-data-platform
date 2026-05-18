from pathlib import Path

import duckdb

WAREHOUSE_PATH = Path("warehouse") / "nhl.duckdb"


def create_analytics_schema(connection: duckdb.DuckDBPyConnection) -> None:
	connection.execute("CREATE SCHEMA IF NOT EXISTS analytics;")


def build_team_stats(connection: duckdb.DuckDBPyConnection) -> None:
	connection.execute("""
        CREATE OR REPLACE TABLE analytics.team_stats AS
        SELECT season, team, COUNT(*) AS games_played, 
            SUM(CASE WHEN team = winner THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN team != winner THEN 1 ELSE 0 END) AS losses,
            SUM(goals_for) AS goals_scored,
            SUM(goals_against) AS goals_against
        FROM (
            SELECT season, home_team_abbrev AS team, home_score AS goals_for,
                away_score AS goals_against, winner
            FROM staging.regular_season_games
            
            UNION ALL
            
            SELECT season, away_team_abbrev AS team, away_score AS goals_for,
                home_score AS goals_against, winner
            FROM staging.regular_season_games
        )
        GROUP BY season, team
        ORDER BY season, wins DESC;
        """)


def main():
	connection = duckdb.connect(str(WAREHOUSE_PATH))

	create_analytics_schema(connection)

	build_team_stats(connection)

	connection.close()

	print("Analytics tables created successfully")


if __name__ == "__main__":
	main()
