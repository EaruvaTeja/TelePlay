"""Read-only schema drift checks against temporary SQLite databases."""

import asyncio

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from app import models
from scripts import verify_schema
from scripts.verify_schema import compare_schema


@pytest.fixture
def schema_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'schema.db'}")
    models.Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def _drift(engine):
    with engine.connect() as connection:
        return compare_schema(connection)


def test_schema_matches_metadata_on_temp_sqlite(schema_engine):
    assert _drift(schema_engine) == []


def test_live_inspection_uses_async_engine_with_temp_sqlite(monkeypatch, tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'async-schema.db'}")

    async def create_schema():
        async with engine.begin() as connection:
            await connection.run_sync(models.Base.metadata.create_all)

    asyncio.run(create_schema())
    monkeypatch.setattr(verify_schema, "engine", engine)
    try:
        assert asyncio.run(verify_schema._inspect_live_schema()) == []
    finally:
        asyncio.run(engine.dispose())


def test_main_reports_schema_drift_and_returns_nonzero(monkeypatch, capsys):
    async def drift_report():
        return ["Missing table 'family_members'"]

    monkeypatch.setattr(verify_schema, "_inspect_live_schema", drift_report)

    assert verify_schema.main() == 1
    output = capsys.readouterr().out
    assert "Schema drift detected (1 item(s))" in output
    assert "Missing table 'family_members'" in output


def test_schema_verifier_reports_missing_table(schema_engine):
    with schema_engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE family_members")

    assert any("Missing table 'family_members'" in item for item in _drift(schema_engine))


def test_schema_verifier_reports_wrong_column_type(schema_engine):
    with schema_engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE users RENAME COLUMN telegram_id TO old_telegram_id")
        connection.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN telegram_id TEXT NOT NULL DEFAULT ''"
        )

    assert any(
        "Column users.telegram_id type mismatch: expected BIGINT, found TEXT" in item
        for item in _drift(schema_engine)
    )


def test_schema_verifier_reports_missing_unique_index(schema_engine):
    with schema_engine.begin() as connection:
        connection.exec_driver_sql("DROP INDEX uq_files_channel_message_id")

    assert any(
        "uq_files_channel_message_id" in item and "missing index" in item
        for item in _drift(schema_engine)
    )
