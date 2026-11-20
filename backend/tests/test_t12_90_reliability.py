import asyncio
import importlib
import json
from types import SimpleNamespace

import pytest
from pyrogram.errors import AuthKeyDuplicated, AuthKeyUnregistered, SessionRevoked

from app import streaming, telegram


def _reset_auth_key_state(monkeypatch):
    monkeypatch.setattr(telegram, "_unhealthy_clients", {})
    monkeypatch.setattr(telegram, "_auth_key_failure_timestamps", {})
    monkeypatch.setattr(telegram, "telegram_auth_key_unhealthy", False)
    monkeypatch.setattr(telegram, "telegram_auth_key_failure_reason", None)


def _use_fake_clock(monkeypatch):
    clock = {"now": 0.0}
    monkeypatch.setattr(
        telegram,
        "time",
        SimpleNamespace(monotonic=lambda: clock["now"]),
    )
    return clock


async def _register_bot_handlers_on_running_loop(main):
    import app.bot as bot

    main.tg_client.loop = asyncio.get_running_loop()
    main.tg_client.dispatcher.groups.clear()
    importlib.reload(bot)
    await asyncio.sleep(0)


def _patch_lifespan_dependencies(monkeypatch, main):
    async def no_op():
        return None

    monkeypatch.setattr(main, "init_db", no_op)
    monkeypatch.setattr(main, "start_all_clients", no_op)
    monkeypatch.setattr(main, "stop_all_clients", no_op)
    monkeypatch.setattr(main, "engine", SimpleNamespace(dispose=no_op))
    monkeypatch.setattr(main.settings, "sync_on_startup", False)
    main._sync_task = None


def test_lifespan_imports_bot_and_registers_handlers(monkeypatch, caplog):
    from app import main

    _patch_lifespan_dependencies(monkeypatch, main)
    caplog.set_level("INFO", logger="app.main")

    async def run():
        await _register_bot_handlers_on_running_loop(main)
        async with main.lifespan(main.app):
            return sum(len(group) for group in main.tg_client.dispatcher.groups.values())

    handler_count = asyncio.run(run())

    assert handler_count > 0
    assert f"Bot handlers registered: {handler_count}" in caplog.text


def test_lifespan_fails_when_no_bot_handlers_are_registered(monkeypatch, caplog):
    from app import main

    monkeypatch.setattr(main.tg_client.dispatcher, "groups", {})
    caplog.set_level("INFO", logger="app.main")

    async def run():
        async with main.lifespan(main.app):
            pytest.fail("lifespan should fail before yielding")

    with pytest.raises(RuntimeError, match="Bot handlers were not registered"):
        asyncio.run(run())

    assert "Bot handlers registered: 0" in caplog.text


@pytest.mark.parametrize(
    ("error_type", "rpc_name", "operator_instruction"),
    [
        (
            AuthKeyUnregistered,
            "AUTH_KEY_UNREGISTERED",
            "re-authorize this client",
        ),
        (
            AuthKeyDuplicated,
            "AUTH_KEY_DUPLICATED",
            "Stop any duplicate process",
        ),
        (
            SessionRevoked,
            "SESSION_REVOKED",
            "Telegram re-authorization procedure",
        ),
    ],
)
def test_stream_auth_key_errors_disable_client_after_three_failures(
    monkeypatch, caplog, error_type, rpc_name, operator_instruction
):
    _reset_auth_key_state(monkeypatch)
    monkeypatch.setattr(streaming, "_semaphores", {})
    caplog.set_level("CRITICAL", logger="app.telegram")
    error = error_type(None, rpc_name)

    class FakeClient:
        pool_index = 4

        def __init__(self):
            self.calls = 0

        async def stream_media(self, message, offset):
            self.calls += 1
            raise error
            yield b""

    client = FakeClient()

    async def read_stream():
        return [
            chunk
            async for chunk in streaming.stream_file([(4, client, object())], 0, 10)
        ]

    with pytest.raises(streaming.StreamUnavailable):
        asyncio.run(read_stream())

    assert client.calls == 3
    assert not telegram.is_client_healthy(client)
    assert telegram.telegram_auth_key_unhealthy is True
    assert error_type.__name__ in telegram.get_telegram_health_failure()
    assert operator_instruction in caplog.text
    assert "Do not delete session files automatically" in caplog.text or (
        error_type is AuthKeyDuplicated
    )


