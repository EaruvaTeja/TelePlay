# Hearth — Deploy-Run Plan (v2, re-baselined 2026-11-19)

**Audited code baseline:** `84926670051242bbbcd5afae378aa6f319ded062` (T1–T12 complete).
**Goal:** production launch 2026-11-19 on free tiers (NeoHeberg 512MB Debian VPS + Neon + Cloudflare Pages + DuckDNS + Caddy). Fallback: owner-only soft launch. Never skip P0 gates for the date.
Task IDs continue the repo's T-numbering (T12.1 and T16 are new). One task = one branch = one Copilot prompt = ONE final commit = one owner-merged PR.

## Constraints & Rules (apply to every task)
* **Frozen:** `web/src/components/MediaPlayer.tsx` is byte-identical except for a currently active, explicit owner-authorized sub-scope. T12.3 SPEEDS, T12.86 auto-landscape, T12.87 tap-controls, and T12.90.2 slider-axis exceptions are closed. T13 Exception #5 is authorized only within the individual T13.2–T13.10 task cards below and re-freezes after each task. Preserve its imports (`TelegramFile`, `formatDuration`, `useUpdateProgress`, `useFile`, `api`, `useAppStore`) and keys `hearth_player_prefs`, `hearth_device_id`. TV/PC behavior remains byte-identical except where #5.1, #5.2, #5.4, #5.6, and #5.8 explicitly permit changes.
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

### 2026-11-20 post-incident execution map (T12.81–T12.92, including T12.90.1/T12.90.2 follow-ups)

| Task | Scope |
|---|---|
| T12.81 | Enforce family stream-token revocation with version claims and User.id identity. |
| T12.82 | Make `family_members.active` the live bot/API family authorization authority. |
| T12.83 | Make Telegram upload compensation commit-aware and file inserts idempotent by channel message ID. |
| T12.84 | Fail-safe Telegram reconciliation: dry-run sync and confirmed-gone-only cleanup. |
| T12.85 | Complete remaining DB-wake UX and server status; record the original verify-code scope as already satisfied by T12.82. |
| T12.86 | OWNER-AUTHORIZED MediaPlayer exception #2: mobile-only auto-landscape. |
| T12.87 | OWNER-AUTHORIZED MediaPlayer exception #3: mobile-only tap controls/center play-pause. |
| T12.88 | Verify mobile/TV/PC parity and apply the final `MediaPlayer.tsx` freeze. |
| T12.89 | Prove schema with `verify_schema.py`; fix deploy runbooks; validate proxy configuration; record provenance. |
| T12.90 | Reliability hardening (A1/A2 handler-count gate, cross-owner device-ID rejection, runtime auth-key health, sync default `confirm=False`, refresh-lifetime decision); replace the banner; run final clean-checkout gates and record freeze-candidate SHA. |
| T12.90.1 | Restore transient auth-key retry behavior; quarantine a client only after 3 auth-key failures within 60 seconds, and clear the counter on successful lookup/chunk delivery. |
| T12.90.2 | OWNER-AUTHORIZED MediaPlayer exception #4: map pseudo-landscape Scrubber/VolumeBar pointer input along the visual vertical axis; rerun final clean-checkout gates and resume the freeze. |
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

## T12.82 — `family_members.active` authorization authority

**Branch:** `hearth/t12.82` from latest `main`. **Files:** `backend/app/bot.py`, `backend/app/routers/auth.py`, `backend/tests/test_bot_access.py`, `backend/tests/test_bot_db_wake.py` (extend only), `PLAN.md`, `PROGRESS.md`, and `AUDIT_REPORT.md`.

Add uncached `is_active_member(telegram_id)` and make the private-message authorization middleware and guarded commands use active database membership. Fall back to `settings.auth_users` only for `_DB_CONNECTIVITY_ERRORS`, so the bootstrap owner can reach the established DB-wake response. Reconcile existing and new User roles from membership; guard uploads before forwarding and prevent inactive users from minting login codes. In `verify-code`, validate live active membership for every bound ID, including existing User rows, and set `role="admin"` only for active members. Preserve the atomic one-time code consume and all owner-only and callback authorization checks.

**Gate:** full backend pytest, `compileall -q app`, and `pip check`; frontend `npm ci`, lint, typecheck, tests, and build; confirm `dist/_redirects`. Add focused active/inactive membership, verify-code, and DB-wake tests. Never weaken or delete existing security tests; do not upgrade dependencies.
**VERIFY ON VPS:** live DB membership add/remove behavior, including old login-code rejection and bootstrap-owner DB-wake behavior.
**Commit:** `T12.82: family_members.active is the live bot/API authorization authority — gate passed`

## T12.83 — Safe upload compensation and unique channel message IDs

**Branch:** `hearth/t12.83` from latest `main`. **Files:** `backend/app/bot.py`, `backend/app/models.py`, `backend/app/database.py`, `backend/tests/test_bot_db_wake.py` (extend only), `backend/tests/test_files_operations.py` (extend), `PLAN.md`, `PROGRESS.md`, and `AUDIT_REPORT.md`.

Track `db_committed` in `handle_file()` and set it only after commit and refresh succeed. Keep success-message creation and status editing in a separate post-commit notification handler that logs failures and attempts a plain reply without deleting the forwarded media. Compensate only while the row is not known committed; after an uncertain commit, query by `channel_message_id`, retain media if a row exists, and report persistence despite notification failure. Add a unique model index and an idempotent PostgreSQL/SQLite index migration guarded by a duplicate pre-check that logs and skips when legacy duplicates exist. Upload inserts must be idempotent and reuse an existing row for the same channel message.

**Gate:** full backend pytest, `compileall -q app`, and `pip check`; frontend `npm ci`, lint, typecheck, tests, and build; confirm `dist/_redirects`. Regress post-commit Telegram edit failure without deletion, preserve existing commit-failure compensation and T12.4 DB-wake tests, and verify duplicate upload/index migration behavior.
**Commit:** `T12.83: Safe upload compensation + unique channel_message_id — gate passed`

## T12.84 — Fail-safe reconciliation

**Branch:** `hearth/t12.84` from latest `main`. **Files:** `backend/app/streaming.py`, `backend/app/routers/streaming.py`, `backend/app/bot.py`, `backend/tests/test_t12_84_reconciliation.py`, `PLAN.md`, `PROGRESS.md`, and `AUDIT_REPORT.md`.

