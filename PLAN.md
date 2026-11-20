# Hearth — Deploy-Run Plan (v2, re-baselined 2026-11-19)

**Audited code baseline:** `84926670051242bbbcd5afae378aa6f319ded062` (T1–T12 complete).
**Goal:** production launch 2026-11-19 on free tiers (NeoHeberg 512MB Debian VPS + Neon + Cloudflare Pages + DuckDNS + Caddy). Fallback: owner-only soft launch. Never skip P0 gates for the date.
Task IDs continue the repo's T-numbering (T12.1 and T16 are new). One task = one branch = one Copilot prompt = ONE final commit = one owner-merged PR.

## Constraints & Rules (apply to every task)
* **Frozen:** `web/src/components/MediaPlayer.tsx` byte-identical for T12.4 onward; the one-time T12.3 owner-authorized SPEEDS exception is closed. Two additional owner-authorized mobile-only exceptions are T12.86 (auto-landscape) and T12.87 (tap=controls, center=play/pause); each freezes independently after implementation, and TV/PC behavior remains byte-identical in behavior. Preserve its imports (`TelegramFile`, `formatDuration`, `useUpdateProgress`, `useFile`, `api`, `useAppStore`) and keys `hearth_player_prefs`, `hearth_device_id`.
* **Non-goals:** Android, folders, search, multi-select, rename/move, QR, public links, transcoding, Redis, Docker, SQLite, helper bots, Alembic (today), broad dependency upgrades.
* **Sanitizer notice:** filename sanitizer and `escape_like` are CORRECT — never alter or "repair".
* One Uvicorn worker; Python 3.13 (Debian 13 native; decision in HANDOFF); Node 20; `npm ci`; pinned `requirements.txt`.
* Playback cap is **household-wide 2** (already implemented — do not change the limiter).
* Full operating rules: see `HANDOFF.md`. Agent never creates/merges PRs; owner merges.

## Execution Map (order is mandatory)

| # | Task | Executor | Deliverable | Commit message |
|---|------|----------|-------------|----------------|
| 0 | Docs re-baseline | Owner | HANDOFF/PLAN/PROGRESS v2 on main | `PLAN: re-baseline deploy run (T12.1→T16) — docs only` |
| R | Reachability preflight | Owner | IPv4/IPv6 answer in PROGRESS Readiness | (no commit; recorded by next task) |
| 1 | T12.1 | Agent | Audit report + surgical fixes + tests | `T12.1: Pre-deploy audit & workflow fixes — gate passed` |
| 2 | T13 | Agent | deploy/ kit + README/docs rewrite | `T13: Production Deployment Kit & Runbooks — gate passed` |
| 3 | T14 | Agent | Fresh gates + hygiene + tag v1.0-rc | `T14: Comprehensive Test Suite & Final Hygiene — gate passed` |
| 4 | T0 | Owner (agent assists) | Verified backups BEFORE first boot | `T0: Backups verified — evidence recorded` |
| 5 | T15 | Owner (agent assists) | VPS+Pages deploy + acceptance evidence | `T15: Real-World Hardware Acceptance — evidence recorded` |
| 6 | T16 | Owner (agent assists) | GO decision + 72h observation log | `T16: Launch & 72-hour observation — GO recorded` |

### 2026-11-20 post-incident execution map (T12.81–T12.92)

| Task | Scope |
|---|---|
| T12.81 | Enforce family stream-token revocation with version claims and User.id identity. |
| T12.82 | Re-baseline, A-item ownership, and execution-state reconciliation. |
| T12.83 | Re-opened F-01 stream identity: bind token file/device/owner consistently. |
| T12.84 | Re-opened F-02 source of truth: enforce `family_members` for family membership. |
| T12.85 | Re-opened F-02 verify-code: remove static-`AUTH_USERS`/mint-admin bypass. |
| T12.86 | OWNER-AUTHORIZED MediaPlayer exception #2: mobile-only auto-landscape. |
| T12.87 | OWNER-AUTHORIZED MediaPlayer exception #3: mobile-only tap controls/center play-pause. |
| T12.88 | Mobile/TV/PC parity and final `MediaPlayer.tsx` freeze. |
| T12.89 | Post-incident auth/origin closure; A-item tracking and security gates. |
| T12.90 | GitHub origin/live `deploy-T12.7` provenance and release consistency. |
| T12.91 | Stale bundle and VPS disk/RAM recovery; incident A-item tracking. |
| T12.92 | Final freeze plus T0-R, T15-R, and T16-R gate reruns before handoff. |