def test_single_transient_stream_auth_error_recovers_and_clears_counter(monkeypatch):
    _reset_auth_key_state(monkeypatch)
    monkeypatch.setattr(streaming, "_semaphores", {})
    error = AuthKeyUnregistered(None, "AUTH_KEY_UNREGISTERED")

    class FakeClient:
        pool_index = 4

        def __init__(self):
            self.calls = 0

        async def stream_media(self, message, offset):
            self.calls += 1
            if self.calls == 1:
                raise error
            yield b"hello world"

    client = FakeClient()

    async def read_stream():
        return [
            chunk
            async for chunk in streaming.stream_file([(4, client, object())], 0, 10)
        ]

    assert asyncio.run(read_stream()) == [b"hello world"]
    assert client.calls == 2
    assert telegram.is_client_healthy(client)
    assert id(client) not in telegram._auth_key_failure_timestamps
    assert telegram.get_telegram_health_failure() is None


def test_successful_message_lookups_clear_auth_key_failure_counter(monkeypatch):
    _reset_auth_key_state(monkeypatch)
    clock = _use_fake_clock(monkeypatch)
    client = SimpleNamespace(pool_index=2, session=SimpleNamespace(dc_id=2))
    message = SimpleNamespace(
        id=42,
        chat=SimpleNamespace(id=99),
        document=SimpleNamespace(file_size=11, dc_id=2),
    )
    error = AuthKeyUnregistered(None, "AUTH_KEY_UNREGISTERED")

    assert telegram.record_auth_key_failure(client, error) is False
    clock["now"] = 1
    assert telegram.record_auth_key_failure(client, error) is False

    async def lookup(*args, **kwargs):
        return message

    monkeypatch.setattr(streaming, "clients", [client])
    monkeypatch.setattr(streaming, "_client_message", lookup)
    context = asyncio.run(streaming.prepare_stream(42))

    assert context == [(2, client, message)]
    assert id(client) not in telegram._auth_key_failure_timestamps

    clock["now"] = 2
    assert telegram.record_auth_key_failure(client, error) is False
    refreshed = SimpleNamespace(id=42, chat=message.chat)
    refresh_calls = 0

    async def lookup_refresh(*args, **kwargs):
        nonlocal refresh_calls
        refresh_calls += 1
        if refresh_calls == 1:
            raise error
        return refreshed

    monkeypatch.setattr(streaming, "_client_message", lookup_refresh)
    clock["now"] = 3
    with pytest.raises(AuthKeyUnregistered):
        asyncio.run(streaming._refresh(2, client, message))
    assert len(telegram._auth_key_failure_timestamps[id(client)]) == 2
    assert telegram.is_client_healthy(client)

    clock["now"] = 4
    assert asyncio.run(streaming._refresh(2, client, message)) is refreshed
    assert id(client) not in telegram._auth_key_failure_timestamps
    assert telegram.is_client_healthy(client)


