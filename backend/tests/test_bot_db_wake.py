import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import bot, models


DB_WAKING_MESSAGE = (
    "⚠️ **Couldn't save your file**\n\n"
    "The database may be waking up or temporarily down (it sleeps after a few minutes of inactivity).\n\n"
    "Please wait ~30 seconds, send /start, then forward the file again."
)


class FakeStatusMessage:
    def __init__(self):
        self.edits = []

    async def edit(self, text, **kwargs):
        self.edits.append((text, kwargs))


class FakeMessage:
    def __init__(self, *, has_video=True, command=None):
        self.from_user = SimpleNamespace(
            id=123456789,
            username="family",
            first_name="Family",
            last_name=None,
        )
        self.id = 42
        self.command = command or []
        self.text = f"/{self.command[0]}" if self.command else "upload"
        self.video = (
            SimpleNamespace(
                file_id="file-id",
                file_unique_id="unique-id",
                file_name="test.mp4",
                file_size=100,
                mime_type="video/mp4",
                duration=1,
                width=10,
                height=10,
                thumbs=[],
            )
            if has_video
            else None
        )
        self.audio = None
        self.document = None
        self.photo = None
        self.replies = []
        self.stop_propagated = False
        self.status_message = FakeStatusMessage()

    async def reply(self, text, **kwargs):
        self.replies.append((text, kwargs))
        if text == "📥 Processing file...":
            return self.status_message

    def stop_propagation(self):
        self.stop_propagated = True


class FakeCallback:
    def __init__(self, sender_id, data="server_status"):
        self.from_user = SimpleNamespace(id=sender_id)
        self.data = data
        self.answers = []

    async def answer(self, text="", show_alert=False):
        self.answers.append((text, show_alert))


class FakeProbeSession:
    def __init__(self, *, error=None, wait_forever=False):
        self.error = error
        self.wait_forever = wait_forever
        self.statements = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def execute(self, statement):
        self.statements.append(str(statement))
        if self.error:
            raise self.error
        if self.wait_forever:
            await asyncio.Event().wait()


class FailingCommitSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    def add(self, row):
        pass

    def get_bind(self):
        return SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))

    async def execute(self, statement):
        return EmptyResult()

    async def commit(self):
        raise OperationalError("INSERT", {}, OSError("database unavailable"))


class EmptyResult:
    def scalars(self):
        return self

    def first(self):
        return None


class FailingStatusMessage:
    async def edit(self, text, **kwargs):
        raise RuntimeError("status edit failed")


@pytest.fixture
def upload_database(monkeypatch, tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'upload.db'}")
    sessions = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        async with sessions() as db:
            db.add(
                models.User(
                    telegram_id=123456789,
                    username="family",
                    first_name="Family",
                    role="admin",
                )
            )
            db.add(
                models.FamilyMember(
                    telegram_id=123456789, is_owner=True, active=True
                )
            )
            await db.commit()

    asyncio.run(setup())
    monkeypatch.setattr(bot, "async_session", sessions)
    yield sessions
    asyncio.run(engine.dispose())


def _assert_status_button(markup):
    button = markup.inline_keyboard[0][0]
    assert button.text == "🩺 Check Server Status"
    assert button.callback_data == "server_status"


def _db_error():
    return OperationalError("SELECT 1", {}, OSError("database unavailable"))


def test_upload_user_lookup_db_failure_replies_with_wake_up_button(monkeypatch, caplog):
    async def fail_user_lookup(*args, **kwargs):
        raise _db_error()

    async def fail_membership_lookup(telegram_id):
        raise _db_error()

    forward = AsyncMock()
    monkeypatch.setattr(bot, "is_active_member", fail_membership_lookup)
    monkeypatch.setattr(bot, "get_or_create_user", fail_user_lookup)
    monkeypatch.setattr(bot, "forward_to_storage_channel", forward)
    message = FakeMessage()

    with caplog.at_level(logging.WARNING, logger="app.bot"):
        asyncio.run(bot.handle_file(None, message))

    assert message.replies[0][0] == "📥 Processing file..."
    assert message.status_message.edits[0][0] == DB_WAKING_MESSAGE
    _assert_status_button(message.status_message.edits[0][1]["reply_markup"])
    forward.assert_not_awaited()
    assert "OperationalError" in caplog.text
    assert "database unavailable" not in caplog.text


