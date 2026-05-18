import duckdb
import pytest

from src.load.pipeline_runs import create_pipeline_runs_table, is_already_loaded, register_pipeline_run


@pytest.fixture
def connection():
    conn = duckdb.connect(":memory:")
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    create_pipeline_runs_table(conn)
    yield conn
    conn.close()


def test_is_already_loaded_returns_false_when_empty(connection):
    assert is_already_loaded(connection, "20232024") is False


def test_is_already_loaded_returns_true_after_register(connection):
    register_pipeline_run(connection, "20232024")
    assert is_already_loaded(connection, "20232024") is True


def test_is_already_loaded_does_not_confuse_seasons(connection):
    register_pipeline_run(connection, "20232024")
    assert is_already_loaded(connection, "20222023") is False


def test_register_pipeline_run_inserts_season(connection):
    register_pipeline_run(connection, "20232024")
    result = connection.execute("SELECT season FROM raw.pipeline_runs").fetchone()
    assert result[0] == "20232024"