---

## Historical — T1–T12 (COMPLETE at baseline; do not redo)

T1 deps/env template · T2 schema truth (String(10), guest default, family_members, idempotent init_db, SQLite rejection) · T3 playback core (issued_at, kick fix, owner-scoped logout) · T4 Telegram client safety (clients[:], bounded FloodWait) · T5 bot management surface (callback gate, /help, /users, /user_add, /user_remove, /sessions, /kick, /guest) · T6 media security (nosniff/CSP/disposition, family ver+membership, slowapi removed) · T7 files ops (ON CONFLICT progress, honest batch delete, newest-first) · T8 web contracts (logout=this-device, fail-closed useMe, 429/409, store role unknown) · T9 keypad/deep-links/cooldowns (8/6, QR removed) · T10 FileBrowser/Manage exit + DeleteConfirm (Cancel default) · T11 context menu/device ID/toasts · T12 toolchain + dead-file deletion. Original per-task detail lives in git history at the baseline SHA.

---

## T12.1 — Pre-deploy Audit & Surgical Workflow Fixes

**Branch:** `hearth/t12.1` from main. **Files (exact):**
* `backend/app/main.py` — F1: gate sync task creation with `if settings.sync_on_startup:` (else log "startup sync disabled"); shutdown already tolerates no task.
* `backend/app/bot.py` — F2: `sync_with_channel()` safety guard: if rows exist and NO message is alive, or >30% of rows would be deleted → log warning, delete NOTHING, return 0. Keep `/sync` working. F3: make `/help` perfect: list every registered command (`/start /help /web /login /logout_all /sync /myfiles /file /users /user_add /user_remove /sessions /kick /guest` + `status|off`), mark owner-only vs family, add TTLs ("family code: 5 min, one-time", "guest PIN: 24 h"), fix supported-files block (photos are REJECTED — videos/audio/documents ≤2 GB), note "guests: watch-only".
* `backend/scripts/gate4_check.py` — F4: help text 6→**8-digit** family code from `/login` (request contract already correct).
* `backend/scripts/smoke_db.py` — F5: remove duplicate imports/docstring (cosmetic).
* `backend/tests/` — add: sync flag off → no sync task/call; guard aborts mass-gone without deleting; `/help` lists all commands. Extend existing files (or one new test file). Never weaken existing tests.
* `AUDIT_REPORT.md` (NEW, repo root) — record the 2026-11-19 static audit at baseline: commit/date/auditor, executive summary, critical issues (= pre-fix F1–F5 state), verification tables (T12 deletions all DELETED; no broken imports; backend/frontend contracts verified; 120 tests; security scan clean; PROGRESS state), recommendation "PROCEED AFTER T12.1", next steps.
* `PROGRESS.md` — tick T12.1, Current Task → T13, log line; record Phase R answer if owner provided it.
* T12.1 file list: append "(+ HANDOFF/PLAN/PROGRESS environment deltas per owner instruction 2026-11-19)".

**Do NOT touch:** anything else. No frontend changes. MediaPlayer untouched. Do not "fix" Verified Baseline Facts (HANDOFF).
**Gate:** full `pytest -q` (≥120 + new, all green) · `compileall -q app` · `npm ci && npm run lint && npm run typecheck && npm test && npm run build` (prove no regression) · MediaPlayer diff empty.
**Commit:** `T12.1: Pre-deploy audit & workflow fixes — gate passed`

## T13 — Production Deployment Kit & Runbooks

**Branch:** `hearth/t13` from main (after T12.1 merge). **NO application code changes.**
**Files to CREATE (canonical content below — after this task, `deploy/*` is the source of truth):**

### deploy/hearth.service
```ini
[Unit]
Description=Hearth Media Streaming Service
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=hearth
Group=hearth
WorkingDirectory=/opt/hearth/app/backend
EnvironmentFile=/etc/hearth/hearth.env
ExecStart=/opt/hearth/app/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
UMask=0077
# 512MB box: throttle early, hard-cap below total RAM. Tune ONLY after T15 measurement.
MemoryHigh=350M
MemoryMax=400M
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/hearth/session

[Install]
WantedBy=multi-user.target
```