@pytest.mark.parametrize("delete_succeeds", [True, False])
def test_upload_db_failure_after_forward_compensates_and_adds_status_button(
    monkeypatch, delete_succeeds
):
    async def get_user(*args, **kwargs):
        return SimpleNamespace(id=7)

    forwarded = SimpleNamespace(id=88)
    delete = AsyncMock(return_value=delete_succeeds)
    monkeypatch.setattr(bot, "get_or_create_user", get_user)
    monkeypatch.setattr(bot, "is_active_member", AsyncMock(return_value=True))
    monkeypatch.setattr(
        bot, "forward_to_storage_channel", AsyncMock(return_value=forwarded)
    )
    monkeypatch.setattr(bot, "delete_from_storage_channel", delete)
    monkeypatch.setattr(bot, "async_session", lambda: FailingCommitSession())
    message = FakeMessage()

    asyncio.run(bot.handle_file(None, message))

    delete.assert_awaited_once_with(forwarded.id)
    text, kwargs = message.status_message.edits[0]
    _assert_status_button(kwargs["reply_markup"])
    if delete_succeeds:
        assert text == DB_WAKING_MESSAGE
    else:
        assert text.startswith("❌ **Database and Telegram error**")
        assert "An admin will need to manually clean up." in text


def test_upload_status_edit_failure_keeps_committed_file(
    upload_database, monkeypatch, caplog
):
    forward = AsyncMock(return_value=SimpleNamespace(id=88))
    delete = AsyncMock(return_value=True)
    monkeypatch.setattr(bot, "forward_to_storage_channel", forward)
    monkeypatch.setattr(bot, "delete_from_storage_channel", delete)
    message = FakeMessage()
    message.status_message = FailingStatusMessage()

    with caplog.at_level(logging.WARNING, logger="app.bot"):
        asyncio.run(bot.handle_file(None, message))

    forward.assert_awaited_once_with(message)
    delete.assert_not_awaited()
    assert message.replies[1][0].startswith("✅ File saved to the shared library")
    assert "status notification failed" in caplog.text

    async def saved_file_count():
        async with upload_database() as db:
            return len((await db.execute(select(models.File))).scalars().all())

    assert asyncio.run(saved_file_count()) == 1


def test_upload_commit_ack_failure_checks_persisted_row_before_compensating(
    upload_database, monkeypatch
):
    real_commit = AsyncSession.commit

    async def commit_then_raise(db):
        await real_commit(db)
        raise OperationalError("COMMIT", {}, OSError("commit acknowledgement lost"))

    monkeypatch.setattr(AsyncSession, "commit", commit_then_raise)
    forward = AsyncMock(return_value=SimpleNamespace(id=89))
    delete = AsyncMock(return_value=True)
    monkeypatch.setattr(bot, "forward_to_storage_channel", forward)
    monkeypatch.setattr(bot, "delete_from_storage_channel", delete)
    message = FakeMessage()

    asyncio.run(bot.handle_file(None, message))

    forward.assert_awaited_once_with(message)
    delete.assert_not_awaited()
    assert message.replies[1][0].startswith("✅ File saved to the shared library")

    async def saved_file_count():
        async with upload_database() as db:
            return len((await db.execute(select(models.File))).scalars().all())

    assert asyncio.run(saved_file_count()) == 1


