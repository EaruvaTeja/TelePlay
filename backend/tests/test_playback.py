"""T3 — Session & Playback Core.

SYNC tests only (this repo has NO asyncio_mode config): async router calls go
through asyncio.run(...) inside sync tests, exactly like
test_stream_cache_auth.py / test_schema_migration.py. No DB, no Telegram:
every test uses a LOCAL PlaybackLimiter with an injectable fake clock, and
router tests monkeypatch app.routers.auth.limiter with a fresh instance.
"""
import asyncio
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest

from app.auth import verify_stream_token
from app.playback import PlaybackLimiter


# ─────────────────────────── helpers ─────────────────────────────────────────

class Clock:
    """Injectable monotonic-style fake clock for slot/TTL behaviour."""

    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, delta: float) -> None:
        self.now += delta


def make_limiter(max_devices: int = 2, ttl: float = 75.0) -> tuple[PlaybackLimiter, Clock]:
    clk = Clock()
    return PlaybackLimiter(max_devices=max_devices, ttl=ttl, clock=clk), clk


def start(lim, device, *, owner=None, role="admin", file_id=1, **kw):
    return lim.start(device, f"Dev {device}", role, file_id, owner_id=owner, **kw)


# ─────────────────────────── 1–2: slot cap ───────────────────────────────────

def test_two_devices_ok_third_refused():
    lim, _ = make_limiter(max_devices=2)
    assert start(lim, "A", owner=1)[0] is True
    assert start(lim, "B", owner=1)[0] is True
    ok, active = start(lim, "C", owner=1)
    assert ok is False
    assert len(lim.active()) == 2
    assert len(active) == 2


def test_restart_same_device_does_not_consume_second_slot():
    lim, _ = make_limiter(max_devices=2)
    assert start(lim, "A", owner=1)[0] is True
    assert start(lim, "B", owner=1)[0] is True
    # Re-starting A while the cap is full must succeed (same device, same slot).
    ok, active = start(lim, "A", owner=1, file_id=2)
    assert ok is True
    assert len(lim.active()) == 2
    assert lim.get("A").file_id == 2


def test_playback_start_rejects_cross_owner_device_id_reuse_with_409(monkeypatch):
    from fastapi import HTTPException

    from app.routers import playback as playback_router
    from app.schemas import PlaybackStartIn

    async def fake_get_meta(file_id):
        return object()

    monkeypatch.setattr(playback_router, "get_meta", fake_get_meta)
    lim, _ = make_limiter()
    monkeypatch.setattr(playback_router, "limiter", lim)
    body = PlaybackStartIn(
        file_id=1,
        device_id="shared-device-id",
        device_label="Shared Device",
    )
    owner_a = SimpleNamespace(id=1, role="admin", auth_version=0)
    owner_b = SimpleNamespace(id=2, role="admin", auth_version=0)

    asyncio.run(playback_router.start_playback(body, current_user=owner_a))
    before = lim.get(body.device_id)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(playback_router.start_playback(body, current_user=owner_b))

    assert exc_info.value.status_code == 409
    assert lim.get(body.device_id) is before
    assert lim.get(body.device_id).owner_id == owner_a.id
    assert lim.heartbeat(body.device_id, owner_id=owner_a.id) is True


# ─────────────────────────── 3–4: TTL & stop ─────────────────────────────────

def test_heartbeat_refreshes_and_ttl_expiry_frees_slot():
    lim, clk = make_limiter(max_devices=1, ttl=75.0)
    assert start(lim, "A", owner=1)[0] is True
    clk.advance(50)
    assert lim.heartbeat("A") is True
    # last_seen was refreshed at t+50; 60 more (< ttl) keeps it alive...
    clk.advance(60)
    assert lim.is_active("A") is True
    # ...but crossing the ttl without a heartbeat frees the slot.
    clk.advance(20)
    assert lim.is_active("A") is False
    assert len(lim.active()) == 0
    assert start(lim, "B", owner=1)[0] is True


