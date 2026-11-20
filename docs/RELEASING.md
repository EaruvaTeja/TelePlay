# Hearth Release and Deployment

Hearth is deployed as a web application: Cloudflare Pages publishes the web
client from `main`, and the owner deploys the backend to the VPS from a reviewed
Git tag. This replaces the obsolete Android APK release instructions.

The owner performs and approves every production tag and deployment. The coding
agent must not create tags, deploy, or merge the release PR.

## T13.11 release candidate

After the owner merges the reviewed T13.11 PR:

```bash
git checkout main
git pull
git rev-parse HEAD
git tag deploy-T13.11-rc
git push origin deploy-T13.11-rc
```

Before tagging, verify that `HEAD` is the merged T13.11 commit. The final merge
commit may differ from the tested code-candidate commit; tag the merged commit
on `main`, not the feature branch. The tag is the pinned VPS release.

Cloudflare Pages auto-publishes from `main`. Confirm that `teleplay.pages.dev`
serves the final build after the merge, then hard-refresh the site.

## VPS deployment

Follow [deploy/README.md](../deploy/README.md), especially its section 4 and
security requirements. For the T13.11 update, the owner checks out the pinned
tag in the existing application checkout:

```bash
sudo -u hearth git -C /opt/hearth/app fetch --tags
sudo -u hearth git -C /opt/hearth/app checkout --detach deploy-T13.11-rc
sudo systemctl restart hearth
curl -fsS http://127.0.0.1:8000/health/ready
sudo journalctl -u hearth -n 50 --no-pager
```

Confirm readiness, registered bot handlers, and the expected service state in
the journal. Then make an authenticated `GET /api/playback/count` request and
confirm the response contains only `{"active":N,"limit":2}`. T13.11 changes no
dependencies, so do not reinstall them for this release.

## Acceptance smoke checks

- **Phone:** Portrait launch, all controls visible, Android and iPhone
  fullscreen entry/exit, left/right drag indicators only while dragging, lock
  handle, hold-to-unlock progress, drag-to-pause/play, unlock, and compact lock
  notices.
- **Phone / PC / TV:** Controls hide after 3 seconds. Verify the glass center
  play button on dark and bright frames.
- **PC / TV:** Side brightness/volume controls and navigation work. On TV, the
  D-pad reaches both side clusters, held OK ramps values, and the pre-existing
  keys still behave as documented in `AUDIT_REPORT.md`.
- **Playback limit:** Two devices playing and a third attempt displays
  “Maximum watch devices reached”; chip count 1 is green and count 2 is orange.
  Stopping or closing a player frees its slot, or the slot expires within about
  75 seconds.

## Rollback

There are no dependency or database-schema changes in T13.11. If backend
rollback is required, restore the previous VPS tag and restart the service:

```bash
sudo -u hearth git -C /opt/hearth/app checkout --detach deploy-T12.90.2-rc
sudo systemctl restart hearth
```

The new web build is compatible with the old server: the live-devices chip
silently stays hidden when the count endpoint returns 404/405. If needed, roll
Cloudflare Pages back to the previous deployment.