def test_upload_forward_failure_does_not_reference_unbound_forwarded(monkeypatch):
    async def get_user(*args, **kwargs):
        return SimpleNamespace(id=7)

    async def fail_forward(message):
        raise RuntimeError("forward failed")

    monkeypatch.setattr(bot, "get_or_create_user", get_user)
    monkeypatch.setattr(bot, "is_active_member", AsyncMock(return_value=True))
    monkeypatch.setattr(bot, "forward_to_storage_channel", fail_forward)
    message = FakeMessage()

    asyncio.run(bot.handle_file(None, message))

    assert message.status_message.edits[0][0] == "❌ Failed to process file: forward failed"


def test_start_db_failure_uses_wake_up_reply_and_button(monkeypatch):
    async def fail_user_lookup(*args, **kwargs):
        raise InterfaceError("SELECT 1", {}, OSError("database unavailable"))

    async def fail_membership_lookup(telegram_id):
        raise _db_error()

    monkeypatch.setattr(bot, "is_active_member", fail_membership_lookup)
    monkeypatch.setattr(bot, "get_or_create_user", fail_user_lookup)
    message = FakeMessage(has_video=False, command=["start"])

    asyncio.run(bot.check_auth(None, message))
    assert message.stop_propagated is False
    asyncio.run(bot.start_command(None, message))

    assert message.replies[0][0] == DB_WAKING_MESSAGE
    _assert_status_button(message.replies[0][1]["reply_markup"])


def test_database_fallback_does_not_authorize_non_bootstrap_user(monkeypatch):
    async def fail_membership_lookup(telegram_id):
        raise _db_error()

    monkeypatch.setattr(bot, "is_active_member", fail_membership_lookup)
    message = FakeMessage(
        has_video=False,
        command=["start"],
    )
    message.from_user = SimpleNamespace(
        id=max(bot.settings.auth_users) + 1,
        username="outsider",
        first_name="Outsider",
        last_name=None,
    )

    asyncio.run(bot.check_auth(None, message))

    assert message.stop_propagated is True
    assert message.replies[0][0].startswith("🚫 **Access Restricted**")


def test_server_status_authorized_db_up_answers_ready(monkeypatch):
    session = FakeProbeSession()
    monkeypatch.setattr(bot, "async_session", lambda: session)
    callback = FakeCallback(bot.settings.auth_users[0])

    asyncio.run(bot.handle_callback(None, callback))

    assert session.statements == ["SELECT 1"]
    assert callback.answers == [
        ("✅ Server is up — database ready. Please re-forward your file.", True)
    ]
    assert "server_status" not in bot.DESTRUCTIVE_CALLBACKS


def test_server_status_database_failure_answers_waking(monkeypatch):
    session = FakeProbeSession(error=_db_error())
    monkeypatch.setattr(bot, "async_session", lambda: session)
    callback = FakeCallback(bot.settings.auth_users[0])

    asyncio.run(bot.handle_callback(None, callback))

    assert callback.answers == [
        ("⏳ Still waking up — please try again in ~30 seconds.", True)
    ]


def test_server_status_timeout_is_bounded_and_answers_waking(monkeypatch):
    session = FakeProbeSession(wait_forever=True)
    monkeypatch.setattr(bot, "async_session", lambda: session)
    real_wait_for = asyncio.wait_for

    async def short_wait_for(awaitable, timeout):
        assert timeout == 8
        return await real_wait_for(awaitable, timeout=0.01)

    monkeypatch.setattr(bot.asyncio, "wait_for", short_wait_for)
    callback = FakeCallback(bot.settings.auth_users[0])

    asyncio.run(bot.handle_callback(None, callback))

    assert callback.answers == [
        ("⏳ Still waking up — please try again in ~30 seconds.", True)
    ]


def test_server_status_rejects_non_whitelisted_user_before_database(monkeypatch):
    def unexpected_database_access():
        raise AssertionError("unauthorized status request must not probe the database")

    monkeypatch.setattr(bot, "async_session", unexpected_database_access)
    sender_id = max(bot.settings.auth_users) + 1
    callback = FakeCallback(sender_id)

    asyncio.run(bot.handle_callback(None, callback))

    assert callback.answers == [("Unauthorized", True)]