def test_stop_frees_slot_without_revoking():
    lim, _ = make_limiter(max_devices=1)
    assert start(lim, "A", owner=1)[0] is True
    assert lim.stop("A", owner_id=1) is True
    assert lim.is_active("A") is False
    # No revocation floor was set: immediate re-start works, media path too.
    assert start(lim, "A", owner=1)[0] is True
    ok, _ = start(lim, "A", owner=1, issued_at=lim.get("A").issued_at, reactivate=False)
    assert ok is True
    assert lim._revoked_before == {}


# ─────────────────────────── 5, 7: kick semantics ────────────────────────────

def test_kick_refuses_media_path_start_with_old_issued_at():
    lim, _ = make_limiter(max_devices=2)
    assert start(lim, "A", owner=1)[0] is True
    lim.kick("A")
    assert lim.is_active("A") is False
    old_iat = lim._revoked_before["A"] - 10.0
    ok, _ = start(lim, "A", owner=1, issued_at=old_iat, reactivate=False)
    assert ok is False
    assert lim.is_active("A") is False


def test_after_kick_media_path_start_with_newer_issued_at_allowed():
    lim, _ = make_limiter(max_devices=2)
    assert start(lim, "A", owner=1)[0] is True
    lim.kick("A")
    new_iat = lim._revoked_before["A"] + 5.0
    ok, _ = start(lim, "A", owner=1, issued_at=new_iat, reactivate=False)
    assert ok is True
    assert lim.is_active("A") is True
    # The session recorded that generation; heartbeats survive the old floor.
    assert lim.heartbeat("A") is True


# ─────────────────────── 6: ★ P0 REGRESSION (13h lockout) ────────────────────

def test_p0_kick_reactivate_heartbeat_survives():
    """kick -> start(reactivate=True) -> FIRST heartbeat True -> stays True.

    Before the T3 fix, heartbeat() called is_revoked(device_id) with no
    generation, so any existing floor killed even a freshly-minted session:
    the kicked device could never play again until the floor aged out (~13h).
    """
    lim, _ = make_limiter(max_devices=2)
    assert start(lim, "A", owner=1)[0] is True
    lim.kick("A")
    ok, _ = start(lim, "A", owner=1, reactivate=True)
    assert ok is True
    assert lim.heartbeat("A", owner_id=1) is True   # FIRST heartbeat after kick
    for _ in range(5):
        assert lim.heartbeat("A", owner_id=1) is True  # no delayed lockout
    assert lim.is_active("A") is True


# ─────────────────── 8: same-whole-second kick + fresh start ─────────────────

def test_same_second_kick_then_fresh_start_survives(monkeypatch):
    import app.playback as pb

    lim, _ = make_limiter(max_devices=2)
    assert start(lim, "A", owner=1)[0] is True

    base = 1_700_000_000.5  # mid-second wall clock
    monkeypatch.setattr(pb.time, "time", lambda: base)
    lim.kick("A")                       # floor = float(int(base)) = 1700000000.0
    assert lim._revoked_before["A"] == float(int(base))  # integer-granularity floor

    # Fresh authenticated start minted in the SAME whole second: iat == floor.
    ok, _ = start(lim, "A", owner=1, reactivate=True)
    assert ok is True
    assert lim.heartbeat("A", owner_id=1) is True
    # And a media-path re-register whose iat equals the floor also survives.
    assert lim.heartbeat("A", owner_id=1, issued_at=float(int(base))) is True


# ─────────────────────────── 9–11: owner scoping ─────────────────────────────

