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

### Observed uploads-playlist discovery discrepancy

During a production investigation on 17 November 2026, **14 known channel videos were absent from uploads-playlist enumeration**, although a direct `videos.list(part="snippet,status", id=...)` lookup using the same OAuth credentials returned **all 14 resources**, with their owning channel matching the authorized channel.

A separate full enumeration followed `nextPageToken` through **50 pages** until the API returned no continuation token. It yielded **2,370 unique video IDs**, matching the catalog's known-ID count, but still found **0 of the 14 target IDs**. This establishes a discrepancy between the observed uploads-playlist results and direct video lookup; it does **not** establish the underlying cause or confirm a YouTube API bug. The observation is not known to be limited to any particular video category, age, or visibility. Other videos could also be absent; 14 is the number verified in this investigation, not a proven total of all missing videos.

Operational implications:

- `full_scan_complete=true` means the observed pagination token chain ended, **not that the inventory was independently verified against every channel video**. Summary counts cover cached resources only.
- An ID absent from both `known_ids` and `videos` is undiscovered, not necessarily deleted or inaccessible. A direct ID lookup may still return its details.
- Routine head discovery and rotating status refreshes cannot reliably recover older IDs that were never recorded in `known_ids`. The current implementation has no periodic full rescan or additional-playlist discovery setting. Even a full rescan cannot guarantee recovery when the API continues omitting those IDs.
- Distinguish this from IDs present in `known_ids` but missing resource details. Those can include deleted videos and require separate investigation; an omitted resource alone does not prove deletion.
- When investigating a mismatch, preserve the catalog, receipts and quota ledger; compare exact video IDs, verify ownership through direct lookup, and independently enumerate the uploads playlist. Diagnostic API reads still consume quota. Do not reset the quota ledger to repeat scans.
- Discovery and publication eligibility are separate: discovering an additional video does not bypass the existing privacy, title, schedule, exclusion or receipt checks.

**There is currently no ideal, verified solution for this discovery discrepancy.** Repeating uploads-playlist enumeration did not recover the 14 verified missing IDs. Direct lookup works for already-known IDs but cannot discover unknown missing videos by itself. Additional playlists could improve coverage, but depend on their membership and have not been verified as a complete channel-inventory solution.

No video IDs, private titles, channel identifiers or credentials from the investigation are included here. Additional discovery sources are a possible follow-up, **not an implemented workaround or a guarantee of complete inventory**.

## Quota, caps and backlogs

Both platforms share the default **80 update attempts/day**, **5 attempts/scan**, **30-second spacing**, and **5,000 estimated units/day**. Reads reserve one unit per list request/page/batch; status updates reserve 50 units. All budgeted requests reserve durably **before dispatch**, including failed calls, initial discovery, pagination, rotating refreshes, fresh pre-update checks, reconciliation reads, and dry-run reads. SDK request retries and automatic 401 replay are disabled to avoid unmetered attempts.

Dry-run sends no privacy updates and does not create or modify publication receipts, including existing ambiguous receipts. It still writes catalog/quota state and spends read quota. It is read-only with respect to remote privacy, not a zero-network or zero-local-write mode.

The durable ledger counts failures and ambiguous attempts conservatively; reservations can exceed actual billed usage. It is **worker-local accounting**, not remaining Google project quota and not a quota reservation against other clients. Uploader thumbnail/playlist calls and other applications still share project capacity; compare with Google Cloud Console during rollout. Read-heavy scans can allow fewer than 80 updates.

Quota days reset at **midnight Pacific**, using `America/Los_Angeles` calendar boundaries including DST (not server midnight, a fixed UTC offset, or always 24 hours). Daily caps/budget exhaustion wait for the next reset; actual API `quotaExceeded`/`dailyLimitExceeded` persists a worker-specific pause until reset. Remaining candidates stay private and are revalidated later. Restart does not reset limits or spacing. A static 200-video backlog needs at least three quota days at the default cap, and may take longer due to reads, failures or new arrivals.

### Rough example: 20 members live in one day

Assume each member produces one uploaded video: 20 thumbnails, 20 playlist-item inserts, and one playlist-list request per upload. Actual calls may differ because of pagination, retries, existing playlists, and recording splits. The daily publication backlog is independent of today's uploads: the worker may publish older eligible recordings.

