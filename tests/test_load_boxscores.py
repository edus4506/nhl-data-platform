import json

import duckdb
import pytest

from src.load.load_boxscores_to_duckdb import (
	create_boxscore_tables,
	load_boxscores_for_season,
	parse_boxscore,
	toi_to_seconds,
)

BOXSCORE = {
	"id": 2023020001,
	"season": 20232024,
	"gameType": 2,
	"gameDate": "2023-10-10",
	"gameOutcome": {"lastPeriodType": "OT"},
	"homeTeam": {"id": 1, "abbrev": "NJD", "score": 3, "sog": 30},
	"awayTeam": {"id": 2, "abbrev": "TBL", "score": 2, "sog": 25},
	"playerByGameStats": {
		"homeTeam": {
			"forwards": [
				{
					"playerId": 10,
					"name": {"default": "A. Forward"},
					"position": "C",
					"goals": 1,
					"toi": "14:01",
				}
			],
			"defense": [{"playerId": 11, "name": {"default": "B. Defense"}, "position": "D"}],
			"goalies": [
				{
					"playerId": 12,
					"name": {"default": "C. Goalie"},
					"toi": "60:00",
					"starter": True,
					"decision": "W",
					"saves": 23,
					"shotsAgainst": 25,
					"goalsAgainst": 2,
				}
			],
		},
		"awayTeam": {"forwards": [], "defense": [], "goalies": []},
	},
}


@pytest.fixture
def connection():
	conn = duckdb.connect(":memory:")
	create_boxscore_tables(conn)
	yield conn
	conn.close()


def test_toi_to_seconds():
	assert toi_to_seconds("14:01") == 841
	assert toi_to_seconds("00:00") == 0
	assert toi_to_seconds(None) is None


def test_parse_boxscore_team_rows():
	teams, _, _ = parse_boxscore(BOXSCORE)
	assert len(teams) == 2
	home = next(t for t in teams if t["is_home"])
	assert home["team_abbrev"] == "NJD"
	assert home["opponent_abbrev"] == "TBL"
	assert home["goals"] == 3
	assert home["last_period_type"] == "OT"


def test_parse_boxscore_players_and_missing_fields():
	_, skaters, goalies = parse_boxscore(BOXSCORE)
	assert {s["player_id"] for s in skaters} == {10, 11}
	forward = next(s for s in skaters if s["player_id"] == 10)
	assert forward["toi_seconds"] == 841
	defense = next(s for s in skaters if s["player_id"] == 11)
	assert defense["shifts"] is None
	assert goalies[0]["saves"] == 23


def test_parse_boxscore_without_player_stats():
	data = {k: v for k, v in BOXSCORE.items() if k != "playerByGameStats"}
	teams, skaters, goalies = parse_boxscore(data)
	assert len(teams) == 2
	assert skaters == [] and goalies == []


def test_load_boxscores_is_idempotent(connection, tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)
	directory = tmp_path / "data" / "raw" / "season=20232024" / "boxscores"
	directory.mkdir(parents=True)
	(directory / "2023020001.json").write_text(json.dumps(BOXSCORE))

	assert load_boxscores_for_season(connection, "20232024") == 1
	assert load_boxscores_for_season(connection, "20232024") == 1

	assert connection.execute("SELECT COUNT(*) FROM raw.boxscore_team").fetchone()[0] == 2
	assert connection.execute("SELECT COUNT(*) FROM raw.boxscore_skaters").fetchone()[0] == 2
	assert connection.execute("SELECT COUNT(*) FROM raw.boxscore_goalies").fetchone()[0] == 1


def test_load_boxscores_without_directory_returns_zero(connection, tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)
	assert load_boxscores_for_season(connection, "20232024") == 0
