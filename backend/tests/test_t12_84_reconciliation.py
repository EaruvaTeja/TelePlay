import asyncio
import sys
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app import streaming as stream_engine
from app.database import Base
from app.models import File, User
from app.routers import streaming as stream_router


def test_prepare_stream_mixed_gone_and_error_is_unavailable(monkeypatch):
    class FakeClient:
        def __init__(self, pool_index, result):
            self.pool_index = pool_index
            self.result = result

        async def get_messages(self, chat_id, message_id):
            if isinstance(self.result, Exception):
                raise self.result
            return self.result

    clients = [FakeClient(0, None), FakeClient(1, RuntimeError("offline"))]
    monkeypatch.setattr(stream_engine, "clients", clients)
    monkeypatch.setattr(
        stream_engine,
        "settings",
        SimpleNamespace(telegram_storage_channel_id=-100),
    )
    stream_engine.forget_all()

    with pytest.raises(stream_engine.StreamUnavailable):
        asyncio.run(stream_engine.prepare_stream(501))


def test_prepare_stream_returns_gone_only_when_all_clients_succeed(monkeypatch):
    class FakeClient:
        def __init__(self, pool_index):
            self.pool_index = pool_index

        async def get_messages(self, chat_id, message_id):
            return None

    monkeypatch.setattr(stream_engine, "clients", [FakeClient(0), FakeClient(1)])
    monkeypatch.setattr(
        stream_engine,
        "settings",
        SimpleNamespace(telegram_storage_channel_id=-100),
    )
    stream_engine.forget_all()

    assert asyncio.run(stream_engine.prepare_stream(502)) == []


def test_prepare_stream_live_nonmedia_message_is_not_treated_as_gone(monkeypatch):
    class FakeClient:
        def __init__(self, pool_index, result):
            self.pool_index = pool_index
            self.result = result

        async def get_messages(self, chat_id, message_id):
            return self.result

    clients = [
        FakeClient(
            0,
            SimpleNamespace(empty=False, document=None, video=None, audio=None),
        ),
        FakeClient(1, None),
    ]
    monkeypatch.setattr(stream_engine, "clients", clients)
    monkeypatch.setattr(
        stream_engine,
        "settings",
        SimpleNamespace(telegram_storage_channel_id=-100),
    )
    stream_engine.forget_all()

    with pytest.raises(stream_engine.StreamUnavailable):
        asyncio.run(stream_engine.prepare_stream(504))


@pytest.fixture
def media_file_db(monkeypatch, tmp_path):
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'reconcile.db'}",
        poolclass=NullPool,
    )
    sessions = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def seed():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with sessions() as db:
            user = User(telegram_id=876543210, role="admin")
            db.add(user)
            await db.flush()
            file = File(
                user_id=user.id,
                file_id="telegram-file",
                file_unique_id="telegram-file-unique",
                channel_message_id=503,
                file_name="clip.mp4",
                file_size=4096,
                mime_type="video/mp4",
                file_type="video",
            )
            db.add(file)
            await db.commit()
            await db.refresh(file)
            return file.id

    file_id = asyncio.run(seed())
    monkeypatch.setattr(stream_router, "async_session", sessions)
    monkeypatch.setattr(
        stream_router,
        "get_meta",
        lambda requested_id: asyncio.sleep(
            0,
            result=stream_router.FileMeta(
                requested_id, 4096, "video/mp4", "clip.mp4", 503, None
            ),
        ),
    )
    monkeypatch.setattr(stream_router, "prepare_stream", _empty_stream_context)
    invalidated = []
    monkeypatch.setattr(
        stream_router,
        "invalidate_meta",
        lambda current_id, message_id: invalidated.append((current_id, message_id)),
    )
    yield sessions, engine, file_id, invalidated
    asyncio.run(engine.dispose())


async def _empty_stream_context(message_id):
    return []


@pytest.mark.parametrize(
    ("lookup_result", "expected_status", "expected_exists"),
    [
        (RuntimeError("Telegram unavailable"), 503, True),
        (None, 404, False),
        (SimpleNamespace(empty=True), 404, False),
        (SimpleNamespace(empty=False, id=503), 503, True),
    ],
)
def test_empty_stream_context_requires_authoritative_gone_confirmation(
    monkeypatch,
    media_file_db,
    lookup_result,
    expected_status,
    expected_exists,
):
    sessions, _, file_id, invalidated = media_file_db
    calls = []

    async def authoritative_lookup(chat_id, message_id):
        calls.append((chat_id, message_id))
        if isinstance(lookup_result, Exception):
            raise lookup_result
        return lookup_result

    monkeypatch.setattr(
        stream_router,
        "telegram",
        SimpleNamespace(
            tg_client=SimpleNamespace(get_messages=authoritative_lookup),
            settings=SimpleNamespace(telegram_storage_channel_id=-100),
        ),
    )
    request = SimpleNamespace(headers={})
    try:
        asyncio.run(stream_router._resolve_media(request, file_id, 0))
    except stream_router.HTTPException as exc:
        assert exc.status_code == expected_status
        expected_code = "FILE_GONE" if expected_status == 404 else "STREAM_UNAVAILABLE"
        assert exc.detail["code"] == expected_code
    else:
        pytest.fail("empty streaming context must not resolve successfully")

    assert calls == [(-100, 503)]

    async def row_exists():
        async with sessions() as db:
            return (
                await db.execute(select(File).where(File.id == file_id))
            ).scalar_one_or_none() is not None

    assert asyncio.run(row_exists()) is expected_exists
    if expected_exists:
        assert invalidated == []
    else:
        assert invalidated == [(file_id, 503)]