### deploy/Caddyfile (replace hostname at deploy time)
```caddyfile
your-domain.duckdns.org {
    # Never log signed stream URLs (?t=)
    @stream path /api/stream/*
    skip_log @stream

    # Health is loopback-only (SSH: curl 127.0.0.1:8000/health/ready)
    @health path /health /health/ready
    respond @health 404

    reverse_proxy 127.0.0.1:8000 {
        flush_interval -1
        header_up X-Real-IP {remote_host}
    }

    header {
        Strict-Transport-Security "max-age=31536000"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "no-referrer"
        -Server
    }

    log {
        output file /var/log/caddy/hearth.log {
            roll_size 10mb
            roll_keep 5
        }
        format json
    }
}
```

### deploy/backup-neon.sh (chmod +x; pg_dump needs DIRECT endpoint + client ≥ server major)
```bash
#!/usr/bin/env bash
set -euo pipefail
umask 077
OUT="${1:-/var/backups/hearth}"
TS="$(date -u +%Y%m%d_%H%M%S)"
mkdir -p "$OUT"
if [ -z "${DATABASE_URL:-}" ]; then
  [ -f /etc/hearth/hearth.env ] || { echo "ERROR: DATABASE_URL unset, no env file"; exit 1; }
  set -a; . /etc/hearth/hearth.env; set +a
fi
PG_URL="${DATABASE_URL/postgresql+asyncpg:/postgresql:}"
PG_URL="${PG_URL/-pooler./.}"     # pg_dump must use the DIRECT (non-pooler) host
PG_URL="${PG_URL%%\?*}"
export PGSSLMODE=require
FILE="$OUT/hearth_${TS}.sql.gz"
echo "Dumping Neon -> $FILE"
pg_dump "$PG_URL" --format=plain --no-owner --no-privileges | gzip > "$FILE"
gzip -t "$FILE"
gunzip -c "$FILE" | tail -n 5 | grep -q "PostgreSQL database dump complete" \
  || { echo "ERROR: incomplete dump"; exit 1; }
echo "OK: $FILE ($(du -h "$FILE" | cut -f1))"
echo "Restore: gunzip -c FILE | psql 'DIRECT postgresql:// URL'"
```

### deploy/duckdns-update.sh (chmod +x; token lives in /etc/hearth/duckdns.env, 0600 root)
```bash
#!/usr/bin/env bash
set -euo pipefail
umask 077
. /etc/hearth/duckdns.env   # DUCKDNS_DOMAIN=your-domain  DUCKDNS_TOKEN=xxx
EXTRA=""
# IPv6-only VPS (Phase R case 2): uncomment
# EXTRA="&ipv6=$(curl -6 -fsS https://api64.ipify.org)"
resp="$(curl -fsS "https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&ip=${EXTRA}")"
[ "$resp" = "OK" ] || { echo "DuckDNS failed: $resp"; exit 1; }
```