def test_owner_isolation_heartbeat_and_stop():
    lim, _ = make_limiter(max_devices=2)
    assert start(lim, "A", owner=1)[0] is True
    # Another account cannot kill it — and the session SURVIVES both attempts.
    assert lim.heartbeat("A", owner_id=2) is False
    assert lim.is_active("A") is True
    assert lim.stop("A", owner_id=2) is False
    assert lim.is_active("A") is True
    # The real owner still works.
    assert lim.heartbeat("A", owner_id=1) is True
    assert lim.stop("A", owner_id=1) is True
    assert lim.is_active("A") is False


def test_stop_owner_removes_only_that_owner():
    lim, _ = make_limiter(max_devices=3)
    assert start(lim, "A", owner=1)[0] is True
    assert start(lim, "B", owner=1)[0] is True
    assert start(lim, "C", owner=2)[0] is True
    lim.stop_owner(1)
    assert lim.is_active("A") is False
    assert lim.is_active("B") is False
    assert lim.is_active("C") is True   # other owner untouched


def test_stop_role_still_drops_guest_sessions():
    """bot.py /guest contract: stop_role('guest') must keep working."""
    lim, _ = make_limiter(max_devices=3)
    assert start(lim, "A", owner=1, role="admin")[0] is True
    assert start(lim, "B", owner=9, role="guest")[0] is True
    assert start(lim, "C", owner=9, role="guest")[0] is True
    lim.stop_role("guest")
    assert lim.is_active("A") is True
    assert lim.is_active("B") is False
    assert lim.is_active("C") is False


def test_playback_start_mints_family_version_with_user_id(monkeypatch):
    from app.routers import playback as playback_router
    from app.schemas import PlaybackStartIn

    async def fake_get_meta(file_id):
        return object()

    monkeypatch.setattr(playback_router, "get_meta", fake_get_meta)
    lim, _ = make_limiter()
    monkeypatch.setattr(playback_router, "limiter", lim)
    user = SimpleNamespace(id=42, role="admin", auth_version=9)
    body = PlaybackStartIn(
        file_id=1,
        device_id="family-device",
        device_label="Family TV",
    )

    result = asyncio.run(playback_router.start_playback(body, current_user=user))
    token = parse_qs(urlparse(result.stream_url).query)["t"][0]
    claims = verify_stream_token(token, 1)

    assert claims["uid"] == user.id
    assert claims["ver"] == user.auth_version
    assert lim.get("family-device").owner_id == user.id


def test_playback_start_keeps_guest_version_claim_without_family_ver(monkeypatch):
    from app.routers import playback as playback_router
    from app.schemas import PlaybackStartIn

    async def fake_get_meta(file_id):
        return object()

    async def fake_guest_state():
        return SimpleNamespace(enabled=True, version=6)

    monkeypatch.setattr(playback_router, "get_meta", fake_get_meta)
    monkeypatch.setattr(playback_router, "get_guest_state", fake_guest_state)
    lim, _ = make_limiter()
    monkeypatch.setattr(playback_router, "limiter", lim)
    user = SimpleNamespace(id=99, role="guest")
    body = PlaybackStartIn(
        file_id=1,
        device_id="guest-device",
        device_label="Guest TV",
    )

    result = asyncio.run(playback_router.start_playback(body, current_user=user))
    token = parse_qs(urlparse(result.stream_url).query)["t"][0]
    claims = verify_stream_token(token, 1)

    assert claims["gv"] == 6
    assert "ver" not in claims
    assert claims["uid"] == user.id


# ─────────────────────────── router-level tests ──────────────────────────────

def _fake_request(device_id):
    headers = {"x-device-id": device_id} if device_id else {}
    return SimpleNamespace(headers=headers)


