# Progress — Update After EVERY Commit

**This file is the single source of truth for execution state across sessions.**

* **Audited Code Baseline:** `84926670051242bbbcd5afae378aa6f319ded062` (main; T1–T12 merged via PR #16; full static audit 2026-11-19)
* **Historical Dev Baseline:** `5f0d769d7c8c143f27e419da90622505d153bcf0` (T1–T12 era; see git history)
* **Active Branch:** `hearth/t13.11`
* **Current Task:** `OWNER deploy step`
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
* [x] **T12.2** — Local-validation fixes (batch-delete JSONResponse + regression test; uvicorn `--no-access-log`; runbook note)
* [x] **T12.3** — Login message polish, 10 playback speeds (owner-authorized MediaPlayer exception), DB-outage 503
* [x] **T12.4** — DB-wake upload UX + server status button + frontend 503 guidance + stream producer cleanup
* [x] **T12.4.1** — Frontend production dependency patch (axios / follow-redirects / form-data; production audit 3 → 0)
* [x] **T12.5** — IPv6-only VPS Telegram connectivity (`ipv6=True` in Pyrogram `create_client`)
* [x] **T12.80** — Post-incident docs re-baseline, F-01/F-02 re-opened, mobile exceptions authorized
* [x] **T12.81** — Enforce family stream-token revocation (version claim, User.id binding, active membership)
* [x] **T12.82** — `family_members.active` is the live bot/API family authorization authority
* [x] **T12.83** — Safe upload compensation and unique `channel_message_id`
* [x] **T12.84** — Fail-safe Telegram reconciliation: dry-run sync and confirmed-gone-only cleanup
* [x] **T12.85** — Complete remaining DB-wake UX and server status; original verify-code scope already satisfied by T12.82
* [x] **T12.86** — OWNER-AUTHORIZED MediaPlayer exception #2: mobile-only auto-landscape
* [x] **T12.87** — OWNER-AUTHORIZED MediaPlayer exception #3: mobile-only tap controls
* [x] **T12.88** — Mobile exception parity and final player freeze
* [x] **T12.89** — Schema proof, deploy runbooks, proxy validation, and provenance
* [x] **T12.90** — Reliability hardening, banner replacement, and clean-checkout freeze candidate
* [x] **T12.90.1** — Persistent auth-key failure threshold; close Finding B
* [x] **T12.90.2** — OWNER-AUTHORIZED MediaPlayer exception #4: pseudo-landscape slider axis fix and final freeze gates
* [x] **T13.1** — Phase authorization and docs re-baseline (docs only)
* [x] **T13.2** — Issue 1: remove bottom-bar volume cluster (all devices)
* [x] **T13.3** — Issue 7: controls auto-hide 4s to 3s (all devices)
* [x] **T13.4** — Issue 2: phone portrait-first player and compact controls
* [x] **T13.5** — Issue 3: glass center play/pause button (visual only)
* [x] **T13.6** — Issue 4: phone brightness/volume drag gestures and indicator
* [x] **T13.7** — Issue 5: TV/PC/tablet side controls and D-pad navigation
* [x] **T13.8** — Issue 8: phone control lock with drag-to-pause/play
* [x] **T13.8.1** — OWNER-AUTHORIZED Exception #5.7.1: phone lock UX polish
* [x] **T13.8.2** — OWNER-AUTHORIZED Exception #5.7.2: phone lock state icons, drag dot, and notice copy
* [x] **T13.9** — Issue 6a: household playback count endpoint
* [x] **T13.10** — Issue 6b: home live-devices chip, popup text, and flow verification
* [x] **T13.11** — Final freeze gates, RC candidate, and deploy handoff (docs only)
* [ ] **T12.91** — Stale bundle and VPS resource recovery — ON HOLD
* [ ] **T12.92** — Final freeze, gate rerun, and handoff (T0-R/T15-R/T16-R) — ON HOLD
* [ ] **T0** — Verified backups BEFORE first production boot (Neon dump verified + off-host; session backup; restore procedure recorded in `deploy/BACKUP_LOG.md`) — ON HOLD
* [ ] **T15** — Real-World Hardware Acceptance (Phase R + runbook deploy + Samsung TV + 512MB VPS matrix; every P0 row PASS) — ON HOLD
* [ ] **T16** — Launch & 72-Hour Observation (GO/NO-GO, family invites, monitoring, Master Review MD → GO, tag `v1.0`) — ON HOLD; NEW 2026-11-19

### T13 execution map and dependencies

The bare **T13 Deployment Kit** is already complete; this phase is the T13.x sequence below.

| Workstream | Dependency / order |
|---|---|
| Player controls | T13.2 → T13.4 → T13.6 → T13.7 → T13.8 → T13.8.1 → T13.8.2 |
| Playback count | T13.9 → T13.10 |
| Independent player changes | T13.3 and T13.5 are independent of the player-controls chain |
| Phase closeout | T13.11 follows completion of T13.2–T13.10 |

T12.91, T12.92, T0, T15, and T16 remain **ON HOLD** during this phase.

---

## Deployment Readiness (owner fills as evidence lands)

* **2026-11-20 post-incident state — CONFIRMED:** VPS origin repointed to GitHub; live SHA `c0aa30f28408add60574de9f9385912131b5524a` (`deploy-T12.7`); silent bot fixed by unconditional bot import in lifespan. WARP SOCKS5 `127.0.0.1:40000` present for GitHub IPv4 egress. Stale bundle `/opt/hearth/hearth-v1.0-rc.bundle` remains at `7629f0a`. Disk 75% (3.0/4.0 GB); RAM 210/512 MB.
* **Incident items:** A1/A2 handler-count fail-fast is **CONFIRMED in code/tests by T12.90**; runtime VPS behavior is **VERIFY ON VPS**. Schema/proxy/provenance are T12.89, VPS bundle/resources are T12.91, and live release gates are T12.92.
* **T12.90 freeze candidate:** clean-checkout test commit `e9f170459ad532020907325472f538408029048c`, tree `d84fe1abbd34f41d9b1d4e8454a0938a944c3648` (base `a0499775e410465f503fe148aee0959b859bc479`); **SUPERSEDED by T12.90.2** below. Owner tags `deploy-T12.90-rc` only after merge.
* **T12.90 banner:** **CONFIRMED** source/destination SHA-256 match; tracked blob and final commit inclusion are checked before handoff.
* **Finding B — CONFIRMED CLOSED IN CODE by T12.90.1:** per-client auth-key failures must reach 3 within 60 seconds before quarantine; successful lookup/chunk delivery clears the counter. **VERIFY ON VPS:** live transient recovery and the persistent-failure operator workflow.
* **T12.90.2 freeze candidate — CONFIRMED:** clean-checkout snapshot SHA `81c41f02c40b60620a9f5c84484f53177af99c72`, tree `fbfe33b3f77f0a2a7980b65e7c0c8eb3d530f5ba`, based on latest `main` `f1f656375f88990332fe3078e70a8e893860085d`; supersedes `e9f1704`. Gate evidence append changed documentation only; tested implementation/tests remain identical. **VERIFY ON DEVICE:** iPhone pseudo-landscape seek/volume drags, orientation exit, Android native lock.
* **T13.11 RC code candidate — CONFIRMED:** clean-checkout gates ran against `main` commit `c7d82f53f28fb823c79fb047aec4794fd63a84ba`, tree `ca77f9ac70da58a4fa152e8a27d24268be3005f6`; 230 backend tests and 88 frontend tests passed. The owner tags the merged T13.11 commit on `main`; this candidate is not the final tag target if merge creates a different commit.
* **ON HOLD:** T12.91, T0-R, T12.92, T15-R, and T16-R; deployment/release remains NO-GO pending owner authorization and required VPS evidence.
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
* `2026-11-20 | T12.86 | gate passed: pytest 190 (61 warnings); compileall; pip check; Node 20.19.5/npm 10.8.2 npm ci/lint/typecheck; 166 frontend tests; build; dist/_redirects present`
* `2026-11-20 | T12.87 | gate passed: pytest 190 (61 warnings); compileall; pip check; Node 20.19.5/npm 10.8.2 npm ci/lint/typecheck; 170 frontend tests; build; dist/_redirects present`
* `2026-11-20 | T12.88 | gate passed: pytest 190 (61 warnings); compileall; pip check; Node 20.19.5/npm 10.8.2 npm ci/lint/typecheck; 170 frontend tests; build; dist/_redirects present; parity source checks passed; MediaPlayer task diff empty`
* `2026-11-20 | T12.89 | gate passed: 208 backend tests (61 warnings), compileall, pip check; Node 20.20.2/npm 11.20.0 npm ci/lint/typecheck, 170 frontend tests, build, dist/_redirects present; schema/proxy regression tests green`
* `2026-11-20 | T12.90 | backend 221 passed (61 warnings), compileall and pip check; frontend lint/typecheck and 170 tests/build passed; prod npm audit 0, pip-audit findings recorded; banner replaced and verified`
* `2026-11-20 | T12.90.1 | backend 226 passed (61 warnings), compileall and pip check; focused auth-key tests 13 passed; frontend lint/typecheck and 170 tests/build passed; prod npm audit 0`
* `2026-11-20 | T12.90.2 | gate passed: clean-checkout pytest 226 (61 warnings), compileall, pip check; pip-audit 22 advisory rows recorded; Node 20.20.2/npm 10.8.2 lint/typecheck and 178 frontend tests/build passed; npm audit production 0`
* `2026-11-20 | T13.1 | baseline gates passed: 226 backend tests (61 warnings); 178 frontend tests; lint 0 warnings; production npm audit 0; build and dist/_redirects passed`
* `2026-11-20 | T13.2 | gate passed: pytest 226 (61 warnings); compileall and pip check; Node 20.20.2/npm 10.8.2 lint/typecheck; 178 frontend tests; build and dist/_redirects; production audit 0`
* `2026-11-20 | T13.3 | gate passed: pytest 226 (61 warnings); compileall and pip check; Node 20.20.2/npm 10.8.2 lint 0 warnings/typecheck; 178 frontend tests; build and dist/_redirects; production audit 0`
* `2026-11-20 | T13.4 | gate passed: pytest 226 (61 warnings); compileall and pip check; Node 20.20.2/npm 10.8.2 lint 0 warnings/typecheck; 35 frontend tests; build and dist/_redirects; production audit 0`
* `2026-11-20 | T13.5 | gate passed: pytest 226 (61 warnings); compileall and pip check; Node 20.20.2/npm 10.8.2 lint 0 warnings/typecheck; 35 frontend tests; build and dist/_redirects; production audit 0`
* `2026-11-20 | T13.6 | gate passed: pytest 226 (61 warnings); compileall and pip check; Node 20.20.2/npm 10.8.2 lint 0 warnings/typecheck; 44 frontend tests; build (1,529 modules) and dist/_redirects; production audit 0`
* `2026-11-20 | T13.7 | gate passed: pytest 226 (61 warnings); compileall and pip check; Node 20.20.2 lint 0 warnings/typecheck; 44 frontend tests; build (1,529 modules) and dist/_redirects; production audit 0`
* `2026-11-20 | T13.8 | gate passed: pytest 226 (61 warnings); compileall and pip check; Node 20.20.2/npm 10.8.2 lint 0 warnings/typecheck; 61 frontend tests; build (1,529 modules) and dist/_redirects; production audit 0`
* `2026-11-20 | T13.9 | gate passed: pytest 230 (61 warnings); compileall and pip check; Node 20.20.2/npm 10.8.2 lint 0 warnings/typecheck; 61 frontend tests; build (1,529 modules) and dist/_redirects; production audit 0`
* `2026-11-20 | T13.8.1 | gate passed: Node 20.20.2/npm 10.8.2 lint 0 warnings/typecheck; 78 frontend tests; build (1,529 modules) and dist/_redirects; no backend changes; Current Task remains T13.10`
* `2026-11-20 | T13.8.2 | gate passed: Node 20.20.2/npm 10.8.2 npm ci; focused 64 and full 78 frontend tests (baseline unchanged); lint 0 warnings/typecheck/build (1,529 modules); dist/_redirects present; Current Task remains T13.10`
* `2026-11-20 | T13.10 | gate passed: pytest 230 (61 warnings); compileall and pip check; Node 20.20.2/npm 10.8.2 npm ci; lint 0 warnings/typecheck; 88 frontend tests; build (1,530 modules) and dist/_redirects; production audit 0`
* `2026-11-20 | T13.11 | clean-checkout gates passed: 230 backend tests; Node 20.20.2/npm 10.8.2 lint 0 warnings/typecheck; 88 frontend tests; build (1,530 modules); dist/_redirects; production audit 0; docs-only freeze and owner deploy handoff`

**T0 status:** ON HOLD pending T12.5 merge, owner smoke tests, and release re-freeze. Do not run backups until the owner resumes T0.

**Note:** T0 is REQUIRED before the FIRST production boot (not before T2 — that dev work already shipped under its own gates). Agent never creates/merges PRs; owner merges after reading the agent report.