### deploy/README.md — full runbook containing, in order:
1. Prerequisites + Phase R reachability gate (IPv4 vs IPv6 decision tree from HANDOFF).
2. VPS prep: `sudo apt install -y python3 python3-venv python3-dev build-essential git curl ca-certificates caddy ufw`; PGDG supports trixie; install `postgresql-client-<major matching Neon server>` (17 or 18 — check the Neon console). Create the venv with `python3 -m venv .venv`; replace any python3.11 commands in this runbook text.
3. Checkout RELEASE_SHA (`git checkout --detach <SHA>`; `git rev-parse HEAD` must match); venv + pinned install + `pip check`.
4. `/etc/hearth/hearth.env` template (0640 root:hearth): TELEGRAM_API_ID/API_HASH/BOT_TOKEN/STORAGE_CHANNEL_ID, AUTH_USERS (owner FIRST), JWT_SECRET (`secrets.token_hex(32)`), DATABASE_URL (pooled `postgresql+asyncpg://…-pooler…?sslmode=require`), WEB_BASE_URL + CORS_ORIGINS (exact Pages origin), TELEGRAM_SESSION_DIR=/var/lib/hearth/session, SERVER_HOST=127.0.0.1, SERVER_PORT=8000, LOG_LEVEL=INFO, MAX_PLAYBACK_DEVICES=2, PLAYBACK_HEARTBEAT_SECONDS=20, PLAYBACK_SESSION_TTL_SECONDS=75, TELEGRAM_CLIENT_CONCURRENCY=2, SYNC_ON_STARTUP=false, SYNC_BATCH_SIZE=100, GUEST_PIN_HOURS=24, LOGIN_ATTEMPT_LIMIT=5, LOGIN_ATTEMPT_WINDOW_SECONDS=3600, TELEGRAM_HELPER_BOT_TOKENS= (empty).
5. T0 backups BEFORE first boot (run backup-neon.sh, verify, copy off-VPS; session tar if exists; restore procedure).
6. DB smoke (`scripts/smoke_db.py` with env loaded → `SELECT 1 -> 1`); install unit; `enable --now hearth`; first boot runs init_db DDL (backed up) with sync OFF; journal watch.
7. Caddy: replace hostname → `/etc/caddy/Caddyfile`; `caddy validate` THEN reload; ufw allow 22,80,443/tcp only; DuckDNS env+script+root cron `*/5 * * * *`.
8. Cloudflare Pages: root `web`, build `npm ci && npm run build`, output `dist`, Node 20, `VITE_API_URL=https://<domain>.duckdns.org/api`, production branch main at RELEASE_SHA; `_redirects` present; no secrets in Pages.
9. Smoke: loopback `/health/ready` 200 (DB+Telegram true); public `/health` → 404; public `:8000` refused; Pages deep-refresh OK; no CORS errors; gate4 security check.
10. Monitoring (free -m, ps RSS, journal, Neon dashboard, egress), retention cron (`find /var/backups/hearth -name 'hearth_*.sql.gz' -mtime +30 -delete`), troubleshooting, rollback.

**Files to UPDATE:** root `README.md` (Hearth overview: web-only flat library, family/guest rules, household-wide 2 streams, TV-first; link deploy/README.md; REMOVE Android/Docker/SQLite/folders/Railway/Render instructions). Add "Historical — do not follow for this deployment" banner atop `docs/DEPLOYMENT.md`, `docs/SETUP.md`, `docs/ARCHITECTURE.md`. `PROGRESS.md`.
**Gate:** `bash -n` on both scripts (or documented review if bash unavailable); `caddy validate` + `systemd-analyze verify` if available, else static review (live validation mandatory in T15); `git diff` shows ZERO `backend/app/**` and `web/src/**` changes; runbook env keys match `config.py` exactly.
**Commit:** `T13: Production Deployment Kit & Runbooks — gate passed`

## T14 — Comprehensive Test Suite & Final Hygiene (freeze the release)

**Branch:** `hearth/t14` from main (after T13 merge). Run everything from a CLEAN checkout:
```
cd backend && python3.13 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q            # record exact count
.venv/bin/python -m compileall -q app
.venv/bin/pip check && .venv/bin/pip freeze   # record summary
cd ../web && npm ci
npm run lint && npm run typecheck && npm test && npm run build
npm audit --omit=dev                     # review + record; NO audit fix --force
```
* Review Python advisories (python-jose 3.3.0, fastapi 0.115.5, …) — record, do NOT blind-upgrade.
* Production-interpreter gate: backend suite must ALSO pass on Python 3.13. If the dev machine lacks 3.13, record the version used and mark the 3.13 gate PENDING; it then runs at T15 entry on the VPS in a TEMP venv (requirements-dev.txt, full pytest -q) which is DELETED before the production venv/service goes live. Production venv stays runtime-only.
* Hygiene greps: no folder/QR/logout-all legacy artifacts in active code; `git ls-files` contains no `.env`/sessions/dumps/media; `dist/_redirects` exists; MediaPlayer byte-identical.
* Append "Fresh gate evidence" section to `AUDIT_REPORT.md` (commands, counts, versions, date, SHA tested).
* Tag `v1.0-rc` on the final commit. Report the SHA — **owner records it as RELEASE_SHA in PROGRESS → Deployment Readiness when merging.** Deploy only this SHA.
* `PROGRESS.md`: tick T14, Current Task → T0.
**Commit:** `T14: Comprehensive Test Suite & Final Hygiene — gate passed`

## T12.3 — Login message polish, 10 playback speeds, DB-outage 503