Treat a Telegram message as gone only when every client lookup succeeds and every client reports it missing. A mixed missing/error result is unknown and raises `StreamUnavailable`. When stream preparation returns an empty context, make one authoritative `tg_client.get_messages()` confirmation before deleting the row; return `FILE_GONE` and invalidate caches only on a successful empty result, and return `STREAM_UNAVAILABLE` without deleting on lookup exceptions or a still-present message.

Make `/sync` a read-only dry run that reports proposed row deletions. `/sync confirm` may delete only after all batch lookups complete successfully and the existing all-gone / 30% safety guard passes. Audit-log each proposed and committed deletion with both file ID and Telegram channel message ID. Keep `SYNC_ON_STARTUP` disabled in the production environment.

**Gate:** full backend pytest, `compileall -q app`, and `pip check`; frontend `npm ci`, lint, typecheck, tests, and build; confirm `dist/_redirects`. Add focused regressions for mixed gone/error, unanimous gone, authoritative confirmation and row preservation, dry-run, confirmation guard, and partial batch failure. Preserve all existing security tests.
**VERIFY ON VPS:** confirm the deployed `SYNC_ON_STARTUP=false` environment and exercise `/sync` dry-run/confirm against the production Telegram channel only after owner approval.
**Commit:** `T12.84: Fail-safe reconciliation — dry-run sync, confirmed-gone only — gate passed`

## T12.85 — Complete DB-wake UX and server status

**Scope:** the originally registered verify-code hardening is already satisfied by T12.82: `_get_or_create_family_user()` checks active membership for both existing and new users, and only active members receive `role=admin`. Complete DB-wake responses for `/logout_all`, `/users`, `/guest` status/rotate/off, `/sessions`, `/user_add`, `/user_remove`, and `/sync`; make the callback membership gate answer with the wake message on DB connectivity errors; and implement the bounded, membership-authorized `server_status` probe with bot connection state and process uptime. Preserve T12.83 upload compensation and T12.84 sync safety semantics.

**Files:** `backend/app/bot.py`, `backend/tests/test_bot_db_wake.py`, `PLAN.md`, `PROGRESS.md`, `HANDOFF.md`, `AUDIT_REPORT.md`.
**Gate:** full backend pytest, `compileall -q app`, and `pip check`; frontend `npm ci`, lint, typecheck, tests, and build; confirm `dist/_redirects`; preserve all existing bot tests and security assertions; MediaPlayer diff empty.
**Commit:** `T12.85: Complete DB-wake UX + server status; reconcile T12.85–T12.92 task map — gate passed`

## T12.86 — OWNER-AUTHORIZED MediaPlayer exception #2: mobile auto-landscape

**Scope:** implement mobile-only automatic landscape behavior after a mobile device is confirmed. TV/PC behavior must remain byte-identical in behavior; preserve every `MediaPlayer.tsx` export and both `hearth_player_prefs` and `hearth_device_id` (`DEVICE_ID_KEY`). Freeze the player again immediately after this task.

**Files:** `web/src/components/MediaPlayer.tsx`, new `web/src/lib/mobilePlayer.ts`, new `web/src/lib/__tests__/mobilePlayer.test.ts`, `HANDOFF.md`, `PLAN.md`, `PROGRESS.md`, and `AUDIT_REPORT.md`. `web/src/index.css` may change only if strictly required.

**Implementation:** phone video playback only; attempt native fullscreen/orientation lock on first play, use stage-scoped CSS pseudo-landscape only when native lock is unavailable in portrait, provide a toggle and one-time hint, and release orientation/fullscreen plus clear pseudo-landscape when minimizing or closing. Audio, tablet, TV, and computer behavior stay unchanged. Preserve all exports, player preferences/device-ID keys, TV key map, scrubber, settings, and session/prewarm behavior.

**Gate:** full backend pytest, `compileall -q app`, and `pip check`; frontend `npm ci`, lint, typecheck, tests, and build on Node 20; confirm `dist/_redirects`; preserve all existing backend/security tests. Record Android Chrome native-lock, iPhone Safari CSS-fallback, and minimize/close portrait-restoration checks as **VERIFY ON DEVICE**. Freeze `MediaPlayer.tsx` immediately afterward.

**Commit:** `T12.86: Mobile-only auto-landscape playback (owner-authorized exception #2) — gate passed`

## T12.87 — OWNER-AUTHORIZED MediaPlayer exception #3: mobile tap controls

**Files:** `web/src/components/MediaPlayer.tsx`, extend `web/src/lib/mobilePlayer.ts`, extend `web/src/lib/__tests__/mobilePlayer.test.ts`, `HANDOFF.md`, `PLAN.md`, `PROGRESS.md`, and `AUDIT_REPORT.md`.

**Scope:** route video-surface taps through `resolveSurfaceTap(kind)`: phones toggle only the controls overlay; TV/computer/tablet keep toggling playback. Disable phone double-click fullscreen, and provide a phone-only center Rewind-10/Pause/Forward-10 cluster while playing with controls visible. Keep the existing paused cluster, bottom-bar play/pause, root reveal/focus duties, and auto-hide behavior. The phone video surface must never play or pause; playback is controlled by the center and bar buttons, with ±10-second controls seeking only. TV remote, PC mouse, keyboard/D-pad map, scrubber, settings, minimize bar, exports, and localStorage keys remain behaviorally unchanged.

**Gate:** full backend pytest, `compileall -q app`, and `pip check`; frontend `npm ci`, lint, typecheck, tests, and build on Node 20; confirm `dist/_redirects`; preserve all existing backend/security tests. Add resolver tests for all four device kinds and assert non-phone kinds retain `toggle-play`. Record phone surface/center/seeking and TV/PC regression checks as **VERIFY ON DEVICE**. Freeze `MediaPlayer.tsx` immediately afterward.

**Commit:** `T12.87: Mobile tap shows controls only — center button owns play/pause (owner-authorized exception #3) — gate passed`

## T12.88 — Mobile exception parity and final player freeze

