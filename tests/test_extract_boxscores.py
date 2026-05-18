import json
from pathlib import Path
from unittest.mock import patch

from src.extract.extract_boxscores import extract_boxscores_for_season, save_raw_boxscore


def test_save_raw_boxscore_creates_file(tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)
	data = {"id": 123, "season": 20232024}
	path = save_raw_boxscore(data, "20232024", 123)
	assert path.exists()


def test_save_raw_boxscore_content_is_correct(tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)
	data = {"id": 123, "season": 20232024}
	path = save_raw_boxscore(data, "20232024", 123)
	with path.open() as f:
		saved = json.load(f)
	assert saved == data


def test_save_raw_boxscore_path_is_correct(tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)
	data = {"id": 456}
	path = save_raw_boxscore(data, "20232024", 456)
	assert path == Path("data") / "raw" / "season=20232024" / "boxscores" / "456.json"


def test_extract_skips_existing_files(tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)

	boxscores_dir = tmp_path / "data" / "raw" / "season=20232024" / "boxscores"
	boxscores_dir.mkdir(parents=True)
	(boxscores_dir / "123.json").write_text("{}")

	with patch("src.extract.extract_boxscores.get_game_ids_for_season", return_value=[123]):
		with patch("src.extract.extract_boxscores.fetch_boxscores") as mock_fetch:
			extract_boxscores_for_season("20232024")
			mock_fetch.assert_not_called()


def test_extract_fetches_missing_files(tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)

	with patch("src.extract.extract_boxscores.get_game_ids_for_season", return_value=[999]):
		with patch(
			"src.extract.extract_boxscores.fetch_boxscores",
			return_value={"id": 999},
		) as mock_fetch:
			extract_boxscores_for_season("20232024")
			mock_fetch.assert_called_once_with(999)