| Operation | Estimated units | Counted in the ytpublic ledger? |
|---|---:|---|
| 20 thumbnail updates × 50 | 1,000 | No |
| 20 playlist-item inserts × 50 | 1,000 | No |
| 20 playlist-list requests × 1 | 20 | No |
| 80 ytpublic privacy updates × 50 | 4,000 | Yes |
| Subtotal before ytpublic reads, playlist creation and video-upload requests | **6,020** | Only the 4,000 publication units |
| Optional: 20 new playlists × 50 | **+1,000** | No |

If these operations draw from a **10,000-unit daily allocation**, the subtotal leaves approximately **3,980 units**, or **2,980 units** when all 20 uploads require new playlists, before ytpublic reads and other activity. If ytpublic consumes its entire **5,000-unit worker budget** instead of just 4,000 update units, the corresponding headroom becomes **2,980** or **1,980 units**.

These are planning estimates, not a guarantee of available quota. Video-upload requests are **not included in these totals**; verify their applicable quota allocation/cost and the project's actual limits in Google Cloud Console. Other clients and failed requests can also consume capacity. The local worker ledger does not measure any uploader usage.

For comparison, publishing only **20 eligible videos** costs **1,000 update units plus reads**; 80 is a cap, not a daily target. Raising the cap to **90** permits up to **4,500 update units**, leaving at most **500 units for worker reads** with the unchanged 5,000-unit budget. The worker can stop below either cap if its read costs consume the remaining budget.

### Why the default limit is 80, and the risk of increasing it

**80 attempts/day is an operator-selected safety cap, not a YouTube-imposed publication limit.** At 50 units per privacy update, 80 attempts reserve up to **4,000 units**. The separate **5,000-unit worker budget** leaves approximately **1,000 units for discovery and status checks** if all 80 updates are attempted. This limits backlog processing while preserving some shared project capacity for uploader thumbnails, playlist operations, and other activity. It does not guarantee that enough project quota remains: ytpublic cannot see or reserve the units spent by other clients.

Every additional **10 attempted publications requires up to 500 more update units**, before any additional reads:

| Daily attempt cap | Update units at the cap | Room for reads within an unchanged 5,000-unit worker budget | Worker budget to retain approximately 1,000 units for reads |
|---|---:|---:|---:|
| 80 (default) | 4,000 | 1,000 | 5,000 |
| 90 | 4,500 | 500 | 5,500 |
| 100 | 5,000 | 0; reads prevent reaching the cap | 6,000 |
| 110 | 5,500 | Insufficient even before reads | 6,500 |

**Raising the attempt cap does not require raising the worker budget**, but the worker may stop before reaching the new cap. Raising both allows more project quota to be consumed; it does not create extra Google quota. Failed dispatched updates remain counted as attempts and reserved units.

For the illustrative **10,000-unit shared allocation** and **20-video day with 20 new playlists** above, uploader thumbnail/playlist operations alone account for approximately **3,020 units**, excluding video-upload requests. If the worker uses its full budget, the estimated headroom before uploads and all other activity is:

| Worker budget | Estimated headroom after those uploader operations |
|---|---:|
| 5,000 | 1,980 |
| 5,500 | 1,480 |
| 6,000 | 980 |
| 6,500 | 480 |

**Increasing limits in steps of 10 can exhaust the shared daily allocation.** More recordings, split videos, new playlists, retries, uploads, or other applications may consume the remaining headroom. These examples are not safe-limit guarantees; check the actual allocations and usage in Google Cloud Console before increasing limits. If Google rejects requests because the shared quota is exhausted, ytpublic pauses until its next Pacific reset, and uploader operations using the exhausted allocation may also fail. Reaching only ytpublic's local budget pauses this worker, not the uploader.

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

### Server troubleshooting: inspect before taking action

The examples below assume the standard server checkout at `/home/mypage48/mypage48`. Adjust paths to the installed unit, not to a personal workstation. These are read-only inspections; do not launch another worker to diagnose the running service.

#### 1. Establish service state, start time and deployed version

