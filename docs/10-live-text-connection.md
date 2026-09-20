# Presence 0.2 — bounded live text connection

Presence 0.3 retains this connection setup and adds saved memory and document excerpts. See [the current memory and repository guide](11-memory-and-repository-conversations.md) for the expanded data disclosure and verified scope. The two live tests below are historical version 0.2 evidence.

The OpenAI connection is implemented and verified with two real text requests on 2026-09-18, following user credential entry and an explicitly authorized initial allowance. Executive Agent, voice, Unreal rendering and external tools stay deferred.

## Connect and test

1. Start the local app normally. A new data folder starts with zero API allowance. An executor may enable a previously authorized initial test allowance with `python3 -B -m app.server --test-budget-usd 1`; this is a total allowance, not a renewal on each launch. The supported initial allowance is at most $1.
2. Open [Connection](http://127.0.0.1:8765/#connection). Confirm the intended allowance displayed there.
3. The user creates a key in the intended funded OpenAI project using [OpenAI API keys](https://platform.openai.com/api-keys). Choose **Restricted**, expand **Model capabilities**, and set **Responses (/v1/responses) → Write**. Leave the other child capabilities and **List models** set to **None**. The parent **Model capabilities** label showing **Mixed** is expected because only Responses is enabled. This path was verified in the user's key-creation screen on 2026-09-18; the underlying permission is `api.responses.write`. See [OpenAI permission documentation](https://developers.openai.com/api/docs/guides/rbac) and the [scoped-key example](https://developers.openai.com/api/docs/guides/terraform/service-accounts). The user then pastes the key directly into the masked field and clicks **Connect OpenAI**. Never ask for the key in chat. The application needs Responses API access to the selected model, not administrative access.
4. Connecting loads the key into server memory and makes no paid request. The interface shows that the key has not yet been verified.
5. Send a harmless test message in Conversation. For example: “Introduce yourself using my saved persona in one sentence.” A successful reply is labeled AI, the connection becomes verified, and usage is shown on Connection.
6. Send a brief follow-up to verify recent conversation context and persona behavior. Inspect any failure in Activity before deliberately retrying. Do not automatically change models, increase allowance or resend uncertain requests.
7. Disconnect to clear the active credential and cancel pending AI replies. Revoke the key in the OpenAI dashboard when it is no longer needed.

Restarting the server requires the user to reconnect their key. Repeating the allowance launch option does not erase reservations. Conversation reset also leaves the usage ledger intact. Keep using the same private data folder during the authorized test; creating another folder creates a separate allowance and must not be used to bypass the authorized total.

## Credential and data handling

- The password field clears before its submission awaits. No key is returned by an API response, saved to browser storage, logged, written to SQLite or included in source archives.
- The local server keeps the key in process memory and sends it as authorization only to `https://api.openai.com/v1/responses`. The transport uses normal TLS verification, disables redirects and inherited proxy routing, and has a 45-second timeout.
- This is local development software. Other software running with access to this user's computer may read process memory. “Memory only” does not promise forensic removal from swap, crash dumps or operating-system snapshots.
- Each real message sends the saved persona and a bounded recent real conversation to OpenAI. Earlier scripted preview messages are excluded. The request carries `store: false`; this is not a claim of zero retention. See [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data).
- The expected provider travels with each message. If another tab switches between preview and live mode before acceptance, the request is rejected rather than silently uploaded or simulated.
- No tool definitions, external account access or EA activation are included. Persona instructions influence text; they do not grant execution permissions.

## Initial spending control

The fixed model is `gpt-5.6-luna`, chosen for the initial low-cost text test. Official model documentation checked on 2026-09-18 lists $0.20 per million input tokens and $1.20 per million output tokens; cache writes are $0.25 per million input tokens. Access to this model was verified with successful live calls on 2026-09-18. [Model profile](https://developers.openai.com/api/docs/models/gpt-5.6-luna).

Requests use `reasoning.effort: none`, the default service tier, no tools, no streaming/background mode, a maximum 30,000-byte serialized payload and 256/512/1,000 output tokens for short/balanced/detailed replies. The last 12 live messages plus the current message are eligible; older context is removed until the payload fits. Responses are limited to 256 KiB.

Before dispatch, each attempt atomically reserves $0.02 in private `runtime-data/api-usage.sqlite3`. This deliberately exceeds the bounded request's cost at the checked rates, including input-cache writes. A $1 allowance admits at most 50 attempts. Errors, timeouts and interrupted requests keep their reservations, and the same task ID cannot dispatch twice. The ledger survives app restarts and conversation resets.

The screen distinguishes **reserved allowance** from **estimated usage cost**. The estimate uses reported input/output counts at standard uncached rates and is not a billing receipt; uncertain calls may cost money without returned usage. OpenAI billing is authoritative. This application allowance does not cap usage through other apps or someone else using the same key. Recheck model pricing before extending this pilot or its allowance.

## Failure and recovery behavior

- No automatic API retries or model fallbacks.
- One live conversation request may be pending at a time, preserving context order.
- Preview jobs recover normally. Queued/running live jobs become failed after restart rather than repeating a potentially billed action.
- Cancel, reset, reconnect and disconnect fence late output. A request already in flight may still incur a charge; cancellation cannot promise a refund or halt provider computation.
- Known API failures use fixed messages for rejected keys, permissions, unavailable models, rate/quota limits and connectivity. Raw upstream errors are never exposed.
- Existing databases migrate provider labels to `preview`; existing local conversations and persona settings are preserved.

## Implementation and validation

`app/openai_provider.py` owns the text request, ephemeral credential, conservative ledger and safe error conversion. `app/server.py` owns request boundaries and dispatch; `app/store.py` owns provider labels, causal history and recovery. The fourth browser view provides Connection controls.

34 automated tests passed on macOS with Python 3.9.6: 16 existing local tests plus 18 provider and HTTP integration tests. All live-provider tests inject synthetic credentials and responses; none call OpenAI. Coverage includes concurrent allowance exhaustion, credential exclusion from disk/state/errors, no-key/no-budget failures, bounded requests, malformed responses, provider drift, context isolation, cancelled/reset/disconnected late replies, invalid reconnect and prevention of duplicated paid attempts.

JavaScript syntax passed. The updated Connection screen was inspected in the actual browser and showed the configured allowance. The automated suite used no real credential or paid request. Subsequent live browser verification passed: a real reply followed the saved persona; a second reply correctly recalled a two-word synthetic test phrase; both replies persisted after page reload; Connection showed the verified state. Two API attempts reported 438 input tokens and 35 output tokens, with an estimated combined cost of $0.000131. The conservative ledger reserved $0.04, leaving $0.96 of the $1 test allowance. These are usage estimates, not a billing receipt. The key was never read by Codex or saved in the source. Windows, production hosting, remote access, voice and Unreal remain unverified.

Run checks:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B scripts/validate_pack.py
```

## Instructions for the next executor

Read the current user request, `agent/state.json` and this document. Treat account credit as availability, not spending authorization; honor the separately authorized allowance. Preserve the existing private runtime folder and never print secrets. If the key is not connected, direct the user to the masked Connection field and finish independent work. Once connected, perform only the authorized harmless text tests, record sanitized results and actual reported usage, and update P5 only after live evidence exists. Do not equate passing mocked tests with a working account/model connection.

Official request references: [text generation](https://developers.openai.com/api/docs/guides/text), [Responses API fields](https://developers.openai.com/api/reference/python/resources/responses/methods/create), and [key creation quickstart](https://developers.openai.com/api/docs/quickstart).
