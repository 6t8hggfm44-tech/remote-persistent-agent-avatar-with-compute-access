# Validation and operations

Everything below is an acceptance plan. No runtime tests have passed yet. The pack's own link/JSON/task-graph checks are separate from application verification.

## Acceptance matrix

| ID | Scenario | Required evidence |
|---|---|---|
| T01 | Fresh local checkout | Documented start succeeds; versions and health recorded |
| T02 | Live governance initialize / missing file / revision change | Correct ready/blocked states and private revision manifest; no stale authorization |
| T03 | Injected instructions in a document/tool result | No new capability or external action granted |
| T04 | Restart while a job and approval are pending | Correct recovered state; no repeated external effect |
| T05 | Repeated request and expired worker lease | One intended operation; fenced stale worker cannot start effects; uncertain in-flight action reconciled |
| T06 | Approval approve/decline/expire/change/replay | Exact action binding; incorrect/reused approvals rejected |
| T07 | Tool timeout after possible external success | Unknown outcome retained, receipt reconciled before retry |
| T08 | Invalid identity, cross-owner request, revoked device | Access denied before data or jobs are returned |
| T09 | Model/API quota error, timeout and spending cap | Bounded retry, persisted state, clear status and no uncontrolled spend |
| T10 | Voice-only and avatar modes | Exactly one microphone and speaker route; explicit mode switch |
| T11 | Cancel speech with late packets | Sound and face stop; old generation never resumes |
| T12 | Packaged arbitrary-speech lip-sync | Editor closed, dependency/asset manifest, visible alignment on fixtures |
| T13 | Remote control and compile | Harmless file round-trip and build log from the actual Windows machine |
| T14 | 20 conversation turns / 60-second speech fixture | Report median/p95 latency, lip offset, interruption and drift measurements |
| T15 | 60-minute avatar soak + renderer/workstation restart | Stable memory/frame behavior and truthful reconnect states |
| T16 | GPU off while backend accepts work | Text/status and previously authorized jobs continue, same state on return |
| T17 | Narrow compute runner | Allowed job succeeds; arbitrary shell/path traversal/unreviewed revision denied |
| T18 | Backup restore into disposable environment | Database consistency, known task/approval/artifact recovery |
| T19 | Deploy failed release and roll back | Previous known-good version restores service without losing accepted state |
| T20 | Optional browser stream on separate/cellular network | Authenticated viewer, working relay if needed, no double microphone/audio |
| T21 | Retention/deletion test | Deleted data removed from active stores/caches; backup expiry behavior documented |
| T22 | Optional real recurrence | Explicit scope, timezone, missed-run, cap and notification rules persisted; one execution per occurrence |

Initial project targets: simple chained replies ≤5 s p95 excluding tool wait; 1080p/30 FPS in the small scene; roughly ≤150 ms audio/mouth onset difference; ≤500 ms stop-speaking response on the tested network; reconnect ≤30 s after connectivity returns where host permits. These are goals to measure and refine, not vendor guarantees. Do not fake a pass if a simpler fallback is used.

## Evidence format

Each task completion record must include task/test IDs, actual code revision, dependency profile, host type, command/procedure, time, actual outcome, failure count, relevant logs/artifact hashes, limitations and next action. Record sensitive host identifiers, media and runtime records privately. Public summaries may state a sanitized outcome and a private evidence reference.

Keep screenshot/audio evidence for visual and timing claims with consent and approved storage. A build log proves compilation, not lipsync; a health response proves service reachability, not memory recovery. Use the specific evidence required by each gate.

## Operational controls to implement

- Health: process liveness, database readiness, EA initialization state, queue depth/age, job heartbeats, renderer connection and solver readiness.
- Capacity: CPU/RAM, disk, database size, audio buffer, GPU memory and frame rate.
- Cost: per-job reservation, model/tool usage, voice duration, GPU on-time and actual provider bills. Use a local ceiling as well as provider budgets; dashboard budgets are not assumed to be instant hard stops.
- Alerts: notify only meaningful failure or required intervention according to the authorized channel and preference. Do not create email/chat notifications without appropriate scope.
- Releases: immutable backend digest and avatar package hash, exact dependency profile, tested previous release, migration notes and rollback.
- Secrets: separate backend, provider, device and integration credentials; revocation and rotation procedures; no logging of secrets.

## Recovery runbooks

| Failure | Executor action | Verification |
|---|---|---|
| Backend process crash | Restart service; reclaim expired leases; reconcile unfinished effects | Existing task IDs and receipts preserved; ended/revoked EA runs stay ended/revoked |
| Database unavailable | Stop new side effects; show service degraded; restore connectivity or approved backup | Consistency check plus effect quarantine, current receipt reconciliation and approval/revocation revalidation before dispatch |
| Governance unreadable | Mark EA unavailable; retain infrastructure health; require successful live initialization | No policy-dependent action under incomplete controls |
| Provider API outage/quota | Back off with bounded attempts; persist status and budget accounting | No duplicate tool execution or infinite retry |
| Renderer/network loss | Revoke active playback lease; clear old audio; keep text UI available | New connection cannot replay old generations |
| Solver/plugin failure | Disable avatar speaking, preserve explicit voice/text fallback; capture diagnostics | Do not label fallback realistic lipsync |
| Workstation shutdown | Mark device offline; preserve tasks; relaunch through verified provider route | Resume existing jobs only after reconciliation |
| Bad deployment | Stop affected workers; use migration-aware rollback and known-good release | Smoke test + state integrity pass |
| Credential exposure | Revoke the affected credential through authorized controls; stop dependent work | Old credential denied; new identity tested |
| Hourly GPU budget reached | Checkpoint, request graceful stop through verified mechanism, confirm billed state | Provider reports stopped; closing tab is insufficient |

Suggested pilot backup objective: recover to a point no more than 24 hours old and restore within four hours. Restore quarantines effectful jobs: a 24-hour-old backup can predate already-committed actions, ended activations or revoked credentials. Reconcile current provider state and revalidate authority before resuming; hold ambiguity for review. These are proposed objectives pending approval, capacity and demonstrated restoration. If the user requires less potential loss, add more frequent database backups or point-in-time recovery and price it before promising it.

## Release definition of done

Project A: authenticated useful text service; actual durable task/approval recovery; successful live governance integration for an authorized EA run; one real permitted tool; tested backups and stop controls; bounded cost; documented private deployment if deployment is in scope.

Project B: one avatar with repeatable packaged-runtime speech animation; actual end-to-end microphone and playback; real interruption/reconnect tests; no editor required; correct backend state after shutdown; known-good rollback. Pixel Streaming, native clients and continuous rendering remain optional additions.

If a phase is blocked, record the failed gate, exact missing access or unsupported module, work already completed and the smallest viable next choice. Do not mark the task complete based on documentation or a demonstration on a different host.
