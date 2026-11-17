# ytpublic — Operational Guide

`ytpublic` is an independent recorder worker for videos **already uploaded to the authorized YouTube channel**. It changes eligible videos from **private to public**, using YouTube titles and current status plus its own safety state. Publication is externally visible: review dry-run candidates before permitting updates.

This guide describes the current implementation, not a live API acceptance result. **Runtime behavior has not been verified against the live YouTube API.** The [implementation plan](RECORDER_YTPUBLIC_IMPLEMENTATION_PLAN.md) is design history; its design-only status and proposals are not the operational source of truth.

## Scope and isolation

- Start explicitly with `python -m recorder.main --mode ytpublic` or the dedicated `mypage48-ytpublic.service`.
- `all` remains unchanged: it does **not** include ytpublic. Neither record, upload, theater nor gdrive implicitly starts it.
- Disabled by default; a disabled service stays alive and idle without YouTube requests. Configuration is loaded at startup; restart to apply changes.
- No backend heartbeat is sent for this role. An active systemd process alone does not prove publication is progressing; inspect its logs.
- No publication inputs from recorder metadata, backend replay/live history, Drive manifests, staging, upload history, or source media. It does not upload videos or delete remote videos or local/Drive source folders.
- Recording, upload queues, R2, Drive pools, cleanup, notifications and uploader privacy selection remain independent. The worker does not touch `.youtube_cooldown` or `.gdrive_youtube_delay`.

## Publication rules

Comparison collapses whitespace and is case-insensitive; it does not edit the actual title. Earlier exclusions take precedence:

1. Skip a video with a successful `published` receipt, even if manually made private later.
2. Skip explicitly excluded video IDs.
3. Skip public, **unlisted**, missing/unknown privacy status, and anything other than private.
4. Skip an existing YouTube `publishAt` schedule.
5. Skip titles containing both standalone `IDN` and `SHOWROOM`: mixed-platform ambiguity fails closed.
6. A remaining private video containing standalone `SHOWROOM` anywhere is immediately eligible, without date parsing. `MYSHOWROOM` is not a match. This is keyword selection, not proof of a recording's origin.
7. Otherwise require the complete member IDN format below and wait for its deadline. Unsupported titles, invalid dates or ambiguity fail closed; no fallback to upload time.

```text
LIVE IDN <member text> JKT48 | <Indonesian weekday>, <day> <Indonesian month> <year> <HH:MM> WIB
LIVE IDN Erine JKT48 | Senin, 16 November 2026 21:10 WIB
```

IDN requires a nonempty member segment, a valid calendar date/time, an Indonesian weekday matching that date, an Indonesian month name, and year 2000–2100. WIB is fixed UTC+7 regardless of host timezone; comparisons use aware UTC times. Future starts remain waiting.

### IDN timing: 72 + 8 hours from the title's start

```text
eligible_at = title_start_at + base_delay_hours + buffer_hours
             = title_start_at + 72 hours + 8 hours  # default: 80 hours
```

The example above becomes eligible on **20 November 2026 at 05:10 WIB** (19 November at 22:10 UTC).

**The actual live end is not known.** The extra eight hours approximate waiting 72 hours after the end, assuming the live ends within eight hours of its start. A longer live breaks that assumption: this does not guarantee 72 hours after its actual end and does not verify IDN policy compliance. Exclude videos requiring exact end-time enforcement or choose an appropriately conservative buffer.

SHOWROOM has no IDN embargo or uploader-delay dependency, but “immediate” means **eligible**, not guaranteed immediate publication: every real update still obeys polling, backlog ordering, spacing, scan/day caps and quota.

Title-only selection cannot distinguish intentionally private videos from temporary embargo videos with matching titles, nor recover publication history outside this worker. Review candidates and use exclusions.

## Configuration and credentials

Set these in `recorder/.env` (the config also reads `recorder/src/.env`; process environment can override settings). All ten ytpublic settings are shown, with their defaults:

