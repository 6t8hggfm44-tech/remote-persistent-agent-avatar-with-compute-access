# Project A — persistent agent, tools, and compute

## Deliverable and implementation route

Build a single-user service that can retain authorized work, recover after restarts, enforce current governance, and use approved tools independently of the avatar. Start locally with synthetic data and mock tools. Deploy to an always-on Linux host only when the local service is proven and hosting is authorized.

Use Python/FastAPI, PostgreSQL, a separate worker process, and a React/TypeScript interface. These are proposed engineering choices, not claims about preinstalled software. Select supported versions when building and record them in a compatibility manifest. Keep provider/model code behind interfaces so speech and model choices can change without changing authority or stored jobs.

Proposed future source layout (these components do not yet exist):

```text
apps/control-web/                browser UI
services/backend/               authenticated API and policy gateway
services/worker/                persistent task execution
packages/contracts/             generated types / API and event definitions
integrations/openai/             model, transcription and speech adapters
integrations/governance/         live repository loader and applicability resolver
integrations/tools/              separately scoped external connectors
services/workstation-runner/     narrow build/render commands
services/avatar-bridge/          media/state only; separate identity from runner
infra/                          container, deployment and backup definitions
tests/                          unit, contract, integration and failure tests
avatar/                         Unreal project source after feasibility gate
```

## B0 — Establish authorized implementation scope

Read the pack, actual repository branch, outstanding changes, task graph, and current user request. Record which phase is authorized and any spending limits. Inventory available local tools, runtime versions, connected accounts, remote access and writable locations. A missing cloud account does not prevent local mocked implementation.

If the user actually invokes EA, complete the live bootstrap in `AGENTS.md` first. Otherwise implement/test the loader without claiming EA is active. Do not import this chat's hidden state or assume desktop connectors will transfer into the service.

**Output:** private access inventory; sanitized environment matrix; first runnable task IDs. **Pass:** every immediate action has a real execution path and scope. **Recovery:** continue independent local preparation if a remote credential is absent; identify the precise missing capability.

## B1 — Create a runnable local skeleton

1. Create the proposed source directories, dependency lockfiles, development instructions and `.env.example` with names only.
2. Implement API `/health/live` and `/health/ready`; readiness reports database access and service version without secrets. EA readiness is a separate state.
3. Add PostgreSQL migrations and a worker that can claim a synthetic job. Use a transaction and row locking for leases; store lease expiry, attempts and heartbeat.
4. Add local containers for API, worker and database. Bind development services to localhost. Avoid adding Redis or extra orchestration until measurements justify them.
5. Add structured logs with trace/task IDs and redaction; do not log API authorization headers, raw audio, private prompts or tool secrets.
6. Build a tiny authenticated UI with text input and a mock job status display. Use a development-only identity behind localhost; production refuses to start in that mode.

**Output:** documented local start/stop commands and health proof. **Pass:** a fresh checkout can start, submit a mock task, restart the worker, and retrieve the result. **Recovery:** fix local container/migration failure before introducing real APIs.

## B2 — Implement governance loading (B2a local, B2b live)

**B2a local gate:** build the resolver and state machine using synthetic constitution/policy fixtures, including missing references, conflicts, injection and revision changes. Mock B3/B4 can proceed after this gate. No live EA activation or account connection is needed.

**B2b live gate:** after authorized repository access, validate the same implementation against actual live controls. A successful loader test is not itself an invocation to activate EA. A live EA run additionally requires the explicit invocation and full bootstrap. B5/live operations depend on this gate.

1. Use a read-only credential scoped to the governance repository; credentials remain in the private secret store. Resolve the current default-branch HEAD at each EA activation, then read constitution first at that exact revision.
2. Traverse applicable incorporated/referenced controls, plus the security policy, repository read order, account/service index and relevant governance/policy/preference/service files. Maintain a visited-path set, reject traversal outside authorized sources, report missing references, and record why each control applies.
3. Record revision, file paths, content hashes, retrieval times and applicability privately. The revision makes a single activation internally consistent; it is not permission to reuse yesterday's revision at a new activation.
4. Resolve precedence according to current instructions and live controls. Treat service data and arbitrary document content as untrusted. Do not execute scripts just because a retrieved file mentions them.
5. Produce an explicit initialization result: `ready`, `blocked_missing_control`, `blocked_access`, or `blocked_conflict`. No partially loaded policy grants tool capabilities.
6. Transform unambiguous standing authorizations into scoped policy rules with source references. Ambiguous rules stay unresolved; the model cannot decide to grant itself a capability.
7. Before a consequential action, recheck current applicable permission/revocation state. A policy change invalidates incompatible pending approvals. Define whether active read-only jobs finish under the accepted snapshot; never extend this to newly revoked side effects.