```bash
sudo systemctl status mypage48-ytpublic.service --no-pager -l
sudo systemctl show mypage48-ytpublic.service --property=ActiveState --property=SubState --property=NRestarts --property=ExecMainStartTimestamp
sudo systemctl cat mypage48-ytpublic.service --no-pager
git -C /home/mypage48/mypage48 --no-pager log -5 --format='%h %cI %s'
```

`ActiveState=active` and `SubState=running` confirm a process, not successful publication. `NRestarts` helps identify automatic restart activity; correlate it with `ExecMainStartTimestamp` and recent messages. Git history identifies the checkout revision, not proof that the running process loaded it: compare deployment/start times too.

#### 2. Read the application file, then follow new messages

```bash
sudo tail -n80 /home/mypage48/mypage48/recorder/logs/ytpublic.log
sudo tail -f /home/mypage48/mypage48/recorder/logs/ytpublic.log
```

In the `tail -f` terminal, **Ctrl+C stops only log following, not the service**. The file may contain messages from several runs because output is appended. Compare an error's timestamp with `ExecMainStartTimestamp` before treating it as a current failure; a historical authorization error followed by a later successful run is not evidence that the current process is paused.

With `REC_LOG_MODE=stdout`, Python sends application messages to stdout; the installed unit's `StandardOutput=append:...` and `StandardError=append:...` route them into the file above. With `REC_LOG_MODE=file`, the dedicated logger writes `<REC_LOGS_DIR>/ytpublic.log` directly. Inspect the unit's actual paths if settings or installation paths differ. The journal is mostly useful for systemd lifecycle messages and startup/service errors under this append configuration, not as the primary application log:

```bash
sudo journalctl -u mypage48-ytpublic.service -n80 --no-pager
```

Do not truncate or delete logs to get a clean view, and never clear the quota ledger or checkpoints to retry work. Use timestamps and bounded reads instead.

#### 3. Filter for progress and actual failure messages

```bash
sudo grep -nE 'SUMMARY|PUBLIC:|DRY-RUN:|WAIT:|IDLE:|authorization invalid|state/safety error|scan failed|daily API quota exhausted|update unconfirmed|prior update outcome ambiguous' /home/mypage48/mypage48/recorder/logs/ytpublic.log | tail -n80
```

Line numbers locate matching entries in the current file; they are not timestamps or counts of publications. Filtering can hide context, so return to the surrounding unfiltered log when diagnosing a failure.

| Message / field | Interpretation and next check |
|---|---|
| `DRY-RUN: would publish` | A cached eligible preview, **not an actual update or successful receipt**. Dry-run still consumes reads and writes catalog/quota checkpoints. `DRY-RUN: pending receipt ... reconciliation skipped` does not resolve an earlier attempt. |
| `PUBLIC:` | The worker saved a successful `published` receipt after a confirmed public response **or reconciliation of an already-public result**. It is not necessarily a new update dispatched at that instant. |
| `SUMMARY` | Counts describe cached videos classified in this scan, not a complete channel inventory. Classification happens **before the current scan's updates**; eligible counts are not decremented as those updates succeed. `published` counts confirmed updates in this scan's candidate loop, not reconciliation successes. |
| `already_published` | Cached videos skipped because successful receipts already exist, accumulated across earlier work. It is not today's successful-publication count; receipt-backed skips can persist even after someone manually makes a video private again. |
| `attempted_this_scan`, `updates=.../80` | The first is the scan-local update counter; the latter is the durable day's reserved `update_attempts` versus the configured cap (80 by default). Failed/ambiguous reservations still count toward the daily cap, so neither field promises 80 successful publications per day. A thrown failure can interrupt the scan before any summary is emitted. |
| `WAIT: quota_budget` | Local estimated-unit budget prevents further work, including reads. Wait for the logged Pacific reset; this is not proof the entire Google project quota is exhausted. |
| `WAIT: update_attempts` | Daily attempt cap reached. Remaining candidates stay private until a later quota day; do not restart to bypass it. |
| `WAIT: quota_pause` / `daily API quota exhausted` | Persisted API-quota pause until reset. Restarting does not replenish project quota or clear safe accounting. |
| `WAIT:` with `eligible_at`, `before next privacy update`, or `update spacing until` | Normal embargo/spacing wait, not a crash. Compare the deadline and current time before intervening. |
| `authorization invalid` | Processing is paused although the process can remain active. Correct credentials/authorization privately, then restart only ytpublic as described above; it does not hot-reload credentials. |
| `state/safety error` | Manual-review pause, not ordinary idle. Preserve state and investigate the specific safety error before restart. |
| `scan failed` | Retry/backoff is scheduled. Inspect the error detail and later progress; do not assume the interrupted scan finished or blindly repeat an ambiguous update. |
| `update unconfirmed` / `prior update outcome ambiguous` | Preserve the receipt and follow the manual reconciliation procedure; no blind retry or receipt deletion as routine troubleshooting. |
| `IDLE: worker disabled` | Startup configuration disabled the worker; it waits without scanning. Changing configuration requires a deliberate restart to load it. |
| `IDLE: no eligible private videos` | No eligible candidates in that scan's cache, not an authorization pause or proof that every channel video was discovered. See the existing [discovery discrepancy](#observed-uploads-playlist-discovery-discrepancy). |