```dotenv
REC_YTPUBLIC_ENABLED=false
REC_YTPUBLIC_DRY_RUN=true
REC_YTPUBLIC_POLL_INTERVAL=900
REC_YTPUBLIC_BASE_DELAY_HOURS=72
REC_YTPUBLIC_BUFFER_HOURS=8
REC_YTPUBLIC_EXCLUDE_VIDEO_IDS=
REC_YTPUBLIC_MAX_UPDATES_PER_DAY=80
REC_YTPUBLIC_MAX_UPDATES_PER_SCAN=5
REC_YTPUBLIC_UPDATE_INTERVAL_SECONDS=30
REC_YTPUBLIC_DAILY_QUOTA_BUDGET=5000

# Existing shared YouTube OAuth settings; reuse your existing values.
REC_GOOGLE_CLIENT_ID=your-existing-client-id
REC_GOOGLE_CLIENT_SECRET=your-existing-client-secret
REC_YOUTUBE_REFRESH_TOKEN=your-existing-youtube-refresh-token

# Existing logging settings; this explicit relative directory assumes repo-root cwd.
REC_LOG_LEVEL=INFO
REC_LOG_MODE=stdout
REC_LOGS_DIR=recorder/logs
```

Do not replace working secrets with the illustrative values above or commit credentials. The existing YouTube refresh token and OAuth client are shared; **no new auth script, new scope, or Drive authorization is needed**. The existing integration requests `youtube.upload` and full `youtube` scopes; the latter supports status updates. An invalid/revoked or insufficiently authorized existing token still needs correction, not repeated publication attempts.

| Setting | Constraint / meaning |
|---|---|
| `POLL_INTERVAL` | Seconds, minimum 60; default 900 between normal scans, not a guaranteed publication deadline |
| `BASE_DELAY_HOURS` | Integer, minimum 72; IDN only |
| `BUFFER_HOURS` | Integer, minimum 0; IDN end-time approximation, default 8 |
| `EXCLUDE_VIDEO_IDS` | Comma-separated exact 11-character YouTube IDs; whitespace/empty entries removed and duplicates collapsed; applies to both branches |
| `MAX_UPDATES_PER_DAY` | Positive integer; default 80 **attempts**, not successes |
| `MAX_UPDATES_PER_SCAN` | Positive integer; default 5 real update attempts per scan |
| `UPDATE_INTERVAL_SECONDS` | Nonnegative integer; default 30 seconds between reserved attempts, persisted across restart |
| `DAILY_QUOTA_BUDGET` | Integer, minimum 51; default 5,000 estimated units for all this worker's Data API requests |

For the table, setting names have prefix `REC_YTPUBLIC_`. Increasing the buffer affects unpublished candidates; it does not undo publication. `REC_YOUTUBE_PRIVACY_STATUS` remains the uploader's setting, not ytpublic's publication switch. Existing unlisted uploads remain unlisted; do not change upload defaults globally merely to populate this worker.

## Discovery, caching and fresh checks

1. Discover exactly one authorized channel and its uploads playlist; reject ambiguous channel selection or a persisted catalog belonging to another channel.
2. Initially paginate the **entire uploads playlist**, up to 50 IDs per page, and fetch `snippet,status` in batches of up to 50. Persist pagination progress and cached resources. A large initial scan can consume the daily read budget before publication begins; it resumes from checkpoints rather than pretending to be complete.
3. Once the full scan is complete, inspect the uploads **head for new uploads**, paging until a known ID is encountered or the playlist ends. Fetch new resources and rotate through **up to 50 known video statuses per scan**. This limits repeated full-channel reads.
4. Reevaluate cached resources each scan; cached waiting candidates can become due as time passes without another full enumeration. Order candidates deterministically by parsed IDN start or SHOWROOM snippet `publishedAt`, then ID. The latter is ordering only, not an embargo source.
5. Before **every actual publication candidate update**, wait for spacing, fetch its current title/status again and rerun the policy and receipt checks. Missing resources are removed from the active cache; changed privacy, title or schedule can block the update. Update `status` only, retaining applicable writable status fields; do not overwrite title/description.

On a large channel, edits to older known videos may not be noticed until their rotating refresh reaches them. This can delay detection of newly eligible edits. A stale eligible cache entry cannot alone authorize an update: **cached/pending retries always need fresh validation**. Dry-run previews use cached decisions and do not perform the per-candidate pre-update fetch, so they are not a guarantee of current live status for every old video.

