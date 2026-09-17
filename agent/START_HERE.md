# Future executor entry point

This pack is a handoff, not an instruction to begin work on its own. Current state: plans delivered; implementation not authorized by the planning request.

Read in order:

1. Current user request and [AGENTS.md](../AGENTS.md).
2. [project.json](../project.json) and [state.json](state.json).
3. [System design](../docs/01-system-design.md), [permissions](../docs/06-permissions-and-handoff.md), and [contracts](../docs/05-integration-contracts.md).
4. The relevant backend/workstation/avatar workflow and [tasks.json](tasks.json).
5. [Acceptance and recovery](../docs/07-validation-and-operations.md).

If EA is actually invoked, initialize from the live governance repository as required before substantive EA work. A previous plan or read of three files is not initialization.

For an authorized build, inspect the repository and existing evidence; write down the exact scope, constraints and permissions privately; choose dependency-ready tasks; implement and verify an increment; persist and verify results. Use `templates/run-record.example.json` as a private run-record starting point. Do not put personal task records in public Git.

Suggested first implementation milestone: B0–B4 excluding B2b (the deferred live-governance gate) locally with synthetic data and mock tools. In parallel prepare W0's concrete quote and W1/W2 preflight procedure. Only perform paid/remote actions once the corresponding scope is authorized. Avatar A0–A2 can proceed through verified desktop control without waiting for B9's automated runner.

Task statuses: `planned`, `in_progress`, `blocked`, `verified`, `deferred`. `verified` requires evidence. Optional tasks are not included merely because their dependencies pass. Each task's `requires` entries identify missing grants/capabilities, not permissions already held.

The state file is intentionally explicit: there is no deployed endpoint, active EA run, purchase, enabled schedule, or runtime implementation to resume. A later agent must update that truthfully after actual work.
