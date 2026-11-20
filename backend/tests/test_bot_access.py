"""T5 — Management Surface & Bot access control.

SYNC tests only (this repo has NO asyncio_mode config): every async call goes
through asyncio.run(...) inside a sync test. No real Telegram, no Neon:
each test spins up a throwaway sqlite engine, patches bot.async_session and
bot.limiter with fakes, and calls the real bot handlers directly.

app.bot is uncache-removed after every test so test_schema_migration (which
imports app.bot lazily after patching database.async_session) can still fresh-
import it with its own patched engine.
"""
import asyncio
import sys
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from fastapi.testclient import TestClient

import app
from app import database, models
from app.database import get_db
from app.main import app as fastapi_app


class FakeLimiter:
    def __init__(self):
        self.sessions = []
        self.kicked = []
        self.stopped_owners = []
        self.stopped_roles = []

    def active(self):
        return list(self.sessions)

    def kick(self, device_id):
        self.kicked.append(device_id)

    def stop_owner(self, owner_id):
        self.stopped_owners.append(owner_id)

    def stop_role(self, role):
        self.stopped_roles.append(role)


class FakeCallback:
    def __init__(self, sender_id, data):
        self.from_user = SimpleNamespace(id=sender_id)
        self.data = data
        self.message = FakeCallbackMessage(sender_id)
        self.answers = []

    async def answer(self, text="", show_alert=False):
        self.answers.append((text, show_alert))


class FakeCallbackMessage:
    def __init__(self, sender_id):
        self.from_user = SimpleNamespace(id=sender_id)
        self.replies = []
        self.edits = []

    async def reply(self, text, **kwargs):
        self.replies.append((text, kwargs))

    async def edit(self, text, **kwargs):
        self.edits.append((text, kwargs))


class FakeMessage:
    def __init__(self, sender_id, text):
        self.from_user = SimpleNamespace(
            id=sender_id,
            username="family",
            first_name="Family",
            last_name=None,
        )
        self.text = text
        self.command = text.split()
        self.replies = []
        self.stop_propagated = False
        self.id = 42
        self.video = None
        self.audio = None
        self.document = None
        self.photo = None
        self.status_message = FakeStatusMessage()

    async def reply(self, text, **kwargs):
        self.replies.append((text, kwargs))
        if text == "📥 Processing file...":
            return self.status_message

    def stop_propagation(self):
        self.stop_propagated = True


class FakeStatusMessage:
    def __init__(self):
        self.edits = []

    async def edit(self, text, **kwargs):
        self.edits.append((text, kwargs))


class FakeUploadMessage(FakeMessage):
    def __init__(self, sender_id):
        super().__init__(sender_id, "video")
        self.video = SimpleNamespace(
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


@pytest.fixture
def patched_bot(monkeypatch, tmp_path):
    """Per-test throwaway sqlite DB + fresh app.bot import + fake limiter."""
    eng = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 't5.db'}")

    async def seed():
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        sess_local = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
        async with sess_local() as s:
            # 123456789 is the owner (AUTH_USERS from conftest).
            s.add(models.FamilyMember(telegram_id=123456789, is_owner=True, active=True))
            s.add(models.FamilyMember(telegram_id=999000111, is_owner=False, active=True))
            s.add(models.FamilyMember(telegram_id=888000222, is_owner=False, active=False))
            s.add(models.FamilyMember(telegram_id=777000333, is_owner=False, active=True))
            s.add(models.User(telegram_id=-1, username="guest", first_name="Guest", role="guest"))
            s.add(
                models.User(
                    telegram_id=999000111,
                    username="member",
                    first_name="Member",
                    role="admin",
                    auth_version=0,
                )
            )
            s.add(
                models.User(
                    telegram_id=888000222,
                    username="removed",
                    first_name="Removed",
                    role="guest",
                    auth_version=0,
                )
            )
            s.add(models.GuestCredential(id=1, pin_hash=None, expires_at=None, version=0))
            await s.commit()

    asyncio.run(seed())

    sess = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)

    # Fresh-import app.bot so bot.async_session captures this test's patched engine.
    sys.modules.pop("app.bot", None)
    if hasattr(app, "bot"):
        delattr(app, "bot")

    monkeypatch.setattr(database, "async_session", sess)
    import app.bot as bot_mod  # noqa: WPS433

    monkeypatch.setattr(bot_mod, "async_session", sess)
    fake = FakeLimiter()
    monkeypatch.setattr(bot_mod, "limiter", fake)

    yield bot_mod, fake, eng, sess

    # Uncache app.bot so other modules (e.g. test_schema_migration) can fresh-import.
    sys.modules.pop("app.bot", None)
    if hasattr(app, "bot"):
        delattr(app, "bot")
    asyncio.run(eng.dispose())


