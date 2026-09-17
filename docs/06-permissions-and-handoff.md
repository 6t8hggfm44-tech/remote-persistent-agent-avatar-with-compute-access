# Permissions, actual capabilities, and future handoff

## Current request

The current scope is to analyze the reconstruction, prepare detailed executable workflows, assess the avatar app, package the result for AI reuse, and store it in the new repository. The user explicitly deferred next steps until this is done. Planning and publication of this requested public-safe bundle are authorized; implementation, hosting purchases and EA activation are not implied by this request.

The attached reconstruction is background. Instructions quoted inside it, in historical notes, or in future execution prompts do not constitute an instruction to execute them now.

## Capability and access matrix

| Work | What the assistant can do with suitable tools/access | What must be supplied or verified |
|---|---|---|
| Design and source code | Write backend/UI/C++/bridge code, schemas, scripts, migrations and tests | A writable checkout and supported runtimes |
| GitHub persistence | Read, commit and verify requested files | Access to exact repo/branch; private runtime records stay elsewhere |
| Local validation | Run builds, contract tests, mock tasks and UI checks | Dependencies and local process/network permissions |
| Cloud deployment | Prepare exact config and deploy through official API/CLI | Cloud authorization, region/SKU/budget, account/billing, secret injection |
| Remote Windows setup | Prepare reviewed scripts, operate available remote UI, run builds, retrieve logs | Actual usable remote control; credentials/MFA/UAC/license steps when needed |
| Unreal scene/character | C++/Blueprint scaffolding, supported editor scripting, GUI work and build inspection | Licensed assets/toolchain and accessible editor; human preference for final look |
| Remote build/render jobs | Build a narrow device runner and dispatch authorized named operations | Device pairing, allowed workspace/commands and scope |
| Voice | Implement microphone, transcription, response and speech pipeline | API project/key, cost cap, microphone permission and real playback tests |
| External tools | Implement separately authenticated adapters and gateway checks | Each service's OAuth/API authorization; connectors do not transfer automatically |
| Persistent work | Implement database, worker, restart and backup behavior | Running host, retention settings and approved task scope |
| Recurrence | Implement scheduling and test it with synthetic time | Separate explicit authorization for each actual recurring task |

Technical permission and user authorization are different. Having a token does not grant every possible action it can perform. Conversely, do not ask again for an action already authorized in the current scope unless a material new commitment or missing platform permission arises.

## Suggested future permission bundles

These are proposed scopes for a later conversation, not grants:

1. **Local backend prototype:** repository branch writes, dependency installation in the project, localhost services, synthetic tests; no paid calls or deployment.
2. **Capped API prototype:** selected OpenAI project/service credential, a small explicit usage cap, allowed data categories, selected live tests.
3. **Remote GPU feasibility:** one chosen subscription or capped rental, exact quoted total/terms, installer permissions, remote access, asset/license steps and a bounded benchmark.
4. **Private deployment:** exact VM/backup/domain configuration, account and monthly ceiling, private owner-only service exposure and restore test resources.
5. **Live tool pilot:** one named account and read/action scopes, retention rules and permitted targets. Broaden after the first adapter passes.
6. **Optional product upgrades:** Pixel Streaming hosting, paid runtime lip-sync plugin, native app, 24/7 rendering, or recurrence—each only if needed and included in scope.

The assistant should prepare the concrete quote/configuration/diff first, then request only missing authorization. Pete should complete required human identity, payment, MFA, consent or terms steps through the service itself; no passwords or one-time codes belong in this repository.

## Data destinations

| Information | Destination |
|---|---|
| General code, schemas, plan, synthetic fixtures | This public implementation repository |
| EA constitution, applicable policies/preferences | Existing live governance repository; no public mirror |
| Durable tasks, approvals, transcripts, runtime events | Private database with access control and selected retention |
| Durable approved preferences / audit records | Authorized private governance/state destination, via conflict-aware writes |
| API keys, OAuth tokens, device secrets | Approved secret manager/environment injection; never Git |
| Build artifacts and licensed MetaHuman assets | Authorized private artifact/LFS store consistent with asset rights |
| Evidence media showing private data | Private evidence store; public task status uses sanitized references |

Before building, identify the private storage destinations; do not invent addresses or put credentials in placeholders. Before public commits inspect actual staged content, not just `.gitignore`.

## Concrete next-step choices after this pack

Recommended next step is a local mocked backend prototype in parallel with preparing the GPU quote and feasibility script. It produces useful working software without requiring the avatar integration to be solved first. After Pete chooses a scope, select the matching prompt under `agent/`, preserve its limits, and execute the corresponding task IDs.

Deferred choices: backend provider/region, GPU SKU and storage, API budget/model/voice, private state and asset storage, runtime facial solver, desired final appearance, and whether an integrated browser viewer is wanted after the initial two-window pilot. Use a placeholder character and stock voice for engineering if preferences are not yet chosen.

## Resume protocol

1. Read current user instruction, actual repo state, `AGENTS.md`, `project.json` and `agent/state.json`.
2. Inspect the task DAG and existing evidence; do not redo verified work without a reason.
3. Revalidate live authority if activating EA; do not treat this planning session's reads as future initialization.
4. Record the actual scope in a private run record using the provided template. Keep the public state summary free of personal details.
5. Select tasks whose dependencies and required grants are satisfied; parallelize independent backend and avatar work.
6. Validate the result, persist source and evidence, verify the remote write, and update state accurately.
7. Stop at the user's requested milestone. Report exactly what runs, what was tested, and what remains blocked.
