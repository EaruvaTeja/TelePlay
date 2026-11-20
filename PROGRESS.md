# Progress — Update After EVERY Commit

**This file is the single source of truth for execution state across sessions.**

* **Audited Code Baseline:** `84926670051242bbbcd5afae378aa6f319ded062` (main; T1–T12 merged via PR #16; full static audit 2026-11-19)
* **Historical Dev Baseline:** `5f0d769d7c8c143f27e419da90622505d153bcf0` (T1–T12 era; see git history)
* **Active Branch:** `hearth/t12.85`
* **Current Task:** `T12.86` — OWNER-AUTHORIZED MediaPlayer exception #2: mobile-only auto-landscape
* **Release SHA:** frozen at end of T14 (tag `v1.0-rc`) — see Deployment Readiness below

---

## Task Checklist

* [x] **T1** — Dependencies & Environment (`backend/requirements.txt`, `requirements-dev.txt`, `.env.example`)
* [x] **T2** — Schema Truth & DB Hardening (`models.py`, `database.py`, `config.py`)
* [x] **T3** — Session & Playback Core (`playback.py`, `routers/auth.py`, `tests/test_playback.py`)
* [x] **T4** — Telegram Client Safety (`telegram.py` in-place mutation & FloodWait retries)
* [x] **T5** — Management Surface & Bot (`bot.py` callback auth gates, `/help`, `/users`, `/guest`, `/kick`)
* [x] **T6** — Media Security & Headers (`routers/streaming.py`, `main.py`, strip `slowapi`)
* [x] **T7** — File Operations & Atomic Upserts (`routers/files.py` ON CONFLICT progress, batch-delete errors)
* [x] **T8** — Web API Contracts & Store State (`lib/api.ts`, `lib/store.ts`; preserve `MediaPlayer.tsx`)
* [x] **T9** — Frontend Keypad, Deep-Links & Cooldowns (`App.tsx` Family 8 / Guest 6, cooldown UI)
* [x] **T10** — File Browser & Confirmation Modals (`FileBrowser.tsx` Done/Esc/Tizen Back, `DeleteConfirmModal.tsx`)
* [x] **T11** — Context Menu & Device Fingerprinting (`GlobalContextMenu.tsx`, `Toasts.tsx`, `device.ts`)
* [x] **T12** — Toolchain & Repository Hygiene (`package.json`, `.eslintrc.cjs`, `tsconfig.json`, delete dead files)
* [x] **T12.1** — Pre-deploy Audit & Surgical Workflow Fixes (`main.py` sync gate, `bot.py` sync guard + `/help`, `gate4_check.py`, `smoke_db.py`, tests, `AUDIT_REPORT.md`) — NEW 2026-11-19
* [x] **T13** — Production Deployment Kit & Runbooks (`deploy/hearth.service`, `deploy/Caddyfile`, `deploy/backup-neon.sh`, `deploy/duckdns-update.sh`, `deploy/README.md`, `README.md`, historical doc banners)
* [x] **T14** — Comprehensive Test Suite & Final Hygiene (fresh clean-checkout gates, advisory review, hygiene greps, evidence, tag `v1.0-rc` → RELEASE_SHA)
* [ ] **T12.2** — Local-validation fixes (batch-delete JSONResponse + regression test; uvicorn `--no-access-log`; runbook note)
* [ ] **T12.3** — Login message polish, 10 playback speeds (owner-authorized MediaPlayer exception), DB-outage 503
* [ ] **T12.4** — DB-wake upload UX + server status button + frontend 503 guidance + stream producer cleanup
* [ ] **T12.4.1** — Frontend production dependency patch (axios / follow-redirects / form-data; production audit 3 → 0)
* [ ] **T12.5** — IPv6-only VPS Telegram connectivity (`ipv6=True` in Pyrogram `create_client`)
* [x] **T12.80** — Post-incident docs re-baseline, F-01/F-02 re-opened, mobile exceptions authorized
* [x] **T12.81** — Enforce family stream-token revocation (version claim, User.id binding, active membership)
* [x] **T12.82** — `family_members.active` is the live bot/API family authorization authority
* [x] **T12.83** — Safe upload compensation and unique `channel_message_id`
* [x] **T12.84** — Fail-safe Telegram reconciliation: dry-run sync and confirmed-gone-only cleanup
* [x] **T12.85** — Complete remaining DB-wake UX and server status; original verify-code scope already satisfied by T12.82
* [ ] **T12.86** — OWNER-AUTHORIZED MediaPlayer exception #2: mobile-only auto-landscape
* [ ] **T12.87** — OWNER-AUTHORIZED MediaPlayer exception #3: mobile-only tap controls
* [ ] **T12.88** — Mobile exception parity and final player freeze
* [ ] **T12.89** — Schema proof, deploy runbooks, proxy validation, and provenance
* [ ] **T12.90** — Reliability hardening and clean-checkout freeze candidate
* [ ] **T12.91** — Stale bundle and VPS resource recovery
* [ ] **T12.92** — Final freeze, gate rerun, and handoff (T0-R/T15-R/T16-R)
* [ ] **T0** — Verified backups BEFORE first production boot (Neon dump verified + off-host; session backup; restore procedure recorded in `deploy/BACKUP_LOG.md`) — ON HOLD; deployment paused pending T12.5 merge, owner smoke tests, and release re-freeze
* [ ] **T15** — Real-World Hardware Acceptance (Phase R + runbook deploy + Samsung TV + 512MB VPS matrix; every P0 row PASS)
* [ ] **T16** — Launch & 72-Hour Observation (GO/NO-GO, family invites, monitoring, Master Review MD → GO, tag `v1.0`) — NEW 2026-11-19

---

## Deployment Readiness (owner fills as evidence lands)

* **2026-11-20 post-incident state — CONFIRMED:** VPS origin repointed to GitHub; live SHA `c0aa30f28408add60574de9f9385912131b5524a` (`deploy-T12.7`); silent bot fixed by unconditional bot import in lifespan. WARP SOCKS5 `127.0.0.1:40000` present for GitHub IPv4 egress. Stale bundle `/opt/hearth/hearth-v1.0-rc.bundle` remains at `7629f0a`. Disk 75% (3.0/4.0 GB); RAM 210/512 MB.
* **Incident items:** A1/A2 handler-count gate is registered under T12.90; the remaining schema/proxy/provenance and VPS resource/bundle evidence is registered under T12.89/T12.91, with final live gates under T12.92. All remain **NOT VERIFIED** resolved until evidence is recorded.
* **F-01 — CONFIRMED CLOSED IN CODE by T12.81:** family stream version, `User.id` identity, and active membership checks are enforced before cache access. **VERIFY ON VPS:** live logout-all/user_remove invalidation of already-issued URLs.
* **F-02 — CONFIRMED CLOSED IN CODE by T12.82:** `family_members.active` governs bot/API authorization and verify-code for existing users; `AUTH_USERS` is only a DB-connectivity bootstrap fallback. **VERIFY ON VPS:** live membership add/remove, verify-code, and DB-wake recovery.
* **MediaPlayer exceptions:** T12.86 exception #2 mobile-only auto-landscape and T12.87 exception #3 mobile-only tap controls/center play-pause are authorized; freeze resumes after each and T12.88 completes the final freeze. TV/PC behavior and exports/localStorage keys remain protected.

* **Phase R FINAL 2026-11-19:** NO NAT64/DNS64 (native IPv4 returned; IPv4 curl failed). CONFIRMED reachable over IPv6: Telegram Bot API (HTTP 302), Telegram MTProto DC TCP (`2001:b28:f23d:f001::a:443`), Neon endpoint (2406:xx AAAA), apt/PyPI/PGDG/Let's Encrypt. IPv4-only fallbacks: DuckDNS update endpoint = set AAAA manually from PC; GitHub clone = scp release tarball/bundle from PC. Telegram MTProto LIBRARY IPv6 selection = verify at first boot (`/health/ready` Telegram connected).
* **T14 gates:** pytest 126 + npm lint/typecheck/test/build green on Python 3.13.0 / Node 20.19.5; advisories recorded; RELEASE_SHA pending owner merge + tag.
* **T12.2 gates:** pytest 127 + npm lint/typecheck/test/build green on Python 3.13.0 / Node 20.19.5; production npm advisories recorded; RELEASE_SHA pending owner merge + tag.
* **T12.4 gates:** pytest 143 + npm lint/typecheck/test/build green on Python 3.13.0 / Node 20.19.5; deployment paused.
* **T12.4.1 gates:** production npm advisories 3 → 0; npm lint/typecheck/test/build and backend pytest/compileall/pip check green on Node 20.19.5 / Python 3.13.0.
* **T12.5 gates:** pytest 143 + compileall + pip check green on Python 3.13.0; Pyrogram client configured for IPv6.
* **Release SHA:** deployment paused; re-freeze deferred until T12.5 merges and owner smoke-tests pass; owner then re-points tag `v1.0-rc`, and VPS must checkout the new SHA before deploy.
* **VPS:** NeoHeberg LXC, Debian 13 trixie, 512MB RAM + 512MB swap, ~3.1GB free disk; Python 3.13 native (explicit decision 2026-11-19).
* **Neon backup verified + off-host:** PENDING (T0)
* **Session backup:** PENDING (T0; after first boot if fresh install)
* **RELEASE_SHA (frozen at T14):** TBD
* **Pages URL / API host:** TBD / TBD
* **GO / NO-GO:** **NO-GO** (flip only per PLAN T16 criteria, with recorded evidence)

---

## Amendments

* T3→T6: family stream-token version/membership enforcement moved to T6.
* 2026-11-19: remaining work re-baselined into T12.1→T16 execution order; T0 re-sequenced to "before first production boot"; playback cap wording corrected to **household-wide 2** (code was already global); T12.1 and T16 added.
* 2026-11-19: owner-authorized one-time T12.3 exception permits only the MediaPlayer SPEEDS constant (+ minimal chip-row layout if required); freeze resumes afterward.
* 2026-11-20: F-01 and F-02 were re-opened by owner authorization and are now closed in code by T12.81/T12.82; live VPS verification remains. T12.86 and T12.87 add the two owner-authorized mobile-only MediaPlayer exceptions; TV/PC behavior, exports, and localStorage keys remain unchanged.

## Deferred notes (status updated 2026-11-19)

* ~~routers/auth.py `_get_or_create_family_user` hardcodes role="admin"~~ — RESOLVED in T5 (reads family_members).
* ~~bot.get_or_create_user uses settings.auth_users~~ — RESOLVED in T5 (family_members is single source of truth).
* app/__init__.py eagerly imports app.main (import side effects) — STILL OPEN; P2 post-launch hygiene, NOT a deploy blocker (production env is present; session dir creation at import is intended).
* test_schema_migration.py patched_db monkeypatch.undo() teardown — fragile but green; leave unless it breaks.

---

## Session Execution Log

*(Append one line per completed task: `YYYY-MM-DD | Task | Gate result` — NO commit SHA; git log is authoritative. Legacy lines below predate the no-SHA rule and are preserved verbatim.)*

* `2026-11-18 | T0 | 5f0d769 | Baseline verified; plan, progress, and handoff files initialized.`
* `2026-11-18 | T1 | fresh-venv install + pip check + imports OK (pyrotgfork 2.2.24.1); .env.example rewritten as fail-closed Neon template; aiosqlite added to dev deps`
* `2026-11-18 | T2 | full pytest green (String(10), guest default, family_members seed, idempotent init_db, sqlite pool-kwargs fix); merged via PR #8 at 07d2130`
* `2026-11-18 | T4 | full pytest green (helper failure removal, clients[:] in-place identity, bounded FloodWait delete retry, started-only shutdown)`
* `2026-11-18 | T5 | full pytest green (callback auth gate, user add/remove with token revocation, sessions/kick, guest status, paginated myfiles, family_members as single source of truth)`
* `2026-11-18 | T6 | full pytest green (nosniff+CSP, safe disposition, family token version/membership checks, heartbeat ownership enforcement, cache bounds, slowapi removed)`
* `2026-11-18 | T7 | full pytest green (atomic progress upsert, batch delete error reporting, guest delete protection, newest-first sorting, pagination)`
* `2026-11-18 | T8 | npm typecheck + test + build green (api.ts rewritten without folder functions, logout=this-device-only, fail-closed useMe, 429/409 handling; store.ts stripped folder state, role='unknown' default, toast auto-dismiss)`
* `2026-11-18 | T9 | npm typecheck + test + build green; pytest 120 passed (8-digit Family / 6-digit Guest keypad, server-driven cooldown, deep-link login, QR UI and encoder removed)`
* `2026-11-18 | T10 | npm typecheck + test green (Manage-mode Done/Esc/Tizen Back exit, focus restoration, unified DeleteConfirmModal with Cancel default focus and Telegram warning)`
* `2026-11-18 | T11 | npm typecheck + test green (GlobalContextMenu blob leak fixed via LRU eviction, dead folder code removed, Toasts timer cleanup verified, device ID stability confirmed)`
* `2026-11-18 | T12 | npm typecheck + lint + build green, pytest green (deleted dead Docker/tv.py/patch.py files, added ESLint config, fixed TSConfig deprecation)`
* `2026-11-19 | PLAN | docs re-baseline: HANDOFF/PLAN/PROGRESS v2 for deploy run (T12.1→T16); full static audit of baseline 8492667 completed (120 tests counted, compileall PASS, contracts verified); owner-committed, docs only`
* `2026-11-19 | T12.1 | pytest 126 passed; compileall PASS; pip check PASS; npm ci/lint/typecheck/test/build all green (13 frontend tests); docs environment deltas applied`
* `2026-11-19 | T13 | deployment kit created (systemd unit, Caddyfile, backup+duckdns scripts, IPv6-only runbook, README/docs rewritten); gates: script syntax + static config review, zero app-code diff`
* `2026-11-19 | T14 | clean-checkout gates green (pytest 126; npm lint/typecheck/test/build); pip check + advisory scan recorded; hygiene clean; MediaPlayer frozen; Phase R final recorded`
* `2026-11-19 | T12.2 | fixed batch-delete tuple→JSONResponse (200/207) + regression test; uvicorn --no-access-log to stop signed-URL logging; gates re-run green`
* `2026-11-19 | T12.3 | pytest 132 + compileall/pip check and npm lint/typecheck/test/build green; 10 playback speeds; DB connection failures return 503; owner local acceptance pending`
* `2026-11-19 | T12.4 | DB-wake upload UX + server_status button + frontend 503 guidance + stream producer cleanup; gates green (143 pytest, 14 frontend)`
* `2026-11-19 | T12.4.1 | patched axios/follow-redirects/form-data (prod advisories 3 → 0, no --force, majors unchanged); all gates green (frontend 14 tests; backend 143 tests)`
* `2026-11-19 | T12.5 | added ipv6=True to Pyrogram Client for IPv6-only VPS compatibility`
* `2026-11-20 | T12.80 | gate passed: 149 backend tests; compileall; pip check; npm ci/lint/typecheck; 14 frontend tests; build; dist/_redirects present; MediaPlayer diff empty; docs-only`
* `2026-11-20 | T12.81 | gate passed: pytest 157; compileall; pip check; npm ci/lint/typecheck; 14 frontend tests; build; dist/_redirects present; family revocation tests green`
* `2026-11-20 | T12.82 | gate passed: pytest 162 (61 warnings); compileall; pip check; npm ci/lint/typecheck; 14 frontend tests; build; dist/_redirects present; family membership authorization tests green`
* `2026-11-20 | T12.83 | gate passed: pytest 167 (61 warnings); compileall; pip check; npm ci/lint/typecheck; 14 frontend tests; build; dist/_redirects present; upload compensation and unique-index tests green`
* `2026-11-20 | T12.84 | gate passed: pytest 177 (61 warnings); compileall; pip check; Node 20.19.5/npm 10.8.2 ci/lint/typecheck; 14 frontend tests; build; dist/_redirects present; fail-safe reconciliation tests green`
* `2026-11-20 | T12.85 | gate passed: pytest 190 (61 warnings); compileall; pip check; Node 20.19.5/npm 10.8.2 npm ci/lint/typecheck; 14 frontend tests; build; dist/_redirects present; MediaPlayer diff empty`

**T0 status:** ON HOLD pending T12.5 merge, owner smoke tests, and release re-freeze. Do not run backups until the owner resumes T0.

**Note:** T0 is REQUIRED before the FIRST production boot (not before T2 — that dev work already shipped under its own gates). Agent never creates/merges PRs; owner merges after reading the agent report.