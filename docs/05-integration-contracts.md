# Integration contracts — proposed v0.1

These are project-owned interface requirements, not vendor API schemas or implemented endpoints. Generate full OpenAPI/types and per-event validators in the first implementation phase. Keep vendor Realtime/GPT-Live events behind adapters; do not expose their changing schemas throughout the application.

## Backend HTTP surface

All `/v1` operations require a verified principal; task/session/device access is checked per request. Identifiers supplied in a payload never establish ownership. Mutations require CSRF protection when cookie-authenticated and an idempotency key where retry could duplicate work.

| Proposed operation | Request / response essentials |
|---|---|
| `GET /health/live`, `/health/ready` | Minimal process/dependency status; no credentials or internal topology |
| `POST /v1/sessions` | Client capabilities → session ID, allowed modes, current governance readiness |
| `POST /v1/sessions/{id}/messages` | Text + request ID → message ID and task/turn ID |
| `POST /v1/sessions/{id}/audio` | Bounded multipart audio + codec/rate/duration → transcription/turn ID; supported MIME types validated |
| `GET /v1/tasks`, `/v1/tasks/{id}` | Owner's statuses, progress, public-facing receipts and artifact links |
| `POST /v1/tasks/{id}/cancel` | Cancel request → acknowledged / already committed / cancellation pending |
| `GET /v1/approvals/{id}` | Exact action preview, target, scope, expiry and canonical digest |
| `POST /v1/approvals/{id}/decision` | Approve/decline + digest + authenticated user gesture; server revalidates all fields |
| `POST /v1/sessions/{id}/speech/cancel` | Current utterance/generation → buffer invalidation and playback acknowledgement |
| `POST /v1/devices/pair` | Short-lived pairing code initiated by owner → scoped device registration |
| `POST /v1/devices/{id}/revoke` | Revoke credential and active lease; disconnect and deny subsequent work |
| `GET /v1/events` (SSE) | Ordered owner-filtered task/status events; resume cursor; private text excluded where not needed |
| `WSS /v1/renderers/connect` | Outbound media bridge session; device-bound auth, heartbeat and capability negotiation |
| `WSS /v1/runners/connect` | Separate compute identity and allowlisted job protocol; no media credential reuse |

Proposed defaults to validate during build: user audio ≤60 seconds per push-to-talk turn; reject oversized uploads before decoding; bounded decoded sample count; UTF-8 text length limits; capped concurrency. Expire unclaimed pairing codes in minutes, revoke after first use, and rate-limit attempts. Keep exact operational limits in versioned configuration, not hard-coded UI assumptions.

## Media events and delivery rules

Common envelope in `contracts/avatar-event.schema.json`:

```json
{
  "protocol_version": "0.1",
  "type": "speech.begin",
  "session_id": "synthetic-session-1",
  "utterance_id": "synthetic-utterance-1",
  "playback_generation": 1,
  "sequence": 0,
  "payload": {
    "sample_rate_hz": 24000,
    "channels": 1,
    "encoding": "pcm_s16le"
  }
}
```

This schema validates the shared envelope only. Implement strict per-type payload schemas before accepting network traffic. A syntactically valid message still needs authentication, authorization, replay checks and size limits.

| Event | Direction | Payload requirement |
|---|---|---|
| `renderer.hello` | Renderer → backend | Device capabilities, build hash, format/rate support, solver readiness |
| `renderer.ready` | Renderer → backend | Selected capabilities, current lease/generation, render and audio readiness |
| `speech.begin` | Backend → renderer | Format, sample rate, channels, optional expected sample count |
| `speech.chunk` | Backend → renderer | Contiguous start sample offset, sample count, PCM bytes; bounded frame |
| `speech.end` | Backend → renderer | Final sample count; denotes production complete, not playback complete |
| `speech.cancel` | Backend → renderer | New generation and cancelled utterance; invalidate all older buffers |
| `playback.progress` | Renderer → backend | Actual played sample offset, queued samples, dropped samples |
| `playback.stopped` | Renderer → backend | Final played sample, cancellation/end/error cause |
| `presentation.state` | Backend → renderer | Enumerated visual state; no secrets, approvals, raw tool arguments |
| `heartbeat` / `error` | Either | Health or bounded diagnostic code, with correlation ID |

Prototype can use bounded base64 PCM inside JSON; use binary framing after the contract tests when throughput justifies it. Example internal format: mono PCM16LE at 24 kHz, 20 ms chunks (480 samples / 960 bytes). Current OpenAI TTS documents 24 kHz raw PCM output; the bridge must still check format and resample once if the selected solver requires another rate. [Text to speech](https://developers.openai.com/api/docs/guides/text-to-speech).

The backend grants one playback lease per session, to either browser voice-only audio or one Unreal renderer. Shadow and Pixel Streaming are alternate audible delivery transports for that same renderer, not separate speech owners. Choose one audible transport and mute the other. Each switch/cancel advances a generation. Sequence numbers and offsets reject duplicates, old data and gaps; counters reset only within a newly identified generation/utterance. On reconnect, exchange current readiness and lease state; never replay old speech by default.

Use a bounded ring buffer, initially targeting 100–250 ms network buffering plus measured solver lookahead; cap total queued audio (proposed 2 seconds). These are tuning hypotheses. If the solver needs more buffering, measure its latency and update the acceptance record. Overflow fails the utterance and stops output rather than growing without bound.

Playback and facial animation use the same sample clock. Wall-clock timestamps help tracing across hosts but do not schedule mouth movement. Backend delivery, renderer receipt and actual speaker playback are separate events. Cancellation invalidates the current stream, stops sound and resets facial motion even if a late provider packet arrives.

## Compute job contract

Required fields: job ID, authorized principal, device ID, named operation, reviewed code revision, validated parameters, workspace root, output prefix, timeout, budget reservation, policy revision, action/approval digest where applicable, and idempotency key. Worker response includes accepted/rejected, reason, process/job reference, progress, exit state, artifact hashes and receipt.

Allowed initial operations: `inventory`, `build_reviewed_revision`, `render_named_scene`, `collect_job_logs`, `cancel_job`. Every operation maps to reviewed local code with bounded arguments. Reject a general `exec`, free-form shell, unsigned script URL, or arbitrary filesystem access. The model can request a defined operation; it cannot change the runner's allowlist.

## Approval and authorization contract

Canonicalize the exact action data before hashing: account, destination, tool, parameters, amount/currency if relevant, scope, expiry and policy revision. Present that same data in the UI. Approval authority comes from the authenticated user or an applicable documented standing authorization, never from the action text itself.

Record the decision, actor, source and use status privately. At commit time recheck expiry, target, digest, current policy and revocation. If the action changed, return `approval_stale`. If an external result is uncertain, return `outcome_unknown` and reconcile rather than invent a success or retry blindly.

## Retention and compatibility

Store event metadata and receipts according to the approved retention policy; keep audio ephemeral by default. Keep private payloads out of public fixture files. Version the bridge and backend contracts together and negotiate supported versions; reject unknown incompatible versions with a useful error. A protocol change requires duplicate/cancel/reconnect tests before release.
