# Presence 0.1 — local persona prototype

Built after Pete authorized implementation and explicitly set Executive Agent integration aside. This supersedes the initial planning-only scope for this milestone. It does not activate EA, load its governance repository, or authorize spending.

## What works

- A responsive browser interface with Conversation, Persona and Activity views.
- Editable name, role, tone, reply length and custom persona notes.
- A live style preview; persona changes persist across reloads and server restarts.
- Clearly labeled scripted conversation replies, with saved message history.
- Sample background tasks producing a fixed project-outline template.
- Durable task state, cancellation, duplicate-message protection, interrupted-job recovery and a single-owner data-directory lock.
- Local-only serving with Host/Origin restrictions, JSON-only mutations and a per-process session token.

**No real AI is connected.** The scripted reply function demonstrates tone/length and interface behavior. It does not interpret arbitrary persona instructions, reason about requests, use external tools or perform actual projects. Custom notes are saved for a later AI adapter. The orb is an abstract visual placeholder, not an Unreal/MetaHuman renderer. Voice and EA integration are disabled.

## Run it

Requires Python 3.9 or newer and a current browser. This milestone has no third-party Python or JavaScript package dependencies.

On the Mac, double-click `start.command` after extracting the complete bundle, or run from the repository root:

```sh
python3 -B -m app.server --port 8765
```

Open [Presence locally](http://127.0.0.1:8765). Keep the launching process running. Stop it with Control-C. If the port is already in use, use the existing instance or select another `--port`; do not kill an unknown process. A second process cannot use the same data directory concurrently.

Data defaults to `runtime-data/state.sqlite3`. Choose a different private folder with `--data-dir`. This is a single-user local development runtime. It intentionally binds only to `127.0.0.1`; do not expose it through a tunnel or deploy it as a public service. Local software with access to your computer can access it. Production identity, deployment and account-level authorization are later work.

## Try it

1. Open **Persona**, change the name or tone, and save.
2. Reload the page and verify the change remains.
3. Open **Conversation**, select an example or type a message. Each generated response is labeled Preview.
4. Open **Activity** and create a sample outline. Watch its status and result.
5. Stop/restart the server and revisit the app. Your saved persona, messages and task results remain.

Reset conversation removes the active conversation text and cancels pending replies. It preserves persona and task history. Request fingerprints remain for duplicate prevention; old disk blocks, WAL files, filesystem snapshots or backups are not guaranteed erased. This is not a secure-erasure feature.

## Deliberate changes from the original architecture proposal

For this local milestone, use Python's standard-library HTTP server and SQLite instead of immediately installing FastAPI, PostgreSQL, React and their runtimes. This gives a working, testable application without account setup, dependency installation or ongoing charges. The API/persistence separation provides a migration path; it does not mean the production architecture has been completed.

The original backend governance and live-account gates remain deferred or unimplemented. In particular, the local process token is cross-site request protection, not user sign-in. The single-process lock and claim tokens protect this local queue; they are not a substitute for a distributed worker design.

## Source map

| File | Responsibility |
|---|---|
| `app/server.py` | Loopback server, input/access checks, background worker and process ownership |
| `app/store.py` | SQLite transactions, persona/messages/tasks, cancellation, recovery and idempotency |
| `app/mock_provider.py` | Clearly labeled deterministic preview replies and sample task templates |
| `app/static/index.html` | Accessible interface structure |
| `app/static/styles.css` | Responsive visual design and reduced-motion behavior |
| `app/static/app.js` | API integration, persona editing, request retry identity and status updates |
| `tests/test_app.py` | Persistence, concurrency, restart and request-boundary regression tests |

## Verification performed

On the development Mac with Python 3.9.6:

- 16 automated tests passed, including abrupt process termination/restart, pending-task recovery, concurrent message retries, reused request IDs with changed content, cancellation/reset preventing late replies and delayed sends, persona persistence/validation, session-token renewal, cross-origin/host rejection, private-file traversal rejection and second-process ownership.
- JavaScript syntax check passed using the bundled Node runtime.
- Actual browser interaction: saved a changed name/tone/length, reloaded to verify persistence, submitted a message and received a labeled preview reply, and created a completed sample task.
- Layout inspected at 1280×900 and 390×844; no horizontal overflow in the checked mobile persona view. Browser error/warning log was empty during the tested flow.
- Independent review found and resolved overlapping form submissions and delayed sends after reset. A targeted re-review confirmed both fixes. A conversation after a real server restart used the saved persona successfully.
- No cloud, API, Unreal or microphone test was performed. Windows locking code is present but unverified on Windows.

Re-run the meaningful backend tests with:

```sh
python3 -B -m unittest discover -s tests -v
```

The planning pack validator checks document/JSON/hash integrity; it is separate from these application tests.

## Next useful step

Add a real text-model adapter behind the current interface. Pete is not sure whether API billing is enabled, so first check that through the official account interface together, choose a small testing allowance, and configure a key through secure local settings. Do not paste a secret into chat or commit it to Git. The existing prototype remains useful without that step.

After actual text responses work: add speech, then test one packaged Unreal avatar on an authorized GPU workstation. Keep EA integration aside until Pete explicitly resumes it. No GPU subscription is needed to evaluate this local milestone.