**Files:** `HANDOFF.md`, `PLAN.md`, `PROGRESS.md`, and `AUDIT_REPORT.md`. `web/src/components/MediaPlayer.tsx` must be byte-identical in this task (`git diff --stat -- web/src/components/MediaPlayer.tsx` empty). Extend the existing test file only if a parity gap needs a regression test. `mobilePlayer.ts` must not change behavior; if verification exposes a defect, stop and report it rather than fixing it.

**Scope:** run all standard gates at the branch tip; build the phone-portrait/phone-landscape/tablet/Tizen-TV/PC parity matrix with **CONFIRMED by source** and **VERIFY ON DEVICE** labels; compare `git diff c7bf7ec..HEAD -- web/src/components/MediaPlayer.tsx` and enumerate every hunk category. Verify exports, both localStorage keys, the TV key map, and desktop surface-click behavior. If any parity defect is found, mark this task BLOCKED and wait for owner authorization; do not make a fix.

**Final freeze:** after T12.88, no further `MediaPlayer.tsx` change is allowed without a new, explicit owner authorization. Record the freeze in `HANDOFF.md` and `PLAN.md`; device verification remains tracked for T15.

**Gate:** full backend pytest, `compileall -q app`, and `pip check`; frontend `npm ci`, lint, typecheck, tests, and build on Node 20; confirm `dist/_redirects`; preserve all existing backend/security tests. Confirm `MediaPlayer.tsx` has no task diff and only the T12.86/T12.87 owner-authorized exception hunks since c7bf7ec.

**Commit:** `T12.88: Mobile/TV/PC parity verified — final MediaPlayer freeze declared — gate passed`

## T12.89 — Schema proof, deploy runbooks, proxy validation, and provenance

**Files:** `backend/scripts/verify_schema.py` (new), `backend/tests/test_verify_schema.py` (new), `backend/app/config.py`, `backend/tests/test_config_validation.py`, `deploy/README.md`, `.env.example` (comments only), `PLAN.md`, `PROGRESS.md`, and `AUDIT_REPORT.md`.

**Scope:** add a read-only SQLAlchemy inspection tool comparing the live database with `Base.metadata` for tables, columns/types, nullability, server defaults, indexes, primary keys, and unique constraints; support the configured app engine for Neon Direct and temporary SQLite regression tests. Report drift and exit nonzero without mutating schema/data; identify the historical T0.7 `family_members` gap and `create_all()` boot behavior. Validate proxy scheme and numeric port (1–65535) whenever a proxy host is configured. Correct the runbook's target-process environment loading, backup row counts, mandatory schema pre/post-boot checks, `ProtectSystem=strict` session write path, and A6/A7 provenance controls; GitHub `main` is authoritative and the stale bundle remains quarantine-only pending T12.91. F-01 and F-02 code fixes are closed by T12.81 and T12.82; do not reassign those code changes here.