**Branch:** `hearth/t12.3` from merged T12.2. **Files (exact):**
* `web/src/App.tsx` — replace only the family and guest invalid/expired login messages with the requested help text.
* `web/src/components/MediaPlayer.tsx` — owner-authorized one-time exception: change only `SPEEDS` to `[0.5, 0.75, 1, 1.1, 1.2, 1.25, 1.35, 1.5, 1.75, 2]`; a minimal speed-chip layout change is allowed only if required to prevent overflow/clipping. Freeze resumes for subsequent tasks.
* `backend/app/main.py` — add a 503 handler only for SQLAlchemy `OperationalError`/`DBAPIError`, `socket.gaierror`, and `ConnectionError`/`OSError`; warning logs include only the exception class name.
* `backend/tests/` — test an authenticated route's DB-connection failure response and a successful normal request.
* `HANDOFF.md`, `PLAN.md`, `PROGRESS.md`, `AUDIT_REPORT.md` — record exception, task, progress, findings and fresh gate evidence.

Playback compatibility investigation is documentation-only; do not change playback implementation or add a device-compatibility badge without owner approval.

**Gate:** full backend pytest, `compileall -q app`, `pip check`; frontend `npm ci`, lint, typecheck, test, build; verify all ten speeds are accepted/persisted/applied and speed stepping fallback index 2 remains 1×; MediaPlayer diff limited to `SPEEDS` (+ optional minimal chip-row layout); `git diff --stat` limited to authorized files.
**Commit:** `T12.3: Login message polish, 10 playback speeds, DB-outage 503 — gate passed`

## T12.4 — DB-wake upload UX, status button, 503 guidance, stream cleanup

**Final version for 2026-11-19.** T12.5 was initially reserved for the owner's external review; the owner subsequently assigned it to the IPv6-only VPS connectivity fix below.

**Branch:** `hearth/t12.4` from merged T12.3. **Files (exact):**
* `backend/app/bot.py` — initialize upload `forwarded`, catch DB-connectivity failures from upload and `/start`, preserve Telegram compensation, and add an AUTH_USERS-authorized DB status callback before the existing DB-backed callback gate.
* `backend/app/streaming.py` — minimal producer cancellation/await cleanup and exception-retrieving done callback.
* `backend/tests/` — bot DB-wake and callback cases; stream early-close/disconnect cleanup regression.
* `web/src/lib/api.ts` — exact guidance for HTTP 503 or `SERVICE_UNAVAILABLE`.
* `web/src/lib/__tests__/api.test.ts` — 503 guidance regression case.
* `PLAN.md`, `PROGRESS.md`, `AUDIT_REPORT.md` — task, status, and fresh evidence.

`MediaPlayer.tsx` is frozen again. Do not change `main.py`, `App.tsx`, `FileBrowser.tsx`, auth, routers, or dependencies.

**Gate:** full backend pytest, `compileall -q app`, `pip check`; frontend `npm ci`, lint, typecheck, test, build; verify `_redirects`; MediaPlayer diff empty; `git diff --stat` limited to authorized files.
**Commit:** `T12.4: DB-wake upload UX + server status button + stream cleanup — gate passed`

## T12.4.1 — Frontend production dependency security patch

**Branch:** `hearth/t12.4.1` from merged T12.4 (`11bd4625936fc6fe81375285242f70d5b8ac660c`). **Files (exact):**
* `web/package-lock.json` — apply `npm audit fix --omit=dev` only; no force or major upgrades.
* `web/package.json` — only if the npm audit fix modifies it; review any diff and preserve major ranges.
* `PLAN.md`, `PROGRESS.md`, `AUDIT_REPORT.md` — task, status, dependency delta, reachability analysis, and gate evidence.

Do not change application code, backend requirements, deploy files, or frozen `MediaPlayer.tsx`. Keep axios on major 1 and verify it is above 1.19.0 and neither 1.14.1 nor 0.30.4; require follow-redirects above 1.15.11, form-data outside 4.0.0–4.0.5, and zero production advisories. The original T12.5 external-review reservation was superseded by the owner-directed IPv6 connectivity task below. Deployment/T0 remain ON HOLD pending merge, owner smoke tests, and release re-freeze.