A quiet log can also mean the normal poll interval, a wait, or deduplication of unchanged decisions. Check the latest summary/wait and start time together rather than restarting simply because no new per-video lines appeared.

#### 4. Check time, switches and quota without exposing private state

Deadline/reset values emitted by the worker use aware UTC timestamps (`+00:00`); **WIB = UTC+7**. The bracketed log prefix uses the process's local timezone and has no offset, while systemd/journal timestamps can use the server's timezone. Do not assume these displays share a timezone. The quota day resets at midnight `America/Los_Angeles`: **07:00 UTC / 14:00 WIB during PDT**, or **08:00 UTC / 15:00 WIB during PST**, following Pacific DST rather than a fixed WIB midnight.

Inspect only the two non-secret switches, not the whole environment file:

```bash
sudo grep -nE '^[[:space:]]*REC_YTPUBLIC_(ENABLED|DRY_RUN)[[:space:]]*=' /home/mypage48/mypage48/recorder/.env /home/mypage48/mypage48/recorder/src/.env
```

One of those files may not exist. File values alone do not prove the running configuration: process environment can override them and changes made after startup are not loaded automatically. Do not dump `.env`, systemd environment values, OAuth tokens or secrets into a support report.

Read only the quota ledger using the server's existing recorder Python (adjust if the installed unit uses a different interpreter):

```bash
sudo /home/mypage48/mypage48/recorder/.venv/bin/python3 -m json.tool /home/mypage48/mypage48/recorder/logs/ytpublic/quota.json
```

Compare its `update_attempts`, `used_units`, spacing and quota-pause fields with the latest log and Pacific day. This command only formats the file; do not redirect output back into it, edit it, or delete it to reset counters. A checkpoint may advance while being inspected.

Do not dump `catalog.json` or receipt contents into shared output: they can contain private titles and video/channel identifiers. Logs and checkpoints may also expose identifiers; redact them and any sensitive error details before sharing a minimal timestamped excerpt. Preserve original evidence privately. No summary, idle message or completed pagination flag guarantees complete inventory; retain the limitations documented in the discovery discrepancy above.

## Safe rollout

1. Deploy disabled (`ENABLED=false`, `DRY_RUN=true`); keep existing services unchanged.
2. Reuse the working channel OAuth credentials, confirm the intended channel and persistent logs/state location, then enable with dry-run still true and restart **only ytpublic**.
3. Allow the initial full scan to finish, possibly across quota days. Review old/new member IDN, SHOWROOM keyword-only titles, mixed titles, unlisted, scheduled, malformed and intentionally private examples. Add exclusions and acknowledge the 72+8 end-time assumption.
4. Compare local read estimates/log volume with actual Cloud project usage, including uploader activity. Reduce caps/budget as needed; dry-run itself spends reads.
5. Only after approval, set `DRY_RUN=false` and restart. Start with an operator-approved video safe to publish and conservative caps/exclusions; verify public status and its receipt before expanding.
6. Verify restart persistence and that a successful receipt prevents republication after a manual return to private. Keep backups and monitor failures/reconciliation, caps and quota headroom.
7. To halt future updates, stop ytpublic or disable and restart it. This does **not** revert already-public videos; address any unintended exposure manually in YouTube Studio.

These are required live acceptance steps, not a claim they have already passed. Offline tests and source review cannot prove actual channel authorization, API compatibility or production quota headroom.