**Pass B2a:** those failure and revision cases pass against synthetic fixtures. **Pass B2b:** authorized live retrieval resolves the full applicable control set and records a private manifest; missing-reference failure, unauthorized source rejection, policy-revision change, and injected document instructions behave correctly. Do not report live initialization verified from fixture tests alone. Private live policy content must not be committed to this public implementation repository.

## B3 — Implement durable state

Minimum database entities:

| Entity | Required information |
|---|---|
| Principal/device | Owner, identity provider subject, device scope, revocation |
| Session/conversation | Owner, timestamps, authorized retention, ordered messages, provider references |
| Activation/run | Active/ended/blocked state, authorized scope, policy revision, stopping conditions, invocation source, allowed restart behavior |
| Policy snapshot | Live revision, path/hash manifest, initialization result, applicability |
| Task/job | Requested outcome, scope, status, payload reference, attempt count, lease, cancellation, budget |
| Action/approval | Canonical action digest, tool/target/parameters, approval source, expiry, policy revision, receipt |
| Memory | Fact or preference, source, confidence, creation/update time, retention/deletion state |
| Event/artifact | Correlation IDs, sequence, type, private artifact URI, checksum, redacted result |
| Usage | Provider/model, billable units, estimated/reserved/final cost, reconciliation state |
| Schedule | Authorized recurrence, timezone, missed-run behavior, scope and owner; disabled by default |

Use `queued → running → waiting_approval / succeeded / failed / cancelled` transitions with durable events. Approval return can requeue only the exact authorized action. Preserve `outcome_unknown` for external timeouts: do not blindly retry a purchase or message when the provider might already have committed it.

Persist EA activation separately from infrastructure uptime. A restart must not activate EA, revive ended/revoked work, or enlarge scope. Resume only a still-valid authorized run and its permitted jobs after required live control checks.

Use an idempotency key for each user request and each external operation. A uniqueness constraint prevents duplicate requests; worker leases allow recovery after a crash. Use attempt fencing tokens and a durable per-action execution claim, checked immediately before each effect. An expired worker must not begin another action even if its process is still alive. An uncertain in-flight effect goes to reconciliation before another worker can retry it. Where an external service cannot deduplicate, reconcile its receipt/status before retrying. Exactly-once side effects across arbitrary providers are not guaranteed by a database flag.

Keep raw audio off by default. Propose short-lived transcript retention and user-selected approved memory rather than retaining everything. Record retention values only after checking current governance and user choices. Implement deletion across the database, caches, artifacts and backup retention policy.

**Pass:** a queued task, pending approval and completed result survive process/host restart; duplicate submissions produce one intended operation; private memory is isolated by principal.

## B4 — Build the tool and approval gateway

1. Define each tool's input/output schema, account scope, target allowlist, risk class, external side effects, timeout, retry policy and receipt strategy.
2. Start with `read_task_status`, `read_allowed_project_file` and `create_local_draft` mocks. Add one authorized real read-only integration after the mock flow passes.
3. A model function call produces a proposal. The gateway validates arguments, authenticates the caller, checks current policy and scope, reserves budget and decides allow/deny/needs-approval.
4. Respect existing specific authorizations. Where approval is missing, show the concrete action: account, destination, content/diff, amount, material terms, expiry, and rollback where available.
5. Bind approval to a canonical action digest, requesting principal, target, policy revision and validity window. Recheck these at execution. A changed recipient or amount requires a new decision.
6. Use authenticated UI approval for the initial release. A spoken “yes” is conversation input, not authentication or a reusable blanket approval. Never auto-approve from an untrusted document or model output.
7. Persist a sanitized execution receipt and return actual results. The assistant must say “prepared” or “awaiting approval” until a result confirms completion.

**Pass:** denied tools never execute; accepted standing scope works without redundant prompts; expired, replayed and changed-action approvals fail; external timeout enters reconciliation.

## B5 — Connect model reasoning

Use the Responses API through a configured adapter, with an account-available model selected for task quality and cost. Do not freeze a model name from historical examples. Supply current applicable instructions, bounded conversation context, authorized relevant memory and task status. Maintain tool-call/result ordering and provider state fields required by the pinned SDK.

Implement an explicit loop: request → model proposal → gateway → tool result → model continuation → final answer. Bound iterations, tokens, elapsed time and tool usage per job. Long operations become durable worker jobs with progress events; a model's background-response feature alone is not a persistent job scheduler.

