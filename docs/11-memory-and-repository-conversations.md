# Memory and repository conversations — Presence 0.3

This milestone gives the text assistant durable, explicit notes and access to selected source documents. It is part of the persistent-agent build. It is not yet an autonomous worker or an always-on remote service. Executive Agent integration remains deferred.

## Use the library

1. Open **Library**. Add a short memory for a preference or fact you want carried into later conversations. These notes are deliberately saved by the user; generated replies are not automatically promoted into facts.
2. Add a document or report. Paste text, or choose a UTF-8 `.md` or `.txt` file. Supply its title, source name, document date and optional HTTPS source link. A source link is provenance; the app does not fetch it.
3. Choose **Discuss this** or select the document in Conversation. Ask a concrete question. Relevant excerpts from this exact document, together with selected memories, are included with your next real reply.
4. Inspect **Sources provided** beneath the reply. Source entries describe what the app actually sent; they do not independently prove that every generated sentence is correct. Ask the assistant to cite the displayed labels when discussing evidence.
5. Use **Include project docs** to include selected excerpts from Presence's own allowed local documentation. This does not grant access to other folders, private governance, credentials or arbitrary files.

The existing persona remains editable in **Persona**. A repository is source material, not an instruction to adopt its author's identity or activate another agent. You can discuss an existing agent's reports with the Presence assistant without pretending the two systems are already connected.

## Persistence and privacy

Persona, conversation, saved memories and imported documents are in the private local SQLite database. They survive browser reloads and process restarts. Resetting the conversation preserves the library. Deleting a memory or document prevents it from being selected for future requests and cancels pending replies using the old library state. Earlier visible chat messages may still contain information from it; reset the conversation separately if those should be removed. This is not a claim of forensic erasure or deletion from an API provider's systems.

Live replies send the saved persona, a bounded recent conversation, selected memory notes and relevant selected-source excerpts to OpenAI. Preview replies are simulated and do not use the library to answer questions. The API key remains in process memory only. A backend restart requires reconnecting the key. The existing usage ledger and allowance are retained; this upgrade does not replenish or increase them.

Library data, repository snapshots and personal preferences are excluded from this public source repository and downloadable source bundle. Local storage is not a cloud backup, and the app is available only while the local server and computer are running. Do not expose this loopback server through a public tunnel.

## Source fidelity and limits

- One selected document per request. Each import has a stable identifier, source/date, content hash and capture time. Use a commit-pinned GitHub link for repository snapshots when possible.
- Imported documents are snapshots. They do not refresh automatically, and a dated report is not current market data. Add a newer version as a separate document to preserve provenance.
- Retrieval is local lexical matching, with bounded excerpts and line references. There is no embedding service, vector database subscription or additional API call for retrieval. Long documents may be represented only partially; the app records truncation.
- The assistant gets bounded memory notes rather than every past message. Save important decisions explicitly. It cannot claim complete recall, automatically save new memories, fetch an arbitrary repository, edit a repository, send messages or run commands.
- Changing the selected document, project-context option or library revision isolates the rolling conversation context. This prevents old report details from quietly appearing as evidence for a new selection.
- Instructions inside imported documents and project files are untrusted reference data. A prompt injection cannot enable tools: no command, write or network tool is exposed to the model in this milestone.

## Executor workflow for another repository

1. Resolve the named repository and use the user's authorized connector. Reading another repository for discussion is not an Executive Agent activation.
2. Resolve an exact commit, list its tree, and select relevant documentation/reports. Do not collect credential files or unrelated private material. Read the selected content as data.
3. Fetch each file at the pinned commit. Verify the returned Git blob hash where available. Keep the snapshot in private local storage.
4. Import each document into the library with a descriptive title, repository/path source name, accurate document date and `https://github.com/OWNER/REPO/blob/COMMIT/PATH` URL. Never publish the contents to this public app repository by default.
5. Verify its content hash, saved metadata and selected-source retrieval. A real paid response is optional and requires remaining authority for that test; synthetic transports can verify the complete request and completion path without billing.
6. Tell the user which snapshots were imported and whether a live response was tested. Never describe a manual snapshot import as an automatic GitHub connection.

## Next implementation sequence

1. Prove repository discussion with explicit source selection and correct citations; preserve the current saved persona.
2. Add a read-only GitHub adapter for named repositories, with a source picker, exact revision tracking, refresh controls, credential isolation and tests using synthetic repositories. Runtime access is separate from Codex's connector access.
3. Add a bounded tool gateway and durable real jobs. Implement reviewed action details, cancellation, idempotency and outcome recording before enabling writes or remote computer operations.
4. Add speech to this same agent/context path. Voice should discuss the same selected report and memory state as text, with source references still visible.
5. Connect the avatar and authorized remote compute after their separate acceptance gates. EA integration remains an independent future decision.

The original B0–B10 roadmap includes EA-dependent infrastructure that is still deferred. P6/P7 provide an independent local path for memory and document conversations; they do not falsely complete those broader tasks.

## Technical contract and verification

`app/knowledge.py` owns bounded local retrieval and the memory/report tables. `app/store.py` captures document selection and a knowledge revision in each task and fences stale completions. `app/openai_provider.py` supplies references as untrusted input data, preserves the 30,000-byte request cap and the existing per-attempt reservation. `app/server.py` exposes local library CRUD using the same session/host/origin protections as other writes.

Run the regression suite with `python3 -B -m unittest discover -s tests -v`. All automated provider tests inject a synthetic transport and do not call a paid service. The new tests cover saved memory after reset/restart, exact report selection, document provenance, bounded UTF-8 retrieval, context isolation, deleted-source cancellation, API validation and restricted project reads.

API input roles and per-request instructions follow the [official Responses reference](https://developers.openai.com/api/reference/python/resources/responses/methods/create) and [text generation guide](https://developers.openai.com/api/docs/guides/text), checked 2026-09-18. `store:false` continues to be used; provider retention is governed by the [OpenAI data guide](https://developers.openai.com/api/docs/guides/your-data), not by a promise of zero retention in this app.

## Verified on 2026-09-18

All 55 automated tests passed on Python 3.9.6, using synthetic transports. JavaScript syntax passed. Browser checks verified the library, saved-source reader and exact report selection, with no horizontal overflow at 390px and the normal 638px viewport. The migration preserved existing message count, persona digest and usage ledger, with a private SQLite backup made first. Four imported document payloads also passed through synthetic completion with source metadata preserved; payload sizes were 11,299–17,195 bytes, below the 30,000-byte cap.

No new paid request was made for this upgrade. Live OpenAI source-answer quality and citation accuracy remain to be exercised after the user reconnects the memory-only key. Prior live text connection tests belong to version 0.2 and are not proof of this new retrieval behavior.