## Quota, caps and backlogs

Both platforms share the default **80 update attempts/day**, **5 attempts/scan**, **30-second spacing**, and **5,000 estimated units/day**. Reads reserve one unit per list request/page/batch; status updates reserve 50 units. All budgeted requests reserve durably **before dispatch**, including failed calls, initial discovery, pagination, rotating refreshes, fresh pre-update checks, reconciliation reads, and dry-run reads. SDK request retries and automatic 401 replay are disabled to avoid unmetered attempts.

Dry-run sends no privacy updates and creates no new publication-intent/success receipts for candidates. It still writes catalog/quota state, spends read quota, and can reconcile an existing ambiguous receipt by reads. It is read-only with respect to remote privacy, not a zero-network or zero-local-write mode.

The durable ledger counts failures and ambiguous attempts conservatively; reservations can exceed actual billed usage. It is **worker-local accounting**, not remaining Google project quota and not a quota reservation against other clients. Uploader thumbnail/playlist calls and other applications still share project capacity; compare with Google Cloud Console during rollout. Read-heavy scans can allow fewer than 80 updates.

Quota days reset at **midnight Pacific**, using `America/Los_Angeles` calendar boundaries including DST (not server midnight, a fixed UTC offset, or always 24 hours). Daily caps/budget exhaustion wait for the next reset; actual API `quotaExceeded`/`dailyLimitExceeded` persists a worker-specific pause until reset. Remaining candidates stay private and are revalidated later. Restart does not reset limits or spacing. A static 200-video backlog needs at least three quota days at the default cap, and may take longer due to reads, failures or new arrivals.

## Durable state and reconciliation

Default locations (all state paths follow `REC_LOGS_DIR`, independently of log output mode):

```text
recorder/src/ytpublic/
  __init__.py
  policy.py                 # Pure classification and time policy
  client.py                 # Metered reads and status updates
  state.py                  # Durable catalog, ledger and receipts
  service.py                # Scan loop, gates, retry/pause and reconciliation
recorder/logs/
  ytpublic.log              # File-mode logger / installed service output
  ytpublic/
    .lock                   # State transaction lock
    catalog.json            # Channel, cached resources, pagination and rotation cursor
    quota.json              # Pacific day, attempt/unit reservations, spacing and quota pause
    receipts/
      <video_id>.json       # Publication intent/outcome and policy evidence
```

The service also uses the shared process-lock utility for role `ytpublic`, rejecting duplicate local instances using the same logs directory while allowing other roles. Do not use different logs directories to bypass that lock or reset counters on the same channel.

Writes use restricted permissions, atomic replacement and durable checkpoints. Invalid/corrupt state or channel mismatches fail closed and pause for manual review rather than resetting counters. **Do not delete, move, replace or edit state/lock folders while the worker is active.** Retain durable state across deployments and back it up while stopped; it is not disposable log rotation data. Deleting it loses attempt accounting, discovery progress and publication history and can permit unwanted republication.

Receipts contain the schema/video/channel IDs, matched rule, observed title, IDN start/deadline/base/buffer (null for SHOWROOM), attempt/publication timestamps and one of:

- `publishing`: intent saved after quota reservation and before dispatch.
- `published`: a confirmed public response or subsequent public-state reconciliation. Prevents automatic republication if later made private manually.
- `needs_reconciliation`: ambiguous failure/unconfirmed result; no blind retry.

For `publishing` or `needs_reconciliation`, the worker reads current YouTube state. Public becomes confirmed success without another update. Private, unlisted or missing remains blocked for manual review; unlisted is never overridden. A private result does not prove that an earlier request never succeeded or that a person never changed it back.

### Manual reconciliation procedure