**Gate:** full backend `.venv\Scripts\python -m pytest -q`, `.venv\Scripts\python -m compileall -q app`, and `.venv\Scripts\pip check`; frontend on Node 20: `npm ci`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`, and confirm `dist/_redirects`; inspect final diff for no dependency or `MediaPlayer.tsx` changes. Live Neon/VPS schema validation is **VERIFY ON VPS**.

**Commit:** `T12.89: Schema proof tooling + runbook env/row-count fixes + proxy validation — gate passed`

## T12.90 — Reliability hardening and clean-checkout freeze candidate

**Files:** `backend/app/main.py`, `backend/app/telegram.py`, `backend/app/streaming.py`, `backend/app/playback.py`, `backend/app/bot.py` (sync default only), `backend/app/config.py` (refresh default only), `backend/tests/`, `files/app_banner.png`, `HANDOFF.md`, `PLAN.md`, `PROGRESS.md`, and `AUDIT_REPORT.md`.

**Scope:** permanently fail startup if the lifespan bot import registers zero handlers; reject playback device IDs owned by another account; mark Telegram clients unhealthy on `AuthKeyUnregistered`, `AuthKeyDuplicated`, or `SessionRevoked`, stop retrying those clients, expose a precise readiness reason, and preserve session files with class-specific recovery guidance. Make reconciliation dry-run by default, keep supervised sync dry-run only, retain explicit `/sync confirm`, and report safety aborts distinctly. Reduce the environment-overridable refresh-token default from 90 to 30 days; document the accepted household residual risk and defer the full rotation matrix to P2. Replace `files/app_banner.png` byte-for-byte with the owner-supplied `C:\Users\earuv\Downloads\app_banner.png`. Do not change dependencies or `MediaPlayer.tsx`.

**Gate:** from a fresh clean checkout and fresh Python 3.13 environment install `requirements-dev`; run full `pytest -q`, `compileall -q app`, `pip check`, record `pip freeze`, and run `pip-audit -r requirements.txt` without blind upgrades. On Node 20 run `npm ci`, lint, typecheck, tests, build, confirm `dist/_redirects`, and run `npm audit --omit=dev` without `--force`. Verify tracked-file hygiene (no `.env`, session, or dump artifacts), no active folder/QR legacy code, the authorized-only MediaPlayer diff, and exact banner source/destination hashes plus Git tracking. Append complete gate evidence with versions, counts, audit outcomes, tested SHA/tree, and freeze-candidate state to `AUDIT_REPORT.md`.

**VERIFY ON VPS:** unhealthy-client reporting and auth-key recovery, cross-account device-ID rejection, sync safety-abort behavior, and banner rendering after deployment. Keep T12.91, T0-R, T12.92, T15-R, and T16-R on hold; the owner tags `deploy-T12.90-rc` only after merge.

**Commit:** `T12.90: Reliability hardening + final release gates & freeze evidence — gate passed`

## T12.90.1 — Persistent auth-key failure threshold

**Files:** `backend/app/telegram.py`, `backend/app/streaming.py`, `backend/tests/test_t12_90_reliability.py` (extend), `PLAN.md`, `PROGRESS.md`, and `AUDIT_REPORT.md`.

**Scope:** close Finding B by retaining per-client auth-key failure timestamps for a rolling 60-second window, pruning stale entries, and marking a client unhealthy only at three failures in that window. Earlier failures are warnings; successful message lookup, refresh lookup, or delivered chunks clear that client's counter. Keep the existing unhealthy-client reason, retry/backoff behavior, healthy-pool filtering, unanimous-gone handling, and session-file preservation unchanged.

**Gate:** full backend `.venv\Scripts\python -m pytest -q`, `compileall -q app`, and `pip check`; frontend Node 20 `npm ci`, lint, typecheck, tests, build, and confirm `dist/_redirects`; `npm audit --omit=dev`; `git diff --check`; confirm no dependency changes and an empty `MediaPlayer.tsx` diff. VPS auth-key recovery remains **VERIFY ON VPS**.

**Commit:** `T12.90.1: Auth-key unhealthy marking requires persistent failures (3/60s) — gate passed`

## T12.90.2 — OWNER-AUTHORIZED MediaPlayer exception #4: pseudo-landscape slider axis

**Files:** `web/src/lib/mobilePlayer.ts`, `web/src/components/MediaPlayer.tsx`, `web/src/lib/__tests__/mobilePlayer.test.ts` (extend), `HANDOFF.md`, `PLAN.md`, `PROGRESS.md`, and `AUDIT_REPORT.md`.

**Owner authorization:** 2026-11-20. The T12.88 MediaPlayer freeze is reopened for this task only; freeze resumes immediately upon completion.

**Scope:** add pure `sliderRatio(rect, clientX, clientY, rotated)` math with clamping and zero-dimension guards. In rotated mode use vertical pointer coordinate and rectangle height; otherwise use horizontal coordinate and width. Add optional `rotated` props to Scrubber and VolumeBar, pass the phone-only `pseudoLandscape` state, and route pointer-down/move ratio calculations through the helper. Leave local paint coordinates (`scaleX`/`left%`) unchanged. No other player behavior, exports, TV/desktop controls, or storage keys may change.

**Gate:** full backend and frontend standard gates; then repeat T12.90's clean-checkout release suite with fresh Python 3.13 environment, pytest/compileall/pip check/pip-audit, Node 20 npm ci/lint/typecheck/test/build/_redirects/npm audit, hygiene checks, and cumulative MediaPlayer exception-category review. Record the tested candidate SHA/tree and supersede the T12.90 freeze candidate in `PROGRESS.md`/`AUDIT_REPORT.md`. Update the T12.88 parity matrix: pseudo-landscape Scrubber/VolumeBar axis mapping is **CONFIRMED by source**; physical iPhone/Android and TV/PC checks remain **VERIFY ON DEVICE**.

**Manual checklist — VERIFY ON DEVICE:** iPhone portrait fallback progress drag seeks along the visual bar; volume drag follows the visual bar; Portrait view control and physical rotation exit cleanly; Android native orientation lock is unaffected.

**Commit:** `T12.90.2: Pseudo-landscape slider axis fix (owner-authorized exception #4) + final freeze gates — gate passed`

## T13 phase — owner-authorized UX and household count tasks

The bare **T13 Deployment Kit & Runbooks** task is already complete. This phase consists of T13.1–T13.11 sub-tasks. Cloudflare Pages publishes on merge to `main`, while the VPS remains on `deploy-T12.90.2-rc` until the owner deploys; every web change must remain compatible with the old server. The owner intends to merge T13.2–T13.8 in one sitting because the temporary removal of the bottom-bar volume controls precedes their replacements. T12.91, T12.92, T0, T15, and T16 remain **ON HOLD**.

**T13 guardrails:** no new dependencies or `backdrop-filter`; preserve Chrome 53/old-Tizen compatibility and the existing old-server contract. Do not change the playback limiter, auth-before-cache/stream-token/revocation logic, bot, database schema, deployment kit, protected API/store exports, or `hearth_player_prefs`/`hearth_device_id` keys. `MediaPlayer.tsx` may change only inside the active task's Exception #5 sub-scope. Do not push to main, create a tag, or create/merge a PR.

### T13.1 — Phase authorization and docs re-baseline (docs only)

**Scope:** Record the owner authorization dated 2026-11-20 as Exception #5 to the `MediaPlayer.tsx` freeze. The exception is divided into task-specific sub-scopes and re-frozen after each matching task. This task changes documentation only; zero code diff.

**Files (only):** `HANDOFF.md`, `PLAN.md`, `PROGRESS.md`, `AUDIT_REPORT.md`.

**Implementation:** In `HANDOFF.md`, record #5.1 T13.2 bottom-bar volume removal; #5.2 T13.3 4s→3s hide timeout; #5.3 T13.4 phone-only portrait-first/compact controls/auto-landscape removal/iOS fullscreen fallback; #5.4 T13.5 class-only glass center button; #5.5 T13.6 phone brightness/volume drag gestures and indicator; #5.6 T13.7 TV/PC/tablet side buttons and additive D-pad navigation; #5.7 T13.8 phone lock and drag-to-pause/play; #5.8 T13.10 DeviceLimitDialog title/body text only. State that TV/PC behavior may change only for #5.1, #5.2, #5.4, #5.6, and #5.8, and everything else remains byte-identical.

Add T13.1–T13.11 to `PLAN.md` using the task cards below, without widening scope. In `PROGRESS.md`, add the checklist, dependency map, current task, and one no-SHA log line; tick T13.1 only after its gates pass. Keep T12.91, T12.92, T0, T15, and T16 on hold. Append the actual clean-main baseline gate measurements and standing notes to `AUDIT_REPORT.md`: stale deploy split/old-server compatibility; temporary volume-control gap and owner merge plan; slot-holder/75-second counter semantics; stale `docs/RELEASING.md` and unchecked T12.2–T12.5 history reserved for T13.11 with owner approval.

**Gate:** On clean latest `main`, run the full backend gates (Python 3.13 `compileall -q app`, `pip check`, full `pytest`) and frontend gates (Node 20 `npm ci`, lint with zero warnings, typecheck, `vitest run`, build, `dist/_redirects`, `npm audit --omit=dev`). Record actual counts and the built JS bundle size. Counts must not drop from the measured baseline. Confirm `git diff --stat` lists only the four docs and the `MediaPlayer.tsx` task diff is empty.

**Commit:** `T13.1: T13 phase authorization & plan re-baseline (owner exception #5) — docs only`

### T13.2 — Issue 1: remove bottom-bar volume cluster (all devices)

**Sub-scope:** Exception #5.1. **Files:** `web/src/components/MediaPlayer.tsx`, `AUDIT_REPORT.md`, `PROGRESS.md`, `HANDOFF.md`.

**Scope:** On every device remove only the volume controls beside the bottom-bar ±10-second buttons. The owner will redesign volume later in T13.6/T13.7.

**Implementation:** Remove the bottom-bar divider span, adjacent Mute button, “Volume down” IconBtn, `VolumeBar`, and “Volume up” IconBtn. Remove the `VolumeBar` component definition and code used only by it; `data-hp-vol` handling and `onVol` D-pad branches used only for the slider; helpers `volDown`, `volUp`, `stepVolume`, `setVolumeLevel`; and now-unused Minus/Plus icon imports. Keep the top-bar Mute button, M key, `prefs.volume`/`prefs.muted` engine and persistence, `onVolumeChange` sync, `toggleMute`, and all `hearth_player_prefs` keys. Remove no unrelated code.

**Check:** Reason through TV D-pad focus order so it has no dead stop or removed-element reference; reason through phone/PC/TV bottom-bar layout. Device behavior cannot be run locally. Acceptance: no volume UI beside the ±10-second buttons; top-bar Mute and M key still work; TV/PC behavior otherwise byte-identical; all gates green.

**Gate:** Full backend and frontend gates; zero lint warnings; `MediaPlayer.tsx` diff limited to this authorization and required removal of newly unused items; task audit/progress docs updated.

**Commit:** `T13.2: Remove bottom-bar volume cluster (owner-authorized exception #5.1) — gate passed`

### T13.3 — Issue 7: controls auto-hide 4s to 3s (all devices)

**Sub-scope:** Exception #5.2. **Files:** `web/src/components/MediaPlayer.tsx` and task documentation.

**Scope:** Controls on all devices auto-hide after 3 seconds of inactivity instead of 4.

**Implementation:** Change `HIDE_AFTER_MS` from 4000 to 3000; update “4s” wording in the file-header comment and the section comment above `hideControlsNow`; update any docs that state four seconds. Grep all of `web/src`, tests, and docs for any other assumption of a four-second controls timeout; record what was checked in `AUDIT_REPORT.md`, and change only text about this auto-hide.

Do not change any auto-hide guards: no hide while paused, buffering, settings open, a dialog open, or scrubbing. Every key press/touch must continue to re-arm the timer via `revealControls`. Do not change another timing constant.

**Acceptance:** playing video hides controls after 3 seconds on phone, PC, and TV; settings and scrubbing continue to block hiding. **VERIFY ON TV:** determine whether 3 seconds feels workable with D-pad navigation; every key press must re-arm the timer.

**Gate:** Full backend and frontend gates; zero lint warnings; search results and only relevant timeout-text changes recorded.

**Commit:** `T13.3: Controls auto-hide 4s → 3s on all devices (owner-authorized exception #5.2) — gate passed`

### T13.4 — Issue 2: phone portrait-first player and compact controls

**Sub-scope:** Exception #5.3. **Files:** `web/src/components/MediaPlayer.tsx`, `web/src/lib/mobilePlayer.ts`, `web/src/lib/__tests__/mobilePlayer.test.ts`, and task documentation. **Phone only:** TV, PC, and tablet behavior must remain byte-identical.

**Problem and target:** T12.86 currently auto-rotates a phone video to landscape using native orientation lock and a CSS `rotate(90deg)` pseudo-landscape. In portrait, the bottom bar is about 440px wide and pushes Crop, Settings, PiP, and Fullscreen off a 360px screen. iPhone Fullscreen is not rendered when `document.fullscreenEnabled` is false. The target is portrait on open, all seven controls visible/tappable even at 320px (Play/Pause, −10s, +10s, Crop, Settings, PiP, Fullscreen), working Fullscreen, and natural landscape after physical rotation.

**Remove all T12.86 auto-landscape machinery:** `requestLandscapeOnPlay`, `releasePhoneLandscape`, and all call sites (play, surface interaction, close/unmount); refs/state `landscapeAttemptedRef`, `landscapeRequestIdRef`, `rotateHintShownRef`, `pseudoLandscapeEnabled`, `nativeLandscapeUnsupported`, `showRotateHint`; rotate-hint chip and toast; `data-hp-pseudo-landscape` rotate CSS and rotated/pseudo-landscape child props (including `Scrubber`). In `mobilePlayer.ts`, remove `shouldAutoLandscape`, `lockLandscape`, `unlockLandscape`, `computePseudoLandscape`, and tests of those deleted functions. Keep `isPhonePlayer`, `resolveSurfaceTap`, `sliderRatio`, and their tests; ensure `Scrubber` remains unrotated and `sliderRatio` still behaves correctly for that case. Remove orientation listeners/`isPortrait` only if unused after removal.

**Compact phone bar, below `sm` only:** IconBtn `h-10 w-10`, `sm:h-11 sm:w-11`; icons `h-5 w-5`, `sm:h-6 sm:w-6`; tighter gaps; time labels `text-xs min-w-[44px] sm:text-sm`; use `flex-nowrap` and `min-w-0` so groups shrink rather than overflow; retain safe-area padding. Budget at 320px: 3 × 40px left controls plus 4 × 40px right controls is about 290px and must fit. At/above `sm`, preserve existing sizes exactly. Mute remains in the top bar (T13.2 removes bottom-bar Mute).

**iOS Fullscreen fallback, phone only:** if `document.fullscreenEnabled` is false but the video element exposes `webkitEnterFullscreen`, render the Fullscreen icon and use native video fullscreen (`webkitEnterFullscreen`/`webkitExitFullscreen`). Track state with `webkitbeginfullscreen`/`webkitendfullscreen`. Keep TV/PC fullscreen logic byte-identical by guarding fallback behavior with `isPhonePlayer()`.

**Tests and acceptance:** delete only tests for deleted functions and list every removed test in `AUDIT_REPORT.md`; keep and, if useful, extend tests for `isPhonePlayer`, `resolveSurfaceTap`, and `sliderRatio`. Verify all seven controls fit at 320px, natural physical rotation, Android and iPhone Fullscreen (**VERIFY ON DEVICE**), and unchanged TV/PC behavior. All gates green.

**Commit:** `T13.4: Mobile portrait-first player + compact controls (owner-authorized exception #5.3) — gate passed`

### T13.5 — Issue 3: glass center play/pause button (visual only)

**Sub-scope:** Exception #5.4. **Files:** `web/src/components/MediaPlayer.tsx` (class strings and icon classes of the two center play/pause buttons only) and task documentation.

**Target:** Replace the solid teal disc on the large centered Play/Pause button with a glass-like treatment that keeps the video visible. Do not use `backdrop-filter`; glass is translucent rgba fill plus thin border.

**Design:** background `rgba(153,246,228,0.16)`, hover `rgba(153,246,228,0.24)`, border `1px solid rgba(94,234,212,0.30)`, icon `#d9fdf6` with `drop-shadow(0 1px 2px rgba(0,0,0,0.55))` on the lucide Play/Pause SVG and its polygon/paths via `currentColor`. Preserve `h-20 w-20`, `rounded-full`, visible `hp-focus` ring for TV, `active:scale-95`, `hover:scale-105`, transition, and Play icon `ml-1` optical offset. Apply to both the paused cluster and phone playing cluster. Do not touch the mini-player bar button or any other button. Use comma-form rgba values, not space-separated rgb slash syntax; use inline style or an existing CSS class if Tailwind arbitrary values are awkward.

**Acceptance:** no behavior change; button remains readable over dark and bright frames; focus ring intact; gates green.

**Commit:** `T13.5: Glass center play/pause button (owner-authorized exception #5.4) — gate passed`

### T13.6 — Issue 4: phone brightness/volume drag gestures and indicator

**Sub-scope:** Exception #5.5. **Files:** `web/src/components/MediaPlayer.tsx`, `web/src/lib/mobilePlayer.ts` (new pure helpers), `web/src/lib/__tests__/mobilePlayer.test.ts` (extend), and task documentation. **Phone only:** gate with `isPhonePlayer()`; TV/PC/tablet are untouched.

**Behavior:** On the video surface, vertical drag on the left half changes brightness and on the right half changes volume. The indicator appears only during a drag and fades for about 800ms after lift; no persistent slider/icon.

**Engine:** Add an additive `brightness` field to `hearth_player_prefs`, default 1, clamped to 0.1–1; older saved prefs without the field must load. Render a pointer-events-none black overlay at `z-[12]`, above video and below all UI, with opacity `1 - brightness`; do not CSS-filter the video. Reuse `prefs.volume`/`prefs.muted`: drag to 0 mutes and values above 0 unmute; add no storage keys. Probe once whether `video.volume` is writable by setting, reading back, and restoring a value. If not writable (iOS), right-side drag shows “Use device volume buttons” instead of a fake value; top-bar Mute still works.

**Gesture rules:** Active only on phone video surface when media is ready, player not minimized, no dialog is open, and settings are closed. On pointerdown store start x/y/value/side; ignore non-primary pointers. Claim only when `|dy| > 12px` and `|dy| > 1.3 * |dx|`; choose side from pointerdown x relative to stage midpoint. Compute `clamp(startValue + (startY - currentY) / (0.65 * stageHeight))`. Use pointer capture after claim; handle pointercancel. After a claimed drag, suppress the surface tap that would otherwise toggle controls. Never intercept starts on buttons, sliders, Scrubber, top bar, or bottom bar. Preserve horizontal-swipe behavior. Add `touch-action: none` to the surface only if needed. Support portrait and fullscreen.

**Reusable indicator:** small component for T13.7 reuse with props `kind: 'brightness' | 'volume'`, `value` 0–1, `side: 'left' | 'right'`, `visible`, optional `hintText`, `fadeMs`. Vertical glass pill uses solid rgba only (`bg-black/45`, `border-white/15`), Sun or VolumeX/Volume1/Volume2 by level, thin vertical track/fill, and `text-white/85` percent. Low-opacity video-visible styling; vertically centered and horizontally offset `max(64px, 14%)` from its side edge (room for T13.8 lock), never over center play cluster; `pointer-events-none`, `z-[60]`; visible when controls are hidden. Phone fade is 800ms.

**Pure-helper tests:** axis classification/claim rule, delta/value math, brightness/volume clamps (brightness 0.1–1, volume 0–1), side selection, and iOS fallback decision.

**Acceptance:** drags work in portrait/fullscreen, taps still toggle controls, indicator is transient, Scrubber unaffected, TV/PC untouched; device behavior is **VERIFY ON DEVICE**. All gates green.

**Commit:** `T13.6: Mobile brightness/volume drag gestures + indicators (owner-authorized exception #5.5) — gate passed`

### T13.7 — Issue 5: TV/PC/tablet side controls and D-pad navigation

**Sub-scope:** Exception #5.6. **Files:** `web/src/components/MediaPlayer.tsx` and task documentation. Reuse the indicator and brightness/volume helpers from T13.6; do not duplicate them. Apply to TV, computer, and tablet; phones retain gestures and get no buttons.

**UI:** Brightness [+]/[−] stack at left edge and Volume [+]/[−] stack at right edge, vertically centered and about 3.5% inset. Buttons use `h-11 w-11 rounded-full bg-white/10 border border-white/15 text-white/85 hp-focus`, matching the existing ±10-second glass family; no backdrop-filter. Each press steps 0.1. Clamp brightness 0.1–1 and volume 0–1; zero mutes and raising above zero unmutes. Buttons are inside the controls overlay and auto-hide with it after 3s; existing `revealControls` handles key/mouse movement. Each step shows the shared indicator with `fadeMs=1200`. PC clicks work; no mouse-hold requirement; preserve keys/shortcuts.

**Additive D-pad/keyboard navigation only:** At bottom-bar left end, ArrowLeft focuses brightness cluster; at right end, ArrowRight focuses volume cluster. Within a cluster ArrowUp/ArrowDown move between + and −; OK/Enter activates; held OK repeats via `e.repeat` or equivalent Tizen keydown repeat. ArrowRight from left cluster and ArrowLeft from right cluster return focus to bottom bar. Extend hide guard while a side button has focus, mirroring Scrubber guard; never leave focus on an element that becomes invisible (reuse existing `hideControlsNow` rescue). Keep Tizen Back/Esc handling unchanged. `hp-focus` rings stay clear. TV path must take at most two presses from bar to either cluster.

**Parity matrix (mandatory):** In `AUDIT_REPORT.md`, table every existing key (arrows, OK/Enter, Space, M, F, Esc/Back, Tizen codes, media keys, etc.) and its result before and after. Nothing may differ except the two additive bar-end transitions.

**Acceptance:** both clusters usable by remote and mouse; held OK ramps; indicator visible; controls do not hide while side button is focused; Samsung TV behavior is **VERIFY ON TV**. All gates green.

**Commit:** `T13.7: TV/PC brightness/volume side buttons + D-pad navigation (owner-authorized exception #5.6) — gate passed`

### T13.8 — Issue 8: phone control lock with drag-to-pause/play

**Sub-scope:** Exception #5.7. **Files:** `web/src/components/MediaPlayer.tsx`, pure helpers in `web/src/lib/mobilePlayer.ts`, tests in `web/src/lib/__tests__/mobilePlayer.test.ts`, and task documentation. Phone only (`isPhonePlayer()`); do not render on TV/PC/tablet.

**Design and behavior:** Add a glass `h-10 w-10` Lock button to the phone controls overlay, 12px from the left edge and vertically centered. Its indicator offset must prevent overlap (T13.6 starts at `max(64px, 14%)`). Tapping Lock enters locked state, immediately hides all controls including lock button, and shows “Locked” briefly (~1s); playback continues. Lock is not persisted and resets on close or a different file.

While locked, disable brightness/volume drags, surface tap-to-toggle, Scrubber, Fullscreen, Settings, and PiP. Screen tap reveals only a small glass closed-lock handle at the left edge; while playing it auto-hides after `HIDE_AFTER_MS` (3s). Drag the handle right at least 32px to toggle pause/play without unlocking; it follows the finger to about 56px then snaps back. Each later drag toggles again. While paused, handle remains visible and shows a small Play glyph. Tapping the handle unlocks and restores controls under normal auto-hide rules.

Use pointer capture and `touch-action: none` on the handle; ignore non-primary pointers and handle pointercancel. Under 8px movement is a tap/unlock; over 8px horizontal movement is a drag and never unlocks. Handle must be a real `<button>` with `aria-label="Unlock controls"` and accessible pause/play state label. Center play button is hidden while locked; only handle drag toggles playback.

**Safety:** Auto-unlock on video end, playback error, or any dialog (device-limit popup, admin kick, etc.). Read current Escape/Backspace/BrowserBack handling near the handler and any history/popstate logic before changing Back behavior. If Back closes the player, while locked first Back reveals the handle with “Tap the lock to unlock” and does not close; a second Back within 2s may close. Document exactly what exists and what is implemented in `AUDIT_REPORT.md`. Never create an inescapable state. Heartbeat, resume, and playback logic remain untouched; lock is pure UI state.

**Pure-helper tests:** tap-vs-drag classification, drag threshold, pause/play toggle decision, and auto-unlock conditions.

**Acceptance checklist:** record each as CONFIRMED by tests/reasoning or VERIFY ON DEVICE: lock visible in portrait/landscape without indicator overlap; lock hides controls while video plays; screen tap shows only handle and playing handle hides in 3s; right drag pauses then resumes while locked; handle tap unlocks; brightness/volume drags disabled while locked; dialogs/errors unlock and remain usable; reopen starts unlocked; TV/PC unchanged. Physical behavior is **VERIFY ON DEVICE**. All gates green.

**Commit:** `T13.8: Mobile control lock with drag-to-pause/play (owner-authorized exception #5.7) — gate passed`

### T13.9 — Issue 6a: household playback count endpoint

**Sub-scope:** none (backend only). **Files:** `backend/app/routers/playback.py`, `backend/app/schemas.py`, `backend/tests/test_playback.py`, `web/src/lib/api.ts` (contract comment only), and task documentation. `web/src/components/MediaPlayer.tsx` diff must be empty. Do not change limiter `backend/app/playback.py`.

**Why:** Guest `GET /api/playback/active` hides other users' sessions, so guests need a privacy-safe household-wide count.

**Implementation:** Add schema `PlaybackCountOut { active: int, limit: int }`. Add authenticated `GET /api/playback/count` for family and guest, using the same auth dependency as the router's other read endpoints and existing rate-limit conventions. Return exactly `{"active": N, "limit": L}`: `active` from existing `limiter.active()` (which purges expired TTL sessions); `limit` from configured maximum (`settings.max_playback_devices` / `limiter.max_devices`). No names, labels, file or owner information. Update router module contract docstring and `api.ts` contract comment only; use `response_model` and existing error conventions.

**Tests:** guest sees household count including other users; family caller; TTL expiry → active 0; unauthenticated status matches existing playback endpoints (401 or repository convention); limit equals configured setting; exactly the two JSON keys. Preserve existing tests.

**Gate:** full backend compileall, pip check, pytest; full frontend gates to prove no other changes; empty MediaPlayer diff.

**Commit:** `T13.9: Household playback count endpoint — gate passed`

### T13.10 — Issue 6b: home live-devices chip, popup text, and flow verification

**Sub-scope:** Exception #5.8, copy-only `DeviceLimitDialog` text. **Files:** new `web/src/components/LiveDevicesChip.tsx`; `web/src/components/FileBrowser.tsx` (import/render by RolePill); `web/src/lib/api.ts` (fetcher, key, hook); `web/src/lib/__tests__/api.test.ts`; only DeviceLimitDialog text in `web/src/components/MediaPlayer.tsx`; task documentation. Backend does not change; T13.9 provides `GET /api/playback/count` returning `{active, limit}`.

**API:** `fetchPlaybackCount()` returns `{active:number; limit:number}` from `/playback/count`, following `fetchActiveDevices` typed-error conventions. Add query key and React Query hook using repository naming. Old-server 404/405 means feature unavailable: chip silently renders nothing, no error toast/console spam. Other errors retain last known value. Poll every 15s only while FileBrowser/home is mounted; pause while tab hidden; refetch on window focus/visibility change.

**Chip:** New `LiveDevicesChip.tsx`, rendered beside RolePill. Dot plus “N watching” from `sm` up and “N/limit” on phones; limit must come from server, never hard-code 2. Colors: 0 neutral grey, 1 green `#34d399`, 2 orange `#fbbf24`, 3+ red `#f43f5e` (defensive state though a third device is blocked). Use `role="status"`, `aria-live="polite"`, not focusable (`tabIndex=-1`/no interactive element) so TV focus order is unchanged. Low-key RolePill styling; no backdrop-filter. Test pure color/text mapping for 0/1/2/3/5 and limit 2 plus another limit; test API 404/405 handling.

**Dialog text only:** title “Two devices are already playing” → “Maximum watch devices reached”. Body says maximum devices are already watching, retains existing ask-family-account/try-again wording, and does not hard-code “two”. Keep device list, admin Stop buttons, Try again, and Close exactly unchanged. No logic, props, hooks, or layout changes.

**Verify existing third-device block by reading code/tests; do not change it:** record evidence that POST `/playback/start` at limit returns 409 `DEVICE_LIMIT` before any bytes; web maps it to DeviceLimitDialog; admin Stop frees a slot; guest copy appears; player close sends stop or slot expires after 75s. If a real bug appears, stop and report, no out-of-scope fix. Record owner **VERIFY ON DEVICE** for two devices playing/third attempt popup and chip 1 green/2 orange.

Document counter semantics: limiter slot-holders include `prewarmPlayback` after card hover/focus at 220ms; browsing can hold a slot up to 75s, and paused playback frees it after 75s. Existing limiter behavior is unchanged.

**Acceptance:** chip hidden on old server, correct new-server text/colors, TV focus unchanged, popup wording updated. The MediaPlayer diff must contain only dialog text lines, included in the report. All gates green.

**Commit:** `T13.10: Home live-devices chip + device-limit popup text + flow verification — gate passed`

### T13.11 — Final freeze gates, RC candidate, and deploy handoff (docs only)

**Sub-scope:** none (docs only). **Files:** `HANDOFF.md`, `PLAN.md`, `PROGRESS.md`, `AUDIT_REPORT.md`. Optional `docs/RELEASING.md` rewrite (stale Android-APK-era text) and T12.2–T12.5 checkbox reconciliation are permitted only with owner approval in the task prompt; otherwise leave both untouched.

**Implementation and gates:**

1. Run all backend/frontend gates from a fresh clean checkout of main, fresh Python 3.13 venv and Node 20; `npm ci`; compare test counts against T13.1 (none may drop except tests removed by T13.4 and listed there).
2. Review line-by-line `git diff a910a72cb29e975b93febc7eb7d2783c952305d..HEAD -- web/src/components/MediaPlayer.tsx`. Table each hunk against #5.1–#5.8. Any unauthorized hunk is a finding; do not conceal it.
3. Confirm the T13.7 keymap parity table still holds. List every intentional TV/PC difference: volume cluster removed, hide at 3s, glass play button, side buttons/bar-end navigation, dialog text.
4. Security greps: no committed secrets/tokens; compare auth-before-cache in `backend/app/streaming.py` and `byte_cache.py`, and `backend/app/playback.py` limiter against a910a72. `git diff a910a72..HEAD --stat` must show no changes to `deploy/`, `auth.py`, `streaming.py`, `byte_cache.py`, models/database, or `bot.py`.
5. Confirm zero dependency changes (`package.json`, lockfile, backend requirements) and zero DB schema changes versus a910a72; rollback to `deploy-T12.90.2-rc` remains safe.
6. Freeze Exception #5 in `HANDOFF.md`: close all sub-scopes and re-freeze MediaPlayer. Record RC candidate commit and tree SHA; the owner tags the merged T13.11 commit on main, which may differ from the candidate due to merge/squash.
7. Set Current Task to “OWNER deploy step” and document owner-only deployment:
   - `git checkout main && git pull`; verify HEAD is merged T13.11; `git tag deploy-T13.11-rc && git push origin deploy-T13.11-rc`. Agent never tags.
   - Hard-refresh `teleplay.pages.dev` and confirm final build.
   - Per `deploy/README.md` §4 on VPS: `sudo -u hearth git -C /opt/hearth/app fetch --tags`; checkout `deploy-T13.11-rc`; no dependency changes, no reinstall; `sudo systemctl restart hearth`; loopback `curl 127.0.0.1:8000/health/ready`; `journalctl -u hearth -n 50` (bot handlers registered); authenticated GET `/api/playback/count` returns `{"active":N,"limit":2}`.
   - Smoke matrix: phone portrait/all icons/Fullscreen on Android and iPhone; left/right drags with indicator only while dragging; lock/handle/drag pause-play/unlock; glass button over dark/bright frames; 3s hide on phone/PC/TV; TV D-pad reaches brightness/volume, hold-OK ramps, old keys unchanged; two devices plus third-device “Maximum watch devices reached” popup; chip 1 green/2 orange; closing a player frees a slot within about 75s.
   - Rollback: on VPS checkout `deploy-T12.90.2-rc` and restart. No schema/dependency changes; old server supports new web build because chip hides on 404/405. Pages may roll back to prior deployment.
8. Consolidate every remaining VERIFY ON DEVICE / TV / VPS item from T13.2–T13.10 in `AUDIT_REPORT.md`.

**Commit:** `T13.11: T13 final freeze gates + RC candidate handoff — gate passed`

## T12.91 — Stale bundle and VPS resource recovery

**Scope:** track and remediate the stale `/opt/hearth/hearth-v1.0-rc.bundle` at SHA `7629f0a`, disk 75% (3.0/4.0 GB), and RAM 210/512 MB. Record owner/VPs actions and evidence for the incident items assigned to this task, including bundle quarantine/removal or replacement and resource recovery.

## T12.92 — Final freeze, gate rerun, and handoff

**Scope:** after T12.81–T12.91, freeze the release and execute the final baseline: T0-R (backups reachability/recovery gate), T15-R (VPS/hardware acceptance gate), and T16-R (launch/72-hour readiness gate). Refresh audit evidence, update final SHA/release status, and prepare handoff for owner merge only.

## T0 — Verified Backups (OWNER, BEFORE first production boot; agent may assist)

Re-scoped: the old "before T2" wording is historical (dev schema work already gated). The hard boundary now is the FIRST boot against production Neon.
* Run `deploy/backup-neon.sh` (direct endpoint; client ≥ Neon major). Verify non-empty + "dump complete". **Copy off-VPS** (scp to your PC).
* Record Neon project/branch/region + row counts (users, family_members, files, login_codes, guest_credentials, watch_progress).
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