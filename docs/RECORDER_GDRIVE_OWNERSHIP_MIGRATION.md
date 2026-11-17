# Drive ownership migration utility

Status: implemented for offline testing; **not verified against live Google accounts**. This is not a one-command guarantee that recorder processing will resume. No worker configuration or runtime behavior is changed.

## Purpose and limits

`recorder/migrate_gdrive_ownership.py` proposes and accepts ownership transfers recursively for a selected folder and its descendants. It preserves item IDs rather than copying video payloads, so existing manifest references are not intentionally rewritten. No content is downloaded, uploaded to YouTube, copied or deleted. No existing recorder refresh token is read or replaced.

The initial implementation accepts consumer `gmail.com`/`googlemail.com` accounts only. Google policy, destination storage capacity, consent configuration and transfer restrictions still apply. Shared drives, shortcuts, unexpected ownership and changed inventories are rejected. An API failure stops the tool; inherited permissions or account restrictions may require manual investigation. Do not assume Google will permit the complete transfer just because a preview succeeds.

**Do not run the modifying phases on production archives before testing the process on a small disposable folder owned by the source account.** Ownership changes are real and the tool has no automatic rollback. Proposals send notification emails and grant the recipient writer access; the transfer process is not private to the original owner. A failed phase can leave some proposals or transfers already applied.

## Permanent archive compatibility

The inventory includes `JKT48Live/permanent/` and its descendants as well as pending archives. Exact private `appProperties` are captured for **every item** and compared during preflight, individual transfers and final verification. These properties include managed identity tags and the completion record that replaces `.yt_done` for permanent MP4-only archives. The utility never rewrites those properties or recreates deleted sidecars.

A permanent archive must already have a valid **finalized** marker, the expected managed ancestry/name, and exactly the retained MP4 IDs, filenames, sizes, checksums and asset tags recorded in its marker. Pending, partial or malformed permanent markers, missing MP4s and unexpected remaining sidecars stop migration before ownership changes. Let the normal worker finish permanent finalization first, then stop all writers before planning. This utility does not complete or repair interrupted archive cleanup.

Use the **same OAuth application as the recorder**, for both accounts and all phases: `appProperties` are private to the application. Broad Drive access from another application is not a substitute. The tool checks the properties visible to its OAuth application, not invisible properties belonging to another application; it cannot independently prove that the configured application is the recorder's original one.

Checkpoints now use **plan version 2** with explicit property snapshots. Older/version-1 or incomplete checkpoints are refused, not silently upgraded. If no ownership changes have begun, retain the old checkpoint for reference and create a fresh plan with a different `--checkpoint` path. If transfers have already begun, preserve all state and reconcile the partial migration before proceeding: do not delete the checkpoint or attempt to bypass checks with a new baseline.

## Preparation

1. Stop every process that can add or change these Drive archives, including backup producers as well as the GDrive-to-YouTube worker. Stopping only `mypage48-gdrive` does not necessarily stop backup producers.
2. Preserve the existing local journals, receipts, staging and configuration securely. Keep workers stopped throughout the operation. The `--workers-stopped` flag is an acknowledgement, not a service-status check or a distributed lock.
3. Find the exact root folder ID in its Drive URL. Do not select a shortcut or identify the folder by name alone.
4. Confirm sufficient destination storage and that both accounts are eligible for ownership transfer.
5. Run on a trusted local computer with a browser and the existing shared OAuth client ID/secret in `recorder/.env` or the process environment. Individually invoked phases open separate account-selection/consent flows; `all` uses two authorizations as described below. Never post tokens, cookies or client secrets.

The utility requests the **full `https://www.googleapis.com/auth/drive` scope**, separately from the worker's restricted `drive.file` authorization. This permission can access and modify files outside the selected tree if misused. The program limits its operations to the planned tree, but the OAuth permission itself is broader. Google may require consent-screen changes or restrict authorization. No refresh token is printed or persisted by this utility. Headless browser authorization is not implemented; run on a trusted browser-equipped machine instead.

### Google Cloud access for both accounts

Use the existing Google Cloud project and OAuth client matching `REC_GOOGLE_CLIENT_ID`. If the external OAuth application's publishing status is **Testing**, add **both the source and destination accounts** under **Google Auth Platform → Audience → Test users** before authorization. Adding the destination as a test user does not require creating another project/client or granting it project IAM access. In-production applications do not use the same test-user allowlist requirement, but Google consent, scope verification and account-policy restrictions can still apply. Ensure the consent configuration permits the migration's full Drive scope; access previously granted for `drive.file` alone is not equivalent.

### Destination storage and Google One

A new Google One subscription is **not mandatory if the destination already has sufficient available storage**. Personal accounts normally include 15 GB shared across Drive, Gmail and Photos. After ownership transfer, the transferred files count against the new owner's storage, so check the whole archive size plus existing destination usage before executing.

If additional capacity is needed, arrange an adequate destination Google One plan or eligible shared Google One family storage first. The source account's subscription does not automatically move to the destination. Do not cancel the source subscription or remove recovery access until migration and normal worker access are verified. Google One provides storage capacity; it does not grant OAuth access, remove API limits, guarantee transfer eligibility or bypass Google policy.