1. Stop **only** ytpublic and wait for in-flight work to finish. Back up its entire state directory; retain quota reservations.
2. Inspect the specific receipt and actual video/channel in YouTube Studio, including title, privacy and schedule. Check available logs/history and establish operator intent; do not infer it from a private status alone.
3. If already public, restarting allows read-based success reconciliation. If it must stay nonpublic, add its ID to exclusions and preserve the ambiguous receipt as evidence; reconciliation may continue logging it, but must not update it.
4. If a new attempt is explicitly approved for a still-private video, an operator may archive and remove **only that video's ambiguous receipt while stopped**, after preserving the evidence and checking policy/exclusions. This is a deliberate reauthorization of a potentially repeated update, not routine recovery. Never clear the whole receipts folder, remove a successful receipt to force republication, or reset `quota.json` to get another attempt. There is no dedicated reconciliation CLI.
5. Restart and monitor fresh validation and the new outcome. For malformed state, restore a verified backup or repair only after understanding the safety failure; do not delete state to silence the pause.

## Running and observing

From the repository root, with recorder dependencies installed and the existing virtualenv active:

```bash
python -m recorder.main --mode ytpublic
```

This is a long-running loop, not a one-shot command. There is no `--dry-run` CLI flag; use `REC_YTPUBLIC_DRY_RUN`. Stop gracefully with Ctrl+C/SIGTERM and allow in-flight API work to finish; forced termination may leave an intent requiring reconciliation.

On Linux, `recorder/setup-recorder.sh` installs/enables the dedicated unit alongside the existing recorder units. The setup script manages **all** those services, so review its environment/path assumptions and broader effects before running it on an existing deployment. Starting the unit does not override the enable/dry-run switches. Once installed:

```bash
sudo systemctl status mypage48-ytpublic.service
sudo systemctl restart mypage48-ytpublic.service
sudo systemctl stop mypage48-ytpublic.service
sudo systemctl cat mypage48-ytpublic.service
```

`REC_LOG_MODE=file` writes the dedicated `ytpublic` logger to `<REC_LOGS_DIR>/ytpublic.log`. `stdout` writes to stdout; the installed unit appends stdout/stderr to its configured `recorder/logs/ytpublic.log` path. If changing `REC_LOGS_DIR`, inspect the unit too: systemd redirection is a generated fixed path, not dynamically derived from that setting. `journalctl -u mypage48-ytpublic.service` helps inspect lifecycle failures, but redirected application messages are in the file, not necessarily the journal.

Look for `SCAN`, `WAIT`, `SKIP`, `DRY-RUN`, `PUBLIC`, `SUMMARY` and `IDLE`, with per-scan/daily counts, local estimated units and reset timestamps. Unchanged per-video decisions are deduplicated in memory; they can appear again after restart. A limit/error-interrupted scan is not a completed empty scan.

- Missing/revoked/rejected authorization: one CRITICAL message, then service remains alive **paused until credentials are corrected and ytpublic restarted**. No hot reload or repeated auth loop.
- State/safety error: CRITICAL and manual-review pause; inspect state before restart.
- Temporary network/token or API failures: exponential backoff with jitter (up to roughly 900 seconds plus jitter); permission errors are not assumed successes. Ambiguous dispatched updates are protected by receipts.
- Daily API quota error: durable pause to Pacific reset, independent of upload/Drive timing files.

## Safe rollout

1. Deploy disabled (`ENABLED=false`, `DRY_RUN=true`); keep existing services unchanged.
2. Reuse the working channel OAuth credentials, confirm the intended channel and persistent logs/state location, then enable with dry-run still true and restart **only ytpublic**.
3. Allow the initial full scan to finish, possibly across quota days. Review old/new member IDN, SHOWROOM keyword-only titles, mixed titles, unlisted, scheduled, malformed and intentionally private examples. Add exclusions and acknowledge the 72+8 end-time assumption.
4. Compare local read estimates/log volume with actual Cloud project usage, including uploader activity. Reduce caps/budget as needed; dry-run itself spends reads.
5. Only after approval, set `DRY_RUN=false` and restart. Start with an operator-approved video safe to publish and conservative caps/exclusions; verify public status and its receipt before expanding.
6. Verify restart persistence and that a successful receipt prevents republication after a manual return to private. Keep backups and monitor failures/reconciliation, caps and quota headroom.
7. To halt future updates, stop ytpublic or disable and restart it. This does **not** revert already-public videos; address any unintended exposure manually in YouTube Studio.

These are required live acceptance steps, not a claim they have already passed. Offline tests and source review cannot prove actual channel authorization, API compatibility or production quota headroom.
