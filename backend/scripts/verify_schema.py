"""Read-only comparison of the live database schema with SQLAlchemy metadata."""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import inspect
from sqlalchemy.engine import Connection
from sqlalchemy.schema import MetaData, UniqueConstraint

from app import models as _models  # noqa: F401
from app.database import Base, engine


def _type_signature(sql_type: Any, dialect: Any) -> str:
    return " ".join(sql_type.compile(dialect=dialect).split()).upper()


def _normalize_default(value: Any) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).strip().split())
    normalized = re.sub(r"::[A-Za-z0-9_ .\"\[\]]+$", "", normalized)
    while normalized.startswith("(") and normalized.endswith(")"):
        normalized = normalized[1:-1].strip()
    if len(normalized) >= 2 and normalized[0] == normalized[-1] == "'":
        normalized = normalized[1:-1].replace("''", "'")
    return normalized.lower()


def _default_matches(column: Any, actual: dict[str, Any], dialect_name: str) -> bool:
    expected_default = column.server_default
    actual_default = actual.get("default")
    if expected_default is not None:
        return _normalize_default(expected_default.arg) == _normalize_default(actual_default)

    if column.primary_key and column.autoincrement is not False:
        if dialect_name == "sqlite":
            return actual_default is None
        if dialect_name == "postgresql":
            return bool(actual.get("identity")) or "nextval(" in str(actual_default).lower()

    return actual_default is None


def compare_schema(connection: Connection, metadata: MetaData = Base.metadata) -> list[str]:
    """Return deterministic schema drift descriptions without changing the database."""
    inspector = inspect(connection)
    actual_tables = set(inspector.get_table_names())
    expected_tables = set(metadata.tables)
    drift: list[str] = []

    for table_name in sorted(expected_tables - actual_tables):
        drift.append(f"Missing table {table_name!r}")
    for table_name in sorted(actual_tables - expected_tables):
        drift.append(f"Unexpected table {table_name!r}")

    for table_name in sorted(expected_tables & actual_tables):
        table = metadata.tables[table_name]
        actual_columns = {column["name"]: column for column in inspector.get_columns(table_name)}
        expected_columns = set(table.columns.keys())

        for column_name in sorted(expected_columns - set(actual_columns)):
            drift.append(f"Table {table_name!r} is missing column {column_name!r}")
        for column_name in sorted(set(actual_columns) - expected_columns):
            drift.append(f"Table {table_name!r} has unexpected column {column_name!r}")

        for column_name in sorted(expected_columns & set(actual_columns)):
            expected = table.columns[column_name]
            actual = actual_columns[column_name]
            expected_type = _type_signature(expected.type, connection.dialect)
            actual_type = _type_signature(actual["type"], connection.dialect)
            if expected_type != actual_type:
                drift.append(
                    f"Column {table_name}.{column_name} type mismatch: "
                    f"expected {expected_type}, found {actual_type}"
                )
            if expected.nullable != actual["nullable"]:
                drift.append(
                    f"Column {table_name}.{column_name} nullability mismatch: "
                    f"expected nullable={expected.nullable}, found nullable={actual['nullable']}"
                )
            if not _default_matches(expected, actual, connection.dialect.name):
                drift.append(
                    f"Column {table_name}.{column_name} default mismatch: "
                    f"expected {_normalize_default(expected.server_default.arg) if expected.server_default else None!r}, "
                    f"found {_normalize_default(actual.get('default'))!r}"
                )

        expected_pk = tuple(column.name for column in table.primary_key.columns)
        actual_pk = tuple(inspector.get_pk_constraint(table_name).get("constrained_columns") or ())
        if expected_pk != actual_pk:
            drift.append(
                f"Table {table_name!r} primary key mismatch: "
                f"expected {expected_pk!r}, found {actual_pk!r}"
            )

        expected_indexes = {
            (index.name, tuple(column.name for column in index.columns), bool(index.unique))
            for index in table.indexes
        }
        actual_indexes = {
            (
                index.get("name"),
                tuple(index.get("column_names") or ()),
                bool(index.get("unique")),
            )
            for index in inspector.get_indexes(table_name)
            if not index.get("duplicates_constraint")
        }
        for index in sorted(expected_indexes - actual_indexes, key=repr):
            drift.append(f"Table {table_name!r} is missing index {index!r}")
        for index in sorted(actual_indexes - expected_indexes, key=repr):
            drift.append(f"Table {table_name!r} has unexpected index {index!r}")

        expected_unique = {
            tuple(column.name for column in constraint.columns)
            for constraint in table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        actual_unique = {
            tuple(constraint.get("column_names") or ())
            for constraint in inspector.get_unique_constraints(table_name)
        }
        for columns in sorted(expected_unique - actual_unique):
            drift.append(f"Table {table_name!r} is missing unique constraint on {columns!r}")
        for columns in sorted(actual_unique - expected_unique):
            drift.append(f"Table {table_name!r} has unexpected unique constraint on {columns!r}")

    return drift


async def _inspect_live_schema() -> list[str]:
    async with engine.connect() as connection:
        return await connection.run_sync(compare_schema)


def main() -> int:
    print("Schema verification is read-only; no DDL or data changes are performed.")
    print(
        "Historical note: the T0.7 baseline lacked family_members; "
        "init_db() uses Base.metadata.create_all() to add missing tables at boot."
    )
    drift = asyncio.run(_inspect_live_schema())
    if drift:
        print(f"Schema drift detected ({len(drift)} item(s)):")
        for item in drift:
            print(f"- {item}")
        return 1

    print("No schema drift detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
