import asyncio
import importlib
import json
from types import SimpleNamespace

import pytest
from pyrogram.errors import AuthKeyDuplicated, AuthKeyUnregistered, SessionRevoked

from app import streaming, telegram


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
def test_stream_auth_key_errors_disable_client_without_retrying(
    monkeypatch, caplog, error_type, rpc_name, operator_instruction
):
    monkeypatch.setattr(telegram, "_unhealthy_clients", {})
    monkeypatch.setattr(telegram, "telegram_auth_key_unhealthy", False)
    monkeypatch.setattr(telegram, "telegram_auth_key_failure_reason", None)
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

    assert client.calls == 1
    assert not telegram.is_client_healthy(client)
    assert telegram.telegram_auth_key_unhealthy is True
    assert error_type.__name__ in telegram.get_telegram_health_failure()
    assert operator_instruction in caplog.text
    assert "Do not delete session files automatically" in caplog.text or (
        error_type is AuthKeyDuplicated
    )


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

    monkeypatch.setattr(telegram, "_unhealthy_clients", {})
    monkeypatch.setattr(telegram, "telegram_auth_key_unhealthy", False)
    monkeypatch.setattr(telegram, "telegram_auth_key_failure_reason", None)
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