# ════════════════════════════════════════════════════════════════════════════
# 1. Unauthorized callback -> rejected, action not executed
# ════════════════════════════════════════════════════════════════════════════

def test_unauthorized_callback_rejected(patched_bot):
    bot, fake, _, _ = patched_bot
    cb = FakeCallback(sender_id=555000999, data="confirmdelfile:1")  # not a family member
    asyncio.run(bot.handle_callback(None, cb))
    assert cb.answers == [("Unauthorized", True)]
    assert fake.kicked == []


def test_removed_member_callback_rejected(patched_bot):
    bot, fake, _, _ = patched_bot
    cb = FakeCallback(sender_id=888000222, data="show_files")  # active=False
    asyncio.run(bot.handle_callback(None, cb))
    assert cb.answers == [("Unauthorized", True)]


# ════════════════════════════════════════════════════════════════════════════
# 2. Authorized family member can trigger non-destructive callbacks
# ════════════════════════════════════════════════════════════════════════════

def test_authorized_member_non_destructive_callback(patched_bot):
    bot, fake, _, _ = patched_bot
    cb = FakeCallback(sender_id=999000111, data="show_files")  # active member
    asyncio.run(bot.handle_callback(None, cb))
    assert not any(a[0] == "Unauthorized" for a in cb.answers)
    assert cb.message.replies  # library listing sent


# ════════════════════════════════════════════════════════════════════════════
# 3. Only owner can trigger user_add, user_remove, kick
# ════════════════════════════════════════════════════════════════════════════

def test_only_owner_can_add_remove_kick(patched_bot):
    bot, fake, _, _ = patched_bot

    # non-owner member attempts user_add
    msg = FakeMessage(999000111, "/user_add 111222333")
    asyncio.run(bot.user_add_command(None, msg))
    assert msg.replies[0][0] == "Owner only."

    # non-owner member attempts user_remove
    msg = FakeMessage(999000111, "/user_remove 777000333")
    asyncio.run(bot.user_remove_command(None, msg))
    assert msg.replies[0][0] == "Owner only."

    # non-owner member attempts kick command
    msg = FakeMessage(999000111, "/kick dev1")
    asyncio.run(bot.kick_command(None, msg))
    assert msg.replies[0][0] == "Owner only."
    assert fake.kicked == []

    # owner user_add works
    msg = FakeMessage(123456789, "/user_add 111222333")
    asyncio.run(bot.user_add_command(None, msg))
    assert msg.replies[0][0] == "Added"

    # owner kick callback works
    cb = FakeCallback(123456789, "kick:dev1")
    asyncio.run(bot.handle_callback(None, cb))
    assert fake.kicked == ["dev1"]

    # non-owner kick callback rejected
    cb = FakeCallback(999000111, "kick:dev2")
    asyncio.run(bot.handle_callback(None, cb))
    assert cb.answers == [("Unauthorized", True)]
    assert "dev2" not in fake.kicked


# ════════════════════════════════════════════════════════════════════════════
# 4. user_remove bumps auth_version and calls limiter.stop_owner
# ════════════════════════════════════════════════════════════════════════════

def test_user_remove_bumps_version_and_stops_owner(patched_bot):
    bot, fake, eng, sess = patched_bot

    async def user_id_of(telegram_id):
        async with sess() as s:
            res = await s.execute(select(models.User).where(models.User.telegram_id == telegram_id))
            return res.scalar_one().id

    uid = asyncio.run(user_id_of(999000111))

    msg = FakeMessage(123456789, "/user_remove 999000111")
    asyncio.run(bot.user_remove_command(None, msg))
    assert msg.replies[0][0] == "Removed and sessions killed"
    assert fake.stopped_owners == [uid]

    async def check():
        async with sess() as s:
            m = (
                await s.execute(
                    select(models.FamilyMember).where(models.FamilyMember.telegram_id == 999000111)
                )
            ).scalar_one()
            u = (
                await s.execute(select(models.User).where(models.User.telegram_id == 999000111))
            ).scalar_one()
        return m.active, u.role, u.auth_version

    active, role, version = asyncio.run(check())
    assert active is False
    assert role == "guest"
    assert version == 1