**Gate:** baseline `npm ci`, package versions, and `npm audit --omit=dev`; `npm audit fix --omit=dev` without `--force`; verify versions and zero production audit findings; then fresh `npm ci`, lint, typecheck, test, build, `_redirects`, full backend pytest, `compileall -q app`, `pip check`, and empty MediaPlayer diff.
**Commit:** `T12.4.1: Patch axios/follow-redirects/form-data advisories — gate passed`

## T12.5 — IPv6-only VPS Telegram connectivity fix

**Branch:** `hearth/t12.5` from merged T12.4.1. **Files (exact):**
* `backend/app/telegram.py` — pass `ipv6=True` to Pyrogram `Client` in `create_client`, with a brief IPv6-only VPS compatibility comment.
* `PLAN.md`, `PROGRESS.md`, `AUDIT_REPORT.md` — record the task, status, root cause, and fresh gate evidence.

Do not change other application code, dependencies, deploy files, or secrets. T0/deployment remain ON HOLD until owner merge and release re-freeze.

**Gate:** full backend pytest, `compileall -q app`, `pip check`; `git diff --stat` limited to the four authorized files. Actual Telegram connectivity on the target IPv6-only VPS remains a post-merge owner verification.
**Commit:** `T12.5: Force IPv6 for Pyrogram Client on IPv6-only VPS — gate passed`

## T12.80 — Post-incident docs re-baseline

**Branch:** `hearth/t12.80` from latest `main`. **Files (exact):**
* `HANDOFF.md`
* `PLAN.md`
* `PROGRESS.md`
* `AUDIT_REPORT.md`

Record the T12.6/T12.7 incident outcome, re-open F-01/F-02 in the verified baseline, authorize only T12.86/T12.87 mobile MediaPlayer exceptions, register T12.81–T12.92, set Current Task to T12.81, and add fresh gate evidence. No application, test, dependency, deploy, or package file may change.