def test_three_auth_key_failures_within_window_mark_client_and_report_readiness(
    monkeypatch
):
    _reset_auth_key_state(monkeypatch)
    _use_fake_clock(monkeypatch)
    monkeypatch.setattr(streaming, "_semaphores", {})
    error = AuthKeyUnregistered(None, "AUTH_KEY_UNREGISTERED")

    class FakeClient:
        pool_index = 7

        def __init__(self):
            self.calls = 0

        async def stream_media(self, message, offset):
            self.calls += 1
            raise error
            yield b""

    client = FakeClient()

    async def read_stream():
        return [
            chunk
            async for chunk in streaming.stream_file([(7, client, object())], 0, 10)
        ]

    with pytest.raises(streaming.StreamUnavailable) as exc_info:
        asyncio.run(read_stream())

    assert client.calls == 3
    assert not telegram.is_client_healthy(client)
    assert "AuthKeyUnregistered" in str(exc_info.value)

    from app import main

    class FakeDatabase:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def execute(self, statement):
            return SimpleNamespace(scalar=lambda: 1)

    monkeypatch.setattr(main, "async_session", FakeDatabase)

    async def unexpected_get_me():
        pytest.fail("readiness must not call Telegram after the auth-key failure")

    monkeypatch.setattr(main.tg_client, "get_me", unexpected_get_me)
    response = asyncio.run(main.health_readiness())
    body = json.loads(response.body)

    assert response.status_code == 503
    assert body["checks"]["telegram"] is False
    assert body["telegram_reason"] == telegram.get_telegram_health_failure()


def test_auth_key_failures_spaced_over_sixty_seconds_never_mark_client(monkeypatch):
    _reset_auth_key_state(monkeypatch)
    clock = _use_fake_clock(monkeypatch)
    client = SimpleNamespace(pool_index=5)
    error = AuthKeyUnregistered(None, "AUTH_KEY_UNREGISTERED")

    for now in (0, 61, 122, 183):
        clock["now"] = now
        assert telegram.record_auth_key_failure(client, error) is False
        assert telegram.is_client_healthy(client)

    assert len(telegram._auth_key_failure_timestamps[id(client)]) == 1


def test_success_between_auth_key_failures_resets_the_threshold(monkeypatch):
    _reset_auth_key_state(monkeypatch)
    clock = _use_fake_clock(monkeypatch)
    client = SimpleNamespace(pool_index=6)
    error = AuthKeyUnregistered(None, "AUTH_KEY_UNREGISTERED")

    assert telegram.record_auth_key_failure(client, error) is False
    clock["now"] = 1
    assert telegram.record_auth_key_failure(client, error) is False
    telegram.note_auth_key_success(client)
    assert id(client) not in telegram._auth_key_failure_timestamps

    for now in (2, 3):
        clock["now"] = now
        assert telegram.record_auth_key_failure(client, error) is False
        assert telegram.is_client_healthy(client)

    clock["now"] = 4
    assert telegram.record_auth_key_failure(client, error) is True
    assert not telegram.is_client_healthy(client)


@pytest.mark.parametrize(
    ("error_type", "rpc_name", "operator_instruction"),
    [
        (AuthKeyUnregistered, "AUTH_KEY_UNREGISTERED", "re-authorize this client"),
        (AuthKeyDuplicated, "AUTH_KEY_DUPLICATED", "Stop any duplicate process"),
        (SessionRevoked, "SESSION_REVOKED", "Telegram re-authorization procedure"),
    ],
)
def test_readiness_exposes_auth_key_failure_reason(
    monkeypatch, error_type, rpc_name, operator_instruction
):
    from app import main

    _reset_auth_key_state(monkeypatch)
    telegram.mark_client_unhealthy(
        SimpleNamespace(pool_index=3),
        error_type(None, rpc_name),
    )

    class FakeDatabase:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def execute(self, statement):
            return SimpleNamespace(scalar=lambda: 1)

    monkeypatch.setattr(main, "async_session", FakeDatabase)

    async def unexpected_get_me():
        pytest.fail("readiness must not call an unhealthy Telegram client")

    monkeypatch.setattr(main.tg_client, "get_me", unexpected_get_me)
    response = asyncio.run(main.health_readiness())
    body = json.loads(response.body)

    assert response.status_code == 503
    assert body["checks"]["telegram"] is False
    assert error_type.__name__ in body["telegram_reason"]
    assert operator_instruction in body["telegram_reason"]