def test_logout_is_owner_scoped(monkeypatch):
    from app.routers import auth as ar

    lim, _ = make_limiter(max_devices=3)
    monkeypatch.setattr(ar, "limiter", lim)
    assert start(lim, "devA", owner=1)[0] is True   # owned by user id 1
    assert start(lim, "devZ", owner=2)[0] is True   # another account

    # Owner B calls logout with device A's id: refused by owner check, but
    # ALWAYS 204 and deviceA's session SURVIVES.
    req = _fake_request("devA")
    user_b = SimpleNamespace(id=2, role="admin")
    resp = asyncio.run(ar.logout(req, current_user=user_b))
    assert resp.status_code == 204
    assert lim.is_active("devA") is True

    # Owner A calls logout for their own device: slot released.
    user_a = SimpleNamespace(id=1, role="admin")
    resp = asyncio.run(ar.logout(req, current_user=user_a))
    assert resp.status_code == 204
    assert lim.is_active("devA") is False
    assert lim.is_active("devZ") is True            # other account untouched

    # No device header: still 204, nothing changes.
    resp = asyncio.run(ar.logout(_fake_request(None), current_user=user_a))
    assert resp.status_code == 204


def test_logout_all_stops_only_callers_and_bumps_version(monkeypatch):
    from app.routers import auth as ar

    lim, _ = make_limiter(max_devices=3)
    monkeypatch.setattr(ar, "limiter", lim)
    assert start(lim, "devA", owner=1)[0] is True
    assert start(lim, "devB", owner=1)[0] is True
    assert start(lim, "devC", owner=2)[0] is True

    commits = []

    class StubDB:
        def add(self, obj):
            pass

        async def commit(self):
            commits.append(True)

    user = SimpleNamespace(id=1, role="admin", auth_version=0)
    result = asyncio.run(ar.logout_all(current_user=user, db=StubDB()))
    assert result == {"message": "All sessions have been invalidated"}
    assert user.auth_version == 1
    assert commits == [True]
    assert lim.is_active("devA") is False
    assert lim.is_active("devB") is False
    assert lim.is_active("devC") is True            # other owner survives
    # stop_owner does NOT revoke — floors untouched.
    assert lim._revoked_before == {}


@pytest.fixture
def playback_count_api():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.routers import playback as playback_router

    api = FastAPI()
    api.include_router(playback_router.router, prefix="/api")
    client = TestClient(api)
    yield api, client, playback_router
    client.close()


@pytest.mark.parametrize(
    ("role", "user_id"),
    [("guest", 101), ("admin", 202)],
)
def test_playback_count_returns_household_count_for_any_authenticated_user(
    playback_count_api, monkeypatch, role, user_id
):
    from types import SimpleNamespace

    api, client, playback_router = playback_count_api
    lim, _ = make_limiter(max_devices=3)
    monkeypatch.setattr(playback_router, "limiter", lim)
    lim.start("guest-device", "Guest phone", "guest", 1, owner_id=101)
    lim.start("family-device", "Family TV", "admin", 2, owner_id=202)
    user = SimpleNamespace(id=user_id, role=role)
    api.dependency_overrides[playback_router.get_current_user] = lambda: user

    response = client.get("/api/playback/count")

    assert response.status_code == 200
    assert set(response.json()) == {"active", "limit"}
    assert response.json() == {"active": 2, "limit": lim.max_devices}


def test_playback_count_purges_expired_sessions(playback_count_api, monkeypatch):
    api, client, playback_router = playback_count_api
    lim, clock = make_limiter(max_devices=3, ttl=75)
    monkeypatch.setattr(playback_router, "limiter", lim)
    lim.start("stale-device", "Stale phone", "guest", 1, owner_id=101)
    clock.advance(76)
    api.dependency_overrides[playback_router.get_current_user] = lambda: SimpleNamespace(
        id=101,
        role="guest",
    )

    response = client.get("/api/playback/count")

    assert response.status_code == 200
    assert response.json() == {"active": 0, "limit": lim.max_devices}


def test_playback_count_requires_authentication(playback_count_api):
    from app.database import get_db

    api, client, _ = playback_count_api

    async def unused_db():
        yield None

    api.dependency_overrides[get_db] = unused_db

    response = client.get("/api/playback/count")

    assert response.status_code == 401