## One-command orchestration

After testing with a disposable folder, the four phases can be orchestrated in one command:

```sh
.venv/bin/python recorder/migrate_gdrive_ownership.py all \
  --root-id ROOT_ID \
  --source-email source@gmail.com \
  --target-email target@gmail.com \
  --execute --confirm-root ROOT_ID --workers-stopped
```

This performs real changes after planning: it is **not a preview**. Source-account browser login is used for `plan` and `propose`, then a second browser authorization must select the target account for `accept` and `verify`. There are **two account-authorization sessions** in `all`, not four: select the old/source account first, then the new/destination account. If already signed in, Google may show only account selection and consent instead of requiring a password twice. Google login/consent cannot be bypassed; this is one command, not unattended migration. Wrong account selection is rejected. Each phase must succeed before the next begins, and services are closed on failure. Some remote changes can already have committed when an error occurs; preserve the checkpoint and investigate before retrying. The same worker-compatibility gates below still apply after a successful run.

## Phases

Run from the repository root. Replace `ROOT_ID`, `source@gmail.com` and `target@gmail.com` with the actual values; retain identical arguments and checkpoint for all phases. Use a fresh checkpoint for each separate migration/test.

### 1. Plan: authenticate as source

```sh
.venv/bin/python recorder/migrate_gdrive_ownership.py plan \
  --root-id ROOT_ID \
  --source-email source@gmail.com \
  --target-email target@gmail.com
```

This performs read-only remote enumeration, follows pagination, and stores an immutable inventory of IDs, names, parent edges, sizes, available checksums and exact private `appProperties`. It creates no Drive folders or permissions. An existing matching plan is validated, not silently replaced.

The default checkpoint is `recorder/logs/ownership-migration/checkpoint.json`. It contains private filenames/account identifiers, but no OAuth tokens. The directory is owner-only and checkpoint files are atomic and owner-readable/writable (`0700`/`0600`). The default path is ignored by Git. Keep the checkpoint for recovery; never publish or commit it. A custom `--checkpoint` must remain under `recorder/logs`.

### 2. Propose: authenticate as source

Preview without remote changes:

```sh
.venv/bin/python recorder/migrate_gdrive_ownership.py propose \
  --root-id ROOT_ID \
  --source-email source@gmail.com \
  --target-email target@gmail.com
```

To actually grant/request pending ownership, add:

```text
--execute --confirm-root ROOT_ID --workers-stopped
```

The tool rechecks the full tree before changing permissions. It uses writer permissions with `pendingOwner=true`; children are handled before parents and the root last. The destination must accept ownership separately.

### 3. Accept: authenticate as target

```sh
.venv/bin/python recorder/migrate_gdrive_ownership.py accept \
  --root-id ROOT_ID \
  --source-email source@gmail.com \
  --target-email target@gmail.com \
  --execute --confirm-root ROOT_ID --workers-stopped
```

Omit the three execution flags for a preview. Actual acceptance uses the destination's permission identity and `transferOwnership=true`. The tool checks remote state before each operation; rerunning the same phase/checkpoint skips remotely confirmed work rather than trusting a stale progress flag. If a transfer changes a checked parent edge or other inventory field, the tool stops rather than rewriting the baseline to hide it.

### 4. Verify: authenticate as target

```sh
.venv/bin/python recorder/migrate_gdrive_ownership.py verify \
  --root-id ROOT_ID \
  --source-email source@gmail.com \
  --target-email target@gmail.com
```

Verification checks every planned item's destination ownership, metadata and complete tree membership. Size/checksum checks compare API metadata; they are not an independent byte-for-byte download audit. A completed phase is not a claim that the recorder worker has been tested.

## Before resuming the recorder

**Do not simply replace `REC_GDRIVE_REFRESH_TOKEN` and restart after ownership verification.** Additional compatibility gates remain:

- Existing `DriveClient` root/archive validation requires private, unshared, application-managed folders. Ownership transfer normally leaves the previous owner with writer access; that sharing state can be rejected by the worker. This utility deliberately does not revoke access automatically. Review remaining permissions and remove obsolete access only after full ownership verification and a recovery plan. Inherited permissions require care.
- Test the destination's normal `drive.file` OAuth access using the same application. Successful broad-scope migration access does not prove restricted worker access, app-property discovery, root selection, downloads or cleanup will work.
- Confirm the existing transferred root is discovered rather than creating a second empty `JKT48Live` folder. The normal authorization helper can create a root; do not run it blindly as a discovery test.
- Verify one archive's manifest-referenced IDs, downloads and keep/delete behavior with the destination account before enabling the backlog. Preserve all local completion/recovery state to avoid duplicate YouTube uploads.
- Only then replace the Drive token securely; the YouTube token stays unchanged if the channel stays the same. Restart the relevant processes after configuration validation.

**End-to-end worker compatibility after account transfer remains unverified and is not automated by this utility.** Do not delete the transferred folder from the old account as a cleanup shortcut, delete local journals, or assume a browser shortcut is a copy. All API reads/writes consume applicable Drive API quota; normal Google restrictions continue to apply.