**Gate:** backend `.venv\Scripts\python -m pytest -q` · `.venv\Scripts\python -m compileall -q app` · `.venv\Scripts\pip check`; frontend `npm ci`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`, and `dist/_redirects`; `git diff --stat -- web/src/components/MediaPlayer.tsx` empty; exactly the four authorized documentation files changed.
**Commit:** `T12.80: Post-incident docs re-baseline, F-01/F-02 re-opened, mobile exceptions authorized — gate passed`

## T12.81 — Enforce family stream-token revocation

**Branch:** `hearth/t12.81` from latest `main`. **Files:** `backend/app/auth.py`, `backend/app/routers/playback.py`, `backend/app/routers/streaming.py`, `backend/tests/test_streaming_security.py`, `backend/tests/test_playback.py`, `backend/tests/test_stream_cache_auth.py` (owner-approved minimal dependent fixture update), `PLAN.md`, `PROGRESS.md`, `AUDIT_REPORT.md`.

Add keyword-only optional `ver` to stream tokens and include it when provided. Family playback passes `User.auth_version` while retaining `uid=User.id`; guest `gv` issuance stays unchanged. Before any cache or byte access, family streams require both claims, query User by primary key `id`, reject stale versions, and require an active `FamilyMember` for the user's Telegram ID. Keep the limiter owner ID as User.id. Replace mock-injected family claims with signed tokens and add TestClient regressions for family login/start/206, logout-all revocation including a warm cache, inactive-member revocation, and a signed admin token without `ver`. Preserve guest revocation and existing warm-cache 401 coverage.

**Gate:** full backend pytest, `compileall -q app`, and `pip check`; no weakened/deleted security tests. **VERIFY ON VPS:** confirm live `/auth/logout-all` and `/user_remove` invalidate already-issued media URLs.
**Commit:** `T12.81: Enforce family stream-token revocation (ver claim + uid identity, fail-closed) — gate passed`

The existing cache-auth test file was initially excluded by its byte-identical note. The owner explicitly approved updating only its valid-family-token fixture because the old fixture minted an admin token without the now-required claims; its 206, cached body, and cache-header assertions remain intact.

## T12.82 — Re-baseline and A-item execution ownership

**Scope:** reconcile the incident findings with the existing master execution order, freeze the post-incident release-state assumptions, and register A1/A2/A4/A5/A6/A7 as tracked rather than silently resolved. T12.89 and T12.91 own the implementation/recovery gates; all evidence remains labeled CONFIRMED, VERIFY ON VPS, or NOT VERIFIED.

## T12.83 — Family stream identity repair: file/device/owner binding

**Scope:** reopen F-01 only and repair stream-token identity so `create_stream_token` carries the required family version and `_auth_stream` resolves the same owner/device identity as `/playback/start`. Preserve auth-before-cache, the household-wide two-stream cap, guest `gv`, and existing exports.

## T12.84 — `family_members` membership source repair

**Scope:** reopen F-02 only and make family membership the single source of truth for media and family authorization. Static `AUTH_USERS` may authorize owner operations only where deliberately specified; it must not manufacture family membership or grant media identity.

## T12.85 — Verify-code role and membership hardening

**Scope:** remove the verify-code minting path that grants `role=admin` to an existing user without membership validation. Existing family members must receive the intended family role only after a live `family_members` check; unknown users remain fail-closed.

## T12.86 — OWNER-AUTHORIZED MediaPlayer exception #2: mobile auto-landscape

**Scope:** implement mobile-only automatic landscape behavior after a mobile device is confirmed. TV/PC behavior must remain byte-identical in behavior; preserve every `MediaPlayer.tsx` export and both `hearth_player_prefs` and `hearth_device_id` (`DEVICE_ID_KEY`). Freeze the player again immediately after this task.

## T12.87 — OWNER-AUTHORIZED MediaPlayer exception #3: mobile tap controls

**Scope:** implement mobile-only player tap-to-show-controls and center-button play/pause behavior. TV/PC behavior must remain byte-identical in behavior; preserve every `MediaPlayer.tsx` export and both localStorage keys. Freeze the player again immediately after this task.

## T12.88 — Mobile exception parity and final player freeze

**Scope:** verify both owner-authorized mobile exceptions independently of TV/PC behavior, confirm no export or localStorage-key change, and record `git diff --stat -- web/src/components/MediaPlayer.tsx` evidence for the final freeze. T12.88 is the gate for no further `MediaPlayer.tsx` changes.

## T12.89 — Post-incident auth and origin incident closure

**Scope:** track and close the incident items assigned here, including the family media identity/membership corrections for F-01/F-02 and incident A1/A2/A4/A5/A6/A7 work ownership where applicable. Re-run security tests, preserve all security invariants, and do not weaken or delete existing tests.

## T12.90 — GitHub origin and live deployment provenance

**Scope:** enforce GitHub as the deployment source of truth, re-point remaining release documentation to the live `deploy-T12.7` provenance, and verify the final tested SHA rather than the stale bundle. No application/dependency behavior change is allowed unless separately authorized.

## T12.91 — Stale bundle and VPS resource recovery

**Scope:** track and remediate the stale `/opt/hearth/hearth-v1.0-rc.bundle` at SHA `7629f0a`, disk 75% (3.0/4.0 GB), and RAM 210/512 MB. Record owner/VPs actions and evidence for the incident items assigned to this task, including bundle quarantine/removal or replacement and resource recovery.

## T12.92 — Final freeze, gate rerun, and handoff

**Scope:** after T12.81–T12.91, freeze the release and execute the final baseline: T0-R (backups reachability/recovery gate), T15-R (VPS/hardware acceptance gate), and T16-R (launch/72-hour readiness gate). Refresh audit evidence, update final SHA/release status, and prepare handoff for owner merge only.

## T0 — Verified Backups (OWNER, BEFORE first production boot; agent may assist)

Re-scoped: the old "before T2" wording is historical (dev schema work already gated). The hard boundary now is the FIRST boot against production Neon.
* Run `deploy/backup-neon.sh` (direct endpoint; client ≥ Neon major). Verify non-empty + "dump complete". **Copy off-VPS** (scp to your PC).
* Record Neon project/branch/region + row counts (users, family_members, files, login_codes, refresh_tokens, guest_credentials).
* Session dir: fresh install → nothing yet; back up after first boot. Existing deployment → tar + off-host, 0600. (Bot sessions re-auth from token if lost — still back up.)
* Write restore procedure (stop service → `gunzip -c | psql DIRECT_URL` → restart → reconcile) into `deploy/BACKUP_LOG.md` with evidence. Restore drill on a Neon branch = strongly recommended.
**Commit (docs-only):** `T0: Backups verified — evidence recorded` · PROGRESS: tick T0, Current Task → T15.

## T15 — Real-World Hardware Acceptance (OWNER on VPS + Samsung TV; agent assists)

Entry gate: Phase R answered; T0 verified; RELEASE_SHA frozen. Deploy per `deploy/README.md`, then record PASS/FAIL + measurements for EVERY row (P0 = all):
* [ ] Phase R reachability proven from the TV itself (A or AAAA path).
* [ ] Server-side Phase R — run `curl -4/-6` on the VPS, require global IPv6, update the DuckDNS AAAA record, then from the TV browser open `https://<domain>/health` and expect 404 (proves inbound reachability and proxy).
* [ ] Effective memory limit check — run `systemctl show hearth -p MemoryMax,MemoryHigh`; if infinity, the limit is host-enforced, note it and rely on monitoring.
* [ ] Firewall fallback — use ufw if supported, otherwise the provider firewall; in both cases, an external `:8000` refused test must pass.
* [ ] Clean VPS deployment step-by-step from runbook; `caddy validate` before reload.
* [ ] gate4 security gate: fresh 8-digit code → authorized range 206; **unauthorized warm-cache 401, zero bytes**.
* [ ] Forward disposable ~1GB MP4 (H.264+AAC) → appears FIRST in All videos; metadata correct.
* [ ] Play without full-file download; second play fast (head cache); seek start/middle/end; pause/resume.
* [ ] DB-failure compensation observed in staging (DB row retained/reported on Telegram delete failure).
* [ ] Family 8-digit + guest 6-digit login; **swapped inputs strictly rejected**.
* [ ] 5 wrong attempts → ~1h lockout message + keypad cooldown; resets after window/success.
* [ ] Two concurrent streams (1 family + 1 guest) OK; **3rd device → 409 popup + zero-byte transfer**.
* [ ] `/kick` → old stream URL dead immediately; fresh login works. `/users`, `/user_add`, `/user_remove` (removed member's tokens/streams die), `/sessions`, `/myfiles`, `/file <id>` delete, `/help` complete.
* [ ] Guest: Logout-only header; API delete → 403; `/guest off` kills stream instantly; 24h expiry live-confirmed next day (unit-covered today).
* [ ] Remote-only flow on TV: Login → Play → Pause → Resume → Seek → long-press OK → actions sheet → Close/Back exits → Manage → Delete → Cancel → Done → Logout. PC right-click sheet exits (Close/Esc/backdrop).
* [ ] Progress survives refresh; 95% rule keeps Continue Watching honest.
* [ ] MP4/H.264+AAC native on Tizen; MKV/HEVC honestly flagged.
* [ ] Delete test file → Telegram message + DB row gone consistently.
* [ ] CORS clean on Pages origin; HTTPS valid; public `:8000` refused; public `/health` 404; logs contain NO tokens/PINs/signed URLs.
* [ ] VPS reboot → systemd recovers; sessions reused; bot responds.
* [ ] RAM under 512MB during 2 streams (`free -m`, `ps -o rss,cmd -C python`, no OOM in journal). Tune Memory* only with evidence.
* [ ] Neon backup restored at least once (branch drill).
Record results in `PROGRESS.md` + `AUDIT_REPORT.md`. **Commit:** `T15: Real-World Hardware Acceptance — evidence recorded`

## T16 — Launch & 72-Hour Observation (OWNER)

* GO only if: backups verified · gates green at RELEASE_SHA · security gate 401 · Pages+CORS+HTTPS working · Phase R proven on TV · all T15 P0 rows PASS · RAM/egress acceptable. Else owner-only soft launch + fix + re-gate.
* Invite intended family (owner first). Update Master Review MD: audited SHA → RELEASE_SHA, decision → GO with evidence.
* First 30 min: loopback health, no restart loop, cert valid, login/upload/play/seek, 401 unauth, 8000 closed.
* Daily ×3: journals, Neon connections/compute, VPS RAM/CPU/disk/**egress** (~1GB per full watch — every relayed byte counts), FloodWait check, guest-24h live confirm, post-deploy Neon export, backup artifact readable.
* No refactors/upgrades during observation unless security/availability demands. Tag `v1.0` at end.
**Commit:** `T16: Launch & 72-hour observation — GO recorded`

## Rollback
Per HANDOFF: previous SHA kept; stop service before code switch; never cross incompatible schema; env/sessions outside checkout; restore verified dump instead of dropping tables; sessions restored only to the single instance (hearth:hearth, 0700).