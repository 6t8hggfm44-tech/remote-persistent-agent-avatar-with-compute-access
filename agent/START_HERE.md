# Future executor entry point

Current priority (2026-09-20): prepare and, after concrete cost approval, provision a remote Windows GPU workstation; then build an isolated Unreal character demo with a fabricated/sample greeting. Pete wants the character first, before any additional report access. No workstation has been purchased or installed, and no scene has been built. Preserve the existing Presence 0.3 app and local data. This file does not authorize spending or new live API calls.

Read in order:

1. Current user request and [AGENTS.md](../AGENTS.md).
2. [project.json](../project.json) and [state.json](state.json).
3. [Current next step: Unreal character first](../docs/12-unreal-character-first.md), including the Vagon Blaze proposal pending exact cost approval; Shadow remains an alternative.
4. The [workstation workflow](../docs/03-workstation-workflow.md), [avatar workflow](../docs/04-avatar-project.md) and [tasks.json](tasks.json), using the current isolated-demo scope below.
5. [Permissions](../docs/06-permissions-and-handoff.md) and [acceptance and recovery](../docs/07-validation-and-operations.md). The broader [system design](../docs/01-system-design.md) and [contracts](../docs/05-integration-contracts.md) remain later integration references.

If EA is actually invoked, initialize from the live governance repository as required before substantive EA work. A previous plan or read of three files is not initialization.

For an authorized build, inspect the repository and existing evidence; write down the exact scope, constraints and permissions privately; choose dependency-ready tasks; implement and verify an increment; persist and verify results. Use `templates/run-record.example.json` as a private run-record starting point. Do not put personal task records in public Git.

Completed local milestone: P0–P3 cover the persona interface, SQLite state, scripted conversation/tasks and verification. P4 adds a real text-model adapter tested with synthetic responses. P5 verified a real persona reply, recent context recall and usage within the approved initial test allowance. P6/P7 add explicit memory, selected document context, source provenance and a private library. These remain completed work; they are not the next implementation priority.

Current path: W0 prepares the concrete host/cost/access decision, W1–W4 establish and verify the authorized workstation/toolchain, and A0–A1 produce one isolated character/scene with sample audio. Verified desktop control is sufficient; do not wait for B9's automated runner. Save and reopen the character identity and scene, and verify the demo with the editor closed before claiming a packaged build. Runtime facial animation, report-connected dialogue and continuous operation are later milestones. Do not expand this demo into generic chat features, report/repository access, live API use, or EA integration. P8 and EA/governance tasks B2a/B2b are deferred. Paid assets/plugins and host charges require their exact cost approval.

Existing report snapshots stay saved; no deletions are requested. Current Presence also retains conversation and memory data. An isolated avatar does not need access to that library or any API key. Reading entails a copy in memory, and cloud AI entails transmitting excerpts; a "no copying" guarantee is invalid. Future report access and retention choices must be handled separately after the character demo. Initial persistence means a saved identity/scene across launches, not an always-on agent.

Task statuses: `planned`, `in_progress`, `blocked`, `verified`, `deferred`. `verified` requires evidence. Optional tasks are not included merely because their dependencies pass. Each task's `requires` entries identify missing grants/capabilities, not permissions already held.

The state file records the completed local prototype and the current avatar-first priority. There is no deployed cloud endpoint, active EA run, workstation purchase, Unreal installation/scene or enabled schedule. Host selection and provisioning await a concrete cost decision and access. Preserve local user data and update progress only with actual evidence.
