# Future executor entry point

Current state: Pete authorized implementation with EA integration set aside. Presence 0.2 has a tested text adapter awaiting live credential verification; read `docs/10-live-text-connection.md` first. This file does not authorize new paid services or deployment.

Read in order:

1. Current user request and [AGENTS.md](../AGENTS.md).
2. [project.json](../project.json) and [state.json](state.json).
3. [System design](../docs/01-system-design.md), [permissions](../docs/06-permissions-and-handoff.md), and [contracts](../docs/05-integration-contracts.md).
4. The relevant backend/workstation/avatar workflow and [tasks.json](tasks.json).
5. [Acceptance and recovery](../docs/07-validation-and-operations.md).

If EA is actually invoked, initialize from the live governance repository as required before substantive EA work. A previous plan or read of three files is not initialization.

For an authorized build, inspect the repository and existing evidence; write down the exact scope, constraints and permissions privately; choose dependency-ready tasks; implement and verify an increment; persist and verify results. Use `templates/run-record.example.json` as a private run-record starting point. Do not put personal task records in public Git.

Completed local milestone: P0–P3 cover the persona interface, SQLite state, scripted conversation/tasks and verification. P4 adds a real text-model adapter tested with synthetic responses. P5 awaits user entry of an API key and authorized live verification. Original B0–B4 remain the broader backend roadmap; both EA/governance tasks B2a and B2b are deferred. Only perform paid/remote actions once the corresponding scope is authorized. Avatar A0–A2 can later proceed through verified desktop control without waiting for B9's automated runner.

Task statuses: `planned`, `in_progress`, `blocked`, `verified`, `deferred`. `verified` requires evidence. Optional tasks are not included merely because their dependencies pass. Each task's `requires` entries identify missing grants/capabilities, not permissions already held.

The state file records the completed local prototype. There is no deployed cloud endpoint, active EA run, purchase or enabled schedule. A later agent should preserve local user data and update progress truthfully.