# ════════════════════════════════════════════════════════════════════════════
# 5. /help output contains all documented commands
# ════════════════════════════════════════════════════════════════════════════

def test_help_contains_all_commands(patched_bot):
    bot, _, _, _ = patched_bot
    msg = FakeMessage(123456789, "/help")
    asyncio.run(bot.help_command(None, msg))
    text = msg.replies[0][0]

    for cmd in [
        "/start", "/help", "/web", "/login", "/logout_all", "/sync",
        "/myfiles", "/file", "/users", "/user_add", "/user_remove",
        "/sessions", "/kick", "/guest",
    ]:
        assert cmd in text, f"missing {cmd} in /help"
    for group in ["GENERAL", "FILE MANAGEMENT", "FAMILY MANAGEMENT", "PLAYBACK", "GUEST"]:
        assert group in text, f"missing group {group} in /help"


# ════════════════════════════════════════════════════════════════════════════
# 6. /myfiles pagination (offset increments via myfiles_next:<offset>)
# ════════════════════════════════════════════════════════════════════════════

def _next_callback_data(markup):
    for row in markup.inline_keyboard:
        for btn in row:
            if getattr(btn, "callback_data", None) and btn.callback_data.startswith("myfiles_next:"):
                return btn.callback_data
    return None


def test_myfiles_pagination(patched_bot):
    bot, _, eng, sess = patched_bot

    async def seed_files():
        base = datetime(2026, 1, 1)
        async with sess() as s:
            for i in range(12):
                s.add(
                    models.File(
                        user_id=2,
                        channel_message_id=100 + i,
                        file_id=f"fid{i}",
                        file_unique_id=f"uid{i}",
                        file_name=f"file{i}.mp4",
                        file_type="video",
                        file_size=1000,
                        created_at=base + timedelta(seconds=i),
                    )
                )
            await s.commit()

    asyncio.run(seed_files())

    msg = FakeMessage(123456789, "/myfiles")
    asyncio.run(bot.myfiles_command(None, msg))
    text = msg.replies[0][0]
    markup = msg.replies[0][1]["reply_markup"]

    # newest inserts first (created_at.desc)
    assert "file11.mp4" in text
    assert "file2.mp4" in text
    assert "file0.mp4" not in text
    assert "file1.mp4" not in text
    assert _next_callback_data(markup) == "myfiles_next:10"

    cb = FakeCallback(123456789, "myfiles_next:10")
    asyncio.run(bot.handle_callback(None, cb))
    page2 = cb.message.edits[0][0]
    markup2 = cb.message.edits[0][1]["reply_markup"]

    assert "file1.mp4" in page2
    assert "file0.mp4" in page2
    assert _next_callback_data(markup2) is None


# ════════════════════════════════════════════════════════════════════════════
# 7. get_or_create_user assigns admin only for active family_members
# ════════════════════════════════════════════════════════════════════════════

def test_get_or_create_user_role_by_family_membership(patched_bot):
    bot, _, _, sess = patched_bot

    async def make_roles_stale():
        async with sess() as s:
            active = (
                await s.execute(
                    select(models.User).where(models.User.telegram_id == 999000111)
                )
            ).scalar_one()
            inactive = (
                await s.execute(
                    select(models.User).where(models.User.telegram_id == 888000222)
                )
            ).scalar_one()
            active.role = "guest"
            inactive.role = "admin"
            await s.commit()

    async def role_of(telegram_id):
        async with sess() as s:
            res = await s.execute(select(models.User.role).where(models.User.telegram_id == telegram_id))
            return res.scalar_one()

    async def go():
        await make_roles_stale()
        await bot.get_or_create_user(999000111)   # active family, existing admin row
        await bot.get_or_create_user(777000333)   # active family, no user row yet -> admin
        await bot.get_or_create_user(888000222)   # inactive family -> guest
        await bot.get_or_create_user(111222333)   # not in family -> guest
        return (
            await role_of(999000111),
            await role_of(777000333),
            await role_of(888000222),
            await role_of(111222333),
        )

    r_active_existing, r_active_new, r_inactive, r_outsider = asyncio.run(go())
    assert r_active_existing == "admin"
    assert r_active_new == "admin"
    assert r_inactive == "guest"
    assert r_outsider == "guest"