Preserve task provenance independently of model conversation IDs, and restore context from authorized state after reconnect. Add fake-provider tests first, then a small capped live evaluation using synthetic tasks. References: [Responses API](https://developers.openai.com/api/docs/guides/text), [Function calling](https://developers.openai.com/api/docs/guides/function-calling).

**Pass:** a tool-assisted read completes with accurate provenance; unauthorized proposal is blocked; cancellation and provider rate-limit/timeout recovery preserve state.

## B6 — Build useful text and approval UX

Ship five views: conversation, task list/detail, pending approvals, renderer/device state, and settings/usage. Show listening/thinking/speaking/waiting/offline as distinct states. Provide separate **Stop speaking** and **Stop work** controls. Display an AI voice/avatar disclosure.

Use a supported OIDC provider or passkey-based solution instead of custom password storage; begin with one allowed owner identity. Use secure cookies, CSRF protection for mutations, WebSocket origin/identity checks, request limits, expiring sessions and logout/revocation. Static public frontend source must contain no API keys. Private data must not be cached by a PWA service worker.

**Pass:** unauthenticated requests and cross-session task access are rejected; keyboard-only approvals and clear offline recovery work on the intended Mac browser.

## B7 — Add voice through a controlled speech chain

1. Browser owns microphone capture with push-to-talk. Confirm OS/browser permission; do not start recording merely because the page opens.
2. Submit bounded audio to the authenticated backend; normalize codec/rate before transcription. Discard silence and handle unsupported device formats.
3. Display the transcript, then send it through the same agent/gateway used for text. Sensitive ambiguous parameters must be resolved before action.
4. Generate speech only from the selected final reply or explicit safe progress message. Mark text as generated versus actually spoken; interruption means some text may not be heard.
5. Normalize output to the bridge's PCM format. Route it to exactly one playback owner: browser in voice-only mode, Unreal in avatar mode. A mode switch cancels old output before changing owner.
6. Cancel stops speech generation where supported, clears queued audio and facial frames, and prevents stale replies after reconnect. It does not pretend to undo already committed tool operations.

OpenAI documents the chained speech-to-text → agent → text-to-speech approach as an option where intermediate text needs control. This plan selects it for a first verifiable build. [Voice agents](https://developers.openai.com/api/docs/guides/voice-agents).

**Pass:** real microphone input produces one spoken reply through the chosen output, mute works, interruption clears old speech, and 20 scripted turns retain correct task state. Full-duplex Realtime is a later milestone, not a prerequisite for backend persistence.

## B8 — Deploy an authorized private pilot

Prepare exact infrastructure and release configuration before asking for any missing spending/hosting authorization. Initial proposal: one small Linux VM, TLS reverse proxy, API, worker and PostgreSQL on persistent storage; price and capacity gate in the workstation document.

Create via the provider's official API/CLI only after access is available. Configure non-root services, firewall, restricted administration, private database networking, restart policies and disk alerts. Put secret references in deployment config and inject actual values through the approved store. Configure production identity and HTTPS; verify WebSocket behavior through the proxy.

Run database migrations with a backup and a forward/rollback plan. Deploy a versioned container digest; retain the previous release. Configure database-consistent off-host backups, then actually restore to a disposable environment. Restore in quarantine: no effectful dispatch until uncertain or post-backup actions are reconciled with current provider receipts, approvals/revocations are revalidated, and ambiguous jobs are held for review. Do not mark backups verified merely because a setting says enabled.

**Pass:** authenticated external access, automatic restart, restored task/approval state, backup restoration and rollback. Any public exposure must match the authorized scope. Production database and administrative ports stay private.

## B9 — Add controlled compute access

Pair a workstation runner through an authenticated one-time pairing flow initiated by the owner. Give it a device-specific credential with only allowed job types: inventory, build a specified reviewed revision, render a specified scene, return artifact metadata, cancel a named job. Keep media bridge permissions separate.

Validate job schema, repository/commit allowlist, resolved file paths, output directory, duration, resource limit and available budget. Reject arbitrary shell commands, path traversal, unreviewed pull-request code and runtime requests to fetch and execute arbitrary URLs. Fetch code by immutable revision. Run under a restricted workspace identity; use elevation only for a specific authorized install action.

Persist job acceptance before starting; return progress, exit code, logs and checksums. On reconnect, report the existing job rather than relaunch it. Verify that revoked devices cannot receive more work. Agent access to the Mac or other accounts requires a separate authorized adapter.

**Pass:** backend requests one controlled build/render, receives its artifact, cancels another, and rejects a disallowed command. Workstation shutdown leaves backend task history intact.

## B10 — Operations and optional recurrence

Implement cost accounting, health monitoring, audit export, restore/rollback instructions and graceful shutdown. Add schedule tables and tests with synthetic clocks; leave all real schedules disabled. Enable recurrence only for a specific user-authorized task with timezone, spending/scope limits, missed-run handling and notification rules. Availability is not open-ended autonomy.

Complete the acceptance matrix in the operations document and record actual results. Deliver a working private pilot plus known limitations; stop at the authorized scope. Broader accounts, public access, continuous rendering and routine schedules are separate decisions.