class _FakeScalarResult:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self):
        return self

    def all(self):
        return self.rows


class _FakeSyncSession:
    def __init__(self, rows):
        self.rows = rows
        self.deleted = []
        self.committed = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, statement):
        return _FakeScalarResult(self.rows)

    async def delete(self, row):
        self.deleted.append(row)

    async def commit(self):
        self.committed += 1


class _FakeStatus:
    def __init__(self):
        self.edits = []

    async def edit(self, text):
        self.edits.append(text)


class _FakeSyncMessage:
    def __init__(self, admin_id, command):
        self.from_user = SimpleNamespace(id=admin_id)
        self.command = command
        self.replies = []
        self.statuses = []

    async def reply(self, text, **kwargs):
        self.replies.append(text)
        status = _FakeStatus()
        self.statuses.append(status)
        return status


def _sync_rows():
    return [
        SimpleNamespace(id=file_id, channel_message_id=1000 + file_id)
        for file_id in range(1, 11)
    ]


async def _sync_lookup(chat_id, message_ids):
    gone_message_id = 1009
    return [
        SimpleNamespace(id=message_id)
        for message_id in message_ids
        if message_id != gone_message_id
    ]


@pytest.fixture
def bot_module(monkeypatch):
    import app

    already_loaded = "app.bot" in sys.modules
    import app.bot as bot

    yield bot

    if not already_loaded:
        sys.modules.pop("app.bot", None)
        if hasattr(app, "bot"):
            delattr(app, "bot")


def _configure_sync(monkeypatch, bot, rows):
    db = _FakeSyncSession(rows)
    monkeypatch.setattr(bot, "async_session", lambda: db)
    monkeypatch.setattr(bot.tg_client, "get_messages", _sync_lookup)
    from app.routers import streaming as router

    invalidated = []
    monkeypatch.setattr(
        router,
        "invalidate_meta",
        lambda file_id, message_id: invalidated.append((file_id, message_id)),
    )
    return db, invalidated


def test_sync_command_dry_run_then_confirm_deletes_only_confirmed_candidates(
    monkeypatch, bot_module, caplog
):
    caplog.set_level("INFO", logger="app.bot")
    rows = _sync_rows()
    db, invalidated = _configure_sync(monkeypatch, bot_module, rows)
    message = _FakeSyncMessage(bot_module.settings.admin_telegram_id, ["sync"])

    asyncio.run(bot_module.sync_command(None, message))
    assert db.deleted == []
    assert db.committed == 0
    assert "1 candidate entry" in message.statuses[0].edits[-1]
    assert "Nothing was deleted" in message.statuses[0].edits[-1]

    message.command = ["sync", "confirm"]
    asyncio.run(bot_module.sync_command(None, message))

    assert db.deleted == [rows[8]]
    assert db.committed == 1
    assert invalidated == [(rows[8].id, rows[8].channel_message_id)]
    assert "Removed 1 dead entry" in message.statuses[1].edits[-1]
    assert any("proposed deletion" in record.message for record in caplog.records)
    assert any("deleted file_id=9" in record.message for record in caplog.records)


def test_sync_command_reports_safety_abort_instead_of_removed_zero(
    monkeypatch, bot_module
):
    rows = _sync_rows()
    db, _ = _configure_sync(monkeypatch, bot_module, rows)

    async def all_gone(chat_id, message_ids):
        return []

    monkeypatch.setattr(bot_module.tg_client, "get_messages", all_gone)
    message = _FakeSyncMessage(bot_module.settings.admin_telegram_id, ["sync", "confirm"])

    asyncio.run(bot_module.sync_command(None, message))

    assert message.statuses[0].edits[-1] == "aborted for safety"
    assert db.deleted == []
    assert db.committed == 0


def test_sync_confirm_aborts_all_deletes_if_any_batch_lookup_errors(
    monkeypatch, bot_module
):
    rows = [
        SimpleNamespace(id=index + 1, channel_message_id=2000 + index)
        for index in range(101)
    ]
    db, invalidated = _configure_sync(monkeypatch, bot_module, rows)
    calls = 0

    async def partial_failure(chat_id, message_ids):
        nonlocal calls
        calls += 1
        if calls == 1:
            return [
                SimpleNamespace(id=message_id)
                for message_id in message_ids
                if message_id != 2000
            ]
        raise RuntimeError("second batch failed")

    monkeypatch.setattr(bot_module.tg_client, "get_messages", partial_failure)

    with pytest.raises(RuntimeError, match="second batch failed"):
        asyncio.run(bot_module.sync_with_channel(confirm=True))

    assert calls == 2
    assert db.deleted == []
    assert db.committed == 0
    assert invalidated == []


def test_sync_command_surfaces_lookup_failure(monkeypatch, bot_module):
    rows = _sync_rows()
    db, _ = _configure_sync(monkeypatch, bot_module, rows)

    async def unavailable(chat_id, message_ids):
        raise RuntimeError("Telegram unavailable")

    monkeypatch.setattr(bot_module.tg_client, "get_messages", unavailable)
    message = _FakeSyncMessage(bot_module.settings.admin_telegram_id, ["sync"])

    asyncio.run(bot_module.sync_command(None, message))

    assert "Sync failed" in message.statuses[0].edits[-1]
    assert "check server logs" in message.statuses[0].edits[-1]
    assert db.deleted == []
    assert db.committed == 0
