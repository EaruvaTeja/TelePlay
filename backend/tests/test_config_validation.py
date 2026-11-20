import pytest
from pydantic import ValidationError

from app.config import Settings


def _base(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "unit-test-secret-" + "x" * 40)
    monkeypatch.setenv("AUTH_USERS", "123456789")


def test_short_jwt_secret_rejected(monkeypatch):
    _base(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "too-short")
    with pytest.raises(ValidationError):
        Settings()


def test_placeholder_jwt_secret_rejected(monkeypatch):
    _base(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "your-super-secret-key-change-in-production")
    with pytest.raises(ValidationError):
        Settings()


def test_empty_auth_users_rejected(monkeypatch):
    _base(monkeypatch)
    monkeypatch.setenv("AUTH_USERS", "")
    with pytest.raises(ValidationError):
        Settings()


def test_malformed_auth_users_rejected(monkeypatch):
    _base(monkeypatch)
    monkeypatch.setenv("AUTH_USERS", "abc,def")
    with pytest.raises(ValidationError):
        Settings()


def test_valid_settings_ok(monkeypatch):
    _base(monkeypatch)
    s = Settings()
    assert s.auth_users == [123456789]


def test_telegram_proxy_settings_default_to_disabled(monkeypatch):
    _base(monkeypatch)
    for name in (
        "TELEGRAM_PROXY_SCHEME",
        "TELEGRAM_PROXY_HOST",
        "TELEGRAM_PROXY_PORT",
        "TELEGRAM_PROXY_USERNAME",
        "TELEGRAM_PROXY_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)

    s = Settings()

    assert s.telegram_proxy_scheme == "socks5"
    assert s.telegram_proxy_host == ""
    assert s.telegram_proxy_port == ""
    assert s.telegram_proxy_username == ""
    assert s.telegram_proxy_password == ""


def test_telegram_proxy_settings_load_from_environment(monkeypatch):
    _base(monkeypatch)
    monkeypatch.setenv("TELEGRAM_PROXY_SCHEME", "socks5")
    monkeypatch.setenv("TELEGRAM_PROXY_HOST", "127.0.0.1")
    monkeypatch.setenv("TELEGRAM_PROXY_PORT", "40000")
    monkeypatch.setenv("TELEGRAM_PROXY_USERNAME", "user")
    monkeypatch.setenv("TELEGRAM_PROXY_PASSWORD", "password")

    s = Settings()

    assert s.telegram_proxy_scheme == "socks5"
    assert s.telegram_proxy_host == "127.0.0.1"
    assert s.telegram_proxy_port == "40000"
    assert s.telegram_proxy_username == "user"
    assert s.telegram_proxy_password == "password"


@pytest.mark.parametrize("scheme", ["socks5", "socks4", "http"])
@pytest.mark.parametrize("port", ["1", "65535"])
def test_telegram_proxy_accepts_supported_schemes_and_port_bounds(monkeypatch, scheme, port):
    _base(monkeypatch)
    monkeypatch.setenv("TELEGRAM_PROXY_HOST", "127.0.0.1")
    monkeypatch.setenv("TELEGRAM_PROXY_SCHEME", scheme)
    monkeypatch.setenv("TELEGRAM_PROXY_PORT", port)

    settings = Settings()

    assert settings.telegram_proxy_scheme == scheme
    assert settings.telegram_proxy_port == port


@pytest.mark.parametrize("port", ["", "abc", "0", "-1", "65536"])
def test_telegram_proxy_rejects_invalid_port_when_host_is_set(monkeypatch, port):
    _base(monkeypatch)
    monkeypatch.setenv("TELEGRAM_PROXY_HOST", "127.0.0.1")
    monkeypatch.setenv("TELEGRAM_PROXY_SCHEME", "socks5")
    monkeypatch.setenv("TELEGRAM_PROXY_PORT", port)

    with pytest.raises(ValidationError, match="TELEGRAM_PROXY_PORT"):
        Settings()


def test_telegram_proxy_rejects_unsupported_scheme_when_host_is_set(monkeypatch):
    _base(monkeypatch)
    monkeypatch.setenv("TELEGRAM_PROXY_HOST", "127.0.0.1")
    monkeypatch.setenv("TELEGRAM_PROXY_SCHEME", "ftp")
    monkeypatch.setenv("TELEGRAM_PROXY_PORT", "1080")

    with pytest.raises(ValidationError, match="TELEGRAM_PROXY_SCHEME"):
        Settings()