def test_db_member_outside_auth_users_can_start_and_upload(patched_bot, monkeypatch):
    bot, _, _, sess = patched_bot
    monkeypatch.setattr(
        bot,
        "settings",
        bot.settings.model_copy(update={"auth_users": [123456789]}),
    )
    message = FakeMessage(777000333, "/start")

    asyncio.run(bot.check_auth(None, message))
    assert message.stop_propagated is False
    asyncio.run(bot.start_command(None, message))
    assert any("Welcome to Media Hub" in reply[0] for reply in message.replies)

    uploaded = FakeUploadMessage(777000333)
    forwarded = SimpleNamespace(id=808)
    forward = AsyncMock(return_value=forwarded)
    monkeypatch.setattr(bot, "forward_to_storage_channel", forward)
    asyncio.run(bot.handle_file(None, uploaded))

    forward.assert_awaited_once_with(uploaded)
    assert uploaded.status_message.edits[0][0].startswith(
        "✅ **File saved to shared library!**"
    )

    async def verify_user_and_file():
        async with sess() as db:
            user = (
                await db.execute(
                    select(models.User).where(models.User.telegram_id == 777000333)
                )
            ).scalar_one()
            file = (
                await db.execute(
                    select(models.File).where(models.File.channel_message_id == 808)
                )
            ).scalar_one()
            return user.role, file.user_id == user.id

    assert asyncio.run(verify_user_and_file()) == ("admin", True)


def test_removed_member_cannot_upload_or_mint_bot_login_codes(patched_bot, monkeypatch):
    bot, _, _, sess = patched_bot
    forward = AsyncMock()
    monkeypatch.setattr(bot, "forward_to_storage_channel", forward)
    before = asyncio.run(_login_code_count(sess))

    start_message = FakeMessage(888000222, "/start")
    asyncio.run(bot.check_auth(None, start_message))
    assert start_message.stop_propagated is True
    assert start_message.replies[0][0].startswith("🚫 **Access Restricted**")

    uploaded = FakeUploadMessage(888000222)
    asyncio.run(bot.handle_file(None, uploaded))
    forward.assert_not_awaited()
    assert uploaded.replies[0][0].startswith("🚫 **Access Restricted**")

    for handler, command in (
        (bot.login_command, "/login"),
        (bot.web_command, "/web"),
    ):
        message = FakeMessage(888000222, command)
        asyncio.run(handler(None, message))
        assert message.replies[0][0].startswith("🚫 **Access Restricted**")

    link_message = FakeMessage(888000222, "/web")
    assert (
        asyncio.run(
            bot.get_web_app_button(
                888000222, "Open Web", target=link_message
            )
        )
        is None
    )
    assert link_message.replies[0][0].startswith("🚫 **Access Restricted**")
    assert asyncio.run(_login_code_count(sess)) == before


async def _login_code_count(sess):
    async with sess() as db:
        return len((await db.execute(select(models.LoginCode))).scalars().all())


def _seed_login_code(sess, code, telegram_id):
    async def seed():
        async with sess() as db:
            db.add(
                models.LoginCode(
                    code=code,
                    telegram_id=telegram_id,
                    expires_at=datetime.utcnow() + timedelta(minutes=5),
                )
            )
            await db.commit()

    asyncio.run(seed())


def test_verify_code_allows_active_db_member_outside_auth_users(patched_bot, monkeypatch):
    bot, _, _, sess = patched_bot
    monkeypatch.setattr(
        bot,
        "settings",
        bot.settings.model_copy(update={"auth_users": [123456789]}),
    )
    _seed_login_code(sess, "87654321", 777000333)

    async def override_get_db():
        async with sess() as db:
            yield db

    monkeypatch.setitem(fastapi_app.dependency_overrides, get_db, override_get_db)
    response = TestClient(fastapi_app).post(
        "/api/auth/verify-code",
        json={"code": "87654321"},
        headers={"X-Device-Id": "active-db-member"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"


def test_verify_code_rejects_removed_member_with_existing_user(patched_bot, monkeypatch):
    _, _, _, sess = patched_bot
    _seed_login_code(sess, "87654322", 888000222)

    async def override_get_db():
        async with sess() as db:
            yield db

    monkeypatch.setitem(fastapi_app.dependency_overrides, get_db, override_get_db)
    response = TestClient(fastapi_app).post(
        "/api/auth/verify-code",
        json={"code": "87654322"},
        headers={"X-Device-Id": "removed-db-member"},
    )

    assert response.status_code == 400

    async def verify_user_role():
        async with sess() as db:
            user = (
                await db.execute(
                    select(models.User).where(models.User.telegram_id == 888000222)
                )
            ).scalar_one()
            return user.role

    assert asyncio.run(verify_user_role()) == "guest"
