# Project B — Remote avatar interface execution plan

Status: **proposed instructions for a future authorized build; no avatar, workstation, application, or deployment has been built by this planning work.** Research checked September 17, 2026. The reconstruction is background, not a fresh instruction to activate EA, purchase services, install software, or deploy anything.

## Decision: what application do we need?

Build a small custom integration application, but begin without a new native Mac or phone app. There are two deliverables: a browser control interface for conversation and approvals, and an Unreal Windows application that renders the avatar. Existing remote-desktop software can carry the first prototype's picture and sound. An installable browser experience/PWA and an integrated Pixel Streaming viewer are later improvements.

| Option | What it provides | Decision |
|---|---|---|
| Shadow viewer plus small browser control page | Uses the rented workstation's existing video/audio transport; quickest way to prove the avatar pipeline | First prototype |
| Browser interface with Unreal Pixel Streaming | Avatar, conversation controls, status, and approvals in one browser; adds signalling, identity, network traversal, and relay operations | Preferred product direction after runtime proof |
| Installable PWA | Optional home-screen/dock entry and app-like browser shell | Add after core browser flow; verify target browsers rather than promise background microphone behavior |
| New native Mac/iOS/Android application | Deeper operating-system integration and bespoke background behavior | Defer until a specific unmet requirement justifies development, signing, distribution, and additional testing |
| Local 3D avatar rendered in browser | Could reduce GPU-streaming dependency; entails a different renderer and asset/performance pipeline | Separate fallback experiment, not an assumed MetaHuman drop-in |

This is an engineering recommendation, not a previously settled decision. The browser handles human interaction; the backend owns identity, instructions, state, and authorization; Unreal handles presentation. Rendering can stop while the backend retains the conversation and approved task state.

## The one baseline audio route

```text
Mac browser microphone (push-to-talk; explicit user gesture)
  -> authenticated backend audio upload
  -> speech transcription
  -> backend policy checks / EA response and approved tool loop
  -> final backend-selected response text
  -> text-to-speech PCM
  -> outbound authenticated WSS connection from GPU workstation
  -> workstation avatar bridge -> Unreal runtime audio queue
  -> the SAME audio samples drive playback and facial animation
  -> Unreal picture + sound -> Shadow viewer -> Mac ears/eyes
```

The browser initially shows transcript, status, approvals, stop, and mute controls. **It does not also play the assistant audio while Shadow is the selected renderer.** Disable Shadow microphone forwarding for this route. Start with headphones and push-to-talk; while listening, stop/flush pending assistant speech. Do not route the user's microphone to MetaHuman facial animation: animate only the assistant's generated speech. Avoid feeding Windows speaker loopback back into transcription.

The first speech pipeline is chained transcription → controlled backend response → speech generation. This makes the approved text, playback owner, and policy boundaries observable. It is a project choice, not a claim that direct speech-to-speech is impossible. Evaluate a Realtime/other live speech session only after the baseline works; that upgrade must preserve backend authorization and the single playback owner. OpenAI's current documentation includes multiple voice API profiles; pin one profile and its exact event schema before implementation rather than mix GPT-Live and Realtime events. [OpenAI voice transports](https://developers.openai.com/api/docs/guides/voice-websockets), [server controls](https://developers.openai.com/api/docs/guides/voice-server-controls).

If the renderer disconnects, stop its speech lease and clear its buffers. Show “Avatar offline; text available.” Offer an explicit switch to browser audio, start a new playback generation, and prevent a reconnecting renderer from replaying speech already delivered elsewhere. Browser fallback need not replay the full previous answer automatically.

## What has evidence, and what remains a build experiment?

Epic supports audio-based realtime MetaHuman animation through Live Link, and an assembled character can select a Live Link subject. The documented audio-device setup is a useful editor prototype. It is **not evidence that arbitrary streamed PCM will work automatically in a packaged executable**. [Realtime animation](https://dev.epicgames.com/documentation/metahuman/realtime-animation?application_version=5.6), [audio source](https://dev.epicgames.com/documentation/metahuman/using-a-metahuman-audio-source?application_version=5.6), [character connection](https://dev.epicgames.com/documentation/en-us/metahuman/realtime-animation-using-live-link).

Epic explicitly distinguishes an offline MetaHuman Performance asset processed with its realtime solver from a genuinely live Audio Live Link source. The former does not solve interactive speech delivery. [Audio Driven Animation](https://dev.epicgames.com/documentation/metahuman/audio-driven-animation).

Packaged runtime audio-to-face integration is the principal technical risk. Epic's 5.8 release notes describe its expanded cross-platform Animator capability as editor-only. That wording must not be generalized to mean all MetaHuman rendering is editor-only: assembled characters are a different concern. It means this plan must demonstrate a runtime-capable audio solver path, its required modules and models, and its licensing before declaring the interface complete. [5.8 release notes](https://dev.epicgames.com/documentation/metahuman/metahuman-5-8-release-notes-in-unreal-engine).

Shadow's listed 28 GB RAM is below Epic's current 32 GB authoring recommendation. The reconstruction's CPU allocation has not been freshly confirmed; inspect actual hardware against the 16-physical-core recommendation. Large character assembly may use still more memory. This is a feasibility concern, not proof that a small runtime scene cannot run. Benchmark the exact rented machine and allow a more capable temporary authoring/build machine. [MetaHuman hardware requirements](https://dev.epicgames.com/documentation/metahuman/metahuman-hardware-requirements-in-unreal-engine?lang=en-US).

## Required inputs and delegated capabilities

The future executor needs a working backend staging endpoint and documented authentication/audio protocol; an authorized Windows GPU environment; Epic account access and accepted applicable terms; engine/compiler installation permissions; network and repository access; a budget for any paid plugin or stronger machine; and the ability to observe the actual remote editor/runtime and its logs. Secrets must be supplied through the configured secret store, not pasted into Git.

Codex can write the browser UI, bridge, C++ modules, build scripts, schema tests, automation, and operational documentation; run builds; inspect logs; and operate exposed remote UI with permission. A browser session on the Mac does not inherently grant file or process control inside remote Windows. Establish a real remote execution/control path before promising unattended installation or packaging. Prefer a dedicated least-privilege workstation runner with named operations and repository-limited workspace over arbitrary commands from a browser.

Pete supplies account sign-ins/MFA where required, grants installation and spending authority, and selects the final avatar appearance and voice after samples exist. A stock/preset character and stock voice are sufficient for engineering work. No custom likeness or voice cloning is needed for the MVP. These future dependencies do not block completing this plan.

## Work packages and acceptance gates

### A0 — Lock the build profile and prepare reproducible access

1. Inspect the available workstation without changing it: OS, GPU/VRAM, RAM, storage/free space, drivers, DirectX support, remote display/audio behavior, outbound HTTPS/WSS, and permitted service lifecycle.
2. Select an installed or available stable engine version and compatible MetaHuman/runtime components. Live sources inspected today describe 5.8; that is a candidate, not a blanket instruction to upgrade existing work. Write the exact engine patch, compiler/SDK, plugin versions, runtime requirements, and asset provenance into `config/avatar-build-profile.json`.
3. Pin browser/bridge dependencies in lockfiles. Put source and nonsecret configuration in Git. Keep project binaries/assets in appropriate private artifact storage or authorized LFS; do not put Epic engine files, licensed marketplace packages, credentials, recordings, or private EA documents into a public repository.
4. Establish a workstation-local checkout, artifact directory, and private evidence directory. Use verified supervised desktop execution of reviewed scripts initially; verify one harmless action and one file round trip. A paired compute runner is an optional later automation path in backend B9, not a prerequisite for A0–A2.
5. Prepare idempotent `doctor`, `build`, `start`, `stop`, and `collect-diagnostics` scripts. At this stage their interfaces may exist while implementations are developed; do not label stubs operational.

**Gate A0:** authenticated remote control and logs work; the machine can run a minimal Unreal scene; the pinned build profile exists. If authoring exceeds memory or runtime is unstable, measure before purchasing more compute and propose the exact alternate machine/cost for approval when required.

### A1 — Prove the presentation chain with deterministic audio

1. Create a minimal C++ Unreal project with one map, fixed camera, simple lighting, and a single optimized assembled MetaHuman. Avoid a complex environment until audio and packaging pass.
2. Cap frame rate, choose conservative texture/groom/LOD settings, and capture a baseline frame-time/memory report. Initial target: stable 1080p/30 FPS; this is an acceptance target, not a provider performance promise.
3. Add a diagnostic scene state display: disconnected, connected, listening, processing, speaking, waiting for approval, interrupted, error. Status events are presentation data, never authorization.
4. Play a known local PCM/WAV speech fixture through Unreal and receive it through Shadow on the Mac. Include silence, plosives, numbers, short and long utterances. Confirm the only audible assistant output is the selected route.
5. Make the first simple packaged Windows build before backend integration; close the editor and launch the package. Store its hash, build log, launch log, and screen/audio evidence.

**Gate A1:** avatar visible, fixture audible once, package starts with editor closed, resource use recorded. This is not a lipsync completion claim.

### A2 — Resolve runtime facial animation first

Time-box the initial feasibility spike to approximately two engineering days once tools/assets are available; this is a planning estimate, not a guarantee. At the checkpoint choose one supported route or report the concrete remaining blocker.

1. In the editor, enable MetaHuman Live Link, create an Audio source, select the capture device, assign a named subject, and attach it to the character. A temporary virtual audio device may connect the known assistant fixture for diagnosis **only after verifying that device/driver is permitted and recognized**. Record routing so it cannot capture the user's voice accidentally.
2. Inspect the pinned engine's actual plugin/module descriptors and exposed realtime audio APIs. Determine which components can be cooked and redistributed, which require editor modules, which neural model files must be staged, and whether runtime initialization is supported. Do not “fix” this by blindly changing module types.
3. Attempt a minimal C++ runtime audio-to-face adapter taking PCM frames directly from a bounded queue. Create/initialize runtime sources explicitly at startup; do not rely on a saved audio-device ID from the development machine. Keep networking, decoder/resampler, solver, and rig adapter separate.
4. Build the standalone Development package and run it with the editor closed, then test on a clean Windows user/environment or second approved machine. Feed the fixture. Verify voice, mouth movement, source initialization, model loading, and stop/reset.
5. If Epic's path is not supportable in the selected version, evaluate one maintained third-party/runtime-capable solution using its vendor's current documentation and a packaged-build trial. Confirm its actual UE-version support, licence, sample input format, model dependencies, cancellation, and deployment rights. Obtain any necessary purchase authorization for a concrete option; do not subscribe merely to continue guessing.
6. Keep an amplitude-driven jaw movement or static face as a clearly labelled diagnostic fallback. It proves audio/network/rendering but does **not** satisfy a realistic lipsync deliverable. Offline animation of pre-recorded lines is also not a replacement for interactive speech.

**Gate A2:** repeatable packaged-build lipsync from arbitrary test PCM with editor closed, exact dependencies recorded, and an attributable runtime licensing path. On failure, preserve a usable text/voice backend and a transparent avatar limitation; do not bury the dependency in later visual polish.

### A3 — Implement the authenticated PCM bridge

1. Implement `AvatarBridge` on Windows as a small process that initiates an outbound WSS connection to the backend; no internet-facing Windows control port is required for this proposed design. Provision a revocable device identity restricted to a specific user and renderer.
2. Connect the bridge to the Unreal runtime by a loopback-only socket or named pipe. Define a small allowlist of messages: readiness/capabilities, speech begin/chunk/end/cancel, presentation state, playback progress, heartbeat, and error. No shell commands or EA tool calls in this protocol.
3. Negotiate PCM sample format, channel count, and supported sample rates explicitly. Use a single internal mono PCM format; resample exactly once at a documented boundary when necessary. Do not infer codec/sample rate from an unlabelled byte stream.
4. Include `protocol_version`, `session_id`, `utterance_id`, `playback_generation`, monotonic `sequence`, and audio sample offsets. Bind all chunks to the authenticated session and current rendering lease. Bound message/chunk size, queued duration, and utterance length.
5. Schedule both audio and facial frames against the same **audio playback sample clock**. Apply measured solver lookahead/buffering to audio, not an arbitrary wall-clock guess. Track samples received, queued, actually played, and discarded separately. Backend receipt is not proof the user heard anything.
6. On cancel, increment the generation, clear queued audio and facial data, stop sound, reset the mouth, and acknowledge the last played sample. Ignore stale chunks after cancel and after reconnect. On a gap or overflow, fail the utterance clearly instead of letting minutes of speech accumulate.
7. Store logs with event IDs, durations, timestamps, and failure codes by default; avoid raw microphone recordings and private transcript payloads in diagnostic bundles.

**Gate A3:** deterministic fixture survives chunking, duplicate messages, delayed messages, disconnect/reconnect, cancellation, and buffer overflow tests with no duplicate playback or stale facial motion.

### A4 — Connect the actual conversation interface

1. Build a responsive authenticated browser page with push-to-talk, editable transcript, send, stop-speaking, mute, typed input, backend/renderer status, and a clear AI-generated voice indication.
2. Browser records one user turn under an explicit gesture and uploads it to backend transcription. Backend records the accepted user message and creates the response through its own policy/tool loop. Display proposed privileged actions as backend-issued approval records, never executable instructions supplied by the avatar.
3. Generate assistant speech only from the backend's backend-selected response text. Send it through A3. Show captions and transcript in the browser; keep browser speech playback disabled while the avatar owns the lease.
4. Send listening/speaking/approval states to Unreal without copying the constitution, credentials, or private tool arguments into the graphics client. Give Unreal only what it needs to render.
5. Test a short conversation, one approved-memory recall, a read-only tool result, a blocked unauthorized action, an action awaiting approval, a declined action, a long response stopped midway, and resumption after GPU shutdown.
6. Keep the browser controls available on the Mac outside the remote desktop. Treat initial two-window interaction as a prototype ergonomics cost; fix through the later integrated viewer if useful.

**Gate A4:** at least 20 end-to-end turns, including interruptions and a renderer restart; no repeated tool execution; no accidental microphone forwarding; approved task/memory state survives avatar shutdown. Save redacted evidence and defects.

### A5 — Make the Windows runtime repeatable and recoverable

1. Generate the final packaging command from a verified Unreal Project Launcher profile and check it into the build script, then use Unreal Automation Tool to repeat it. UE supports command-line build/cook/package workflows; arguments depend on the locked profile. [Build operations](https://dev.epicgames.com/documentation/unreal-engine/build-operations-cooking-packaging-deploying-and-running-projects-in-unreal-engine).
2. Automate scene/asset setup where exposed through supported Unreal editor scripting. Keep runtime code in C++/Blueprint/runtime modules: Epic's embedded Python support is for editor automation, not gameplay/packaged execution. [Unreal Python](https://dev.epicgames.com/documentation/unreal-engine/scripting-the-unreal-editor-using-python).
3. Produce versioned release artifacts with checksums, dependency manifest, changelog, and rollback instructions. Test start/stop/restart without the editor. Keep the prior working package until the new one passes.
4. Add bounded local supervision for the bridge and runtime within the host's allowed lifecycle. Verify that a usable interactive Windows session, GPU and audio devices exist after reboot; the avatar is not assumed to run as a headless Windows service. Record a manual provider/Windows login step if unattended session restoration is unsupported. Never keep a cloud PC awake by synthetic input to evade idle/session rules. On stop, save backend state and stop GPU use through a supported mechanism or an explicit manual action.
5. Run a 60-minute soak, several reconnects, a workstation restart, and a backend outage. Recover automatically where supported; otherwise present actionable state in the browser. Any paid always-on service must be separately authorized.

**Gate A5:** fresh launch and rollback documented, no editor dependence, bounded recovery, and no persistent state stored exclusively on the graphics machine.

### A6 — Optional integrated browser viewer with Pixel Streaming

This phase is not necessary for the first working avatar. Begin only after A2–A5 establish a useful runtime.

1. Validate the cloud PC/provider permits the needed software, outbound streaming, encoder access, and intended service use. A working Shadow viewer does not prove a custom Pixel Streaming host is available or supported.
2. Enable the selected Pixel Streaming plugin and fetch the matching infrastructure branch/release. Do not use the repository's development branch by default. Epic warns of breaking changes across UE versions. [Official infrastructure](https://github.com/EpicGames/PixelStreamingInfrastructure).
3. First prove a packaged/standalone stream on the same machine or a private network. Pixel Streaming streams Unreal frames/audio to browsers; its normal setup targets packaged applications or Standalone Game. [Getting started](https://dev.epicgames.com/documentation/en-us/unreal-engine/getting-started-with-pixel-streaming-in-unreal-engine).
4. Add authenticated HTTPS/WSS player access, per-session renderer binding, private/allowlisted streamer access, and suitable short-lived relay credentials. Test direct and forced-TURN paths from a Mac and a phone on a different network. STUN alone may be insufficient; TURN consumes relay bandwidth and adds cost. [Hosting/networking](https://dev.epicgames.com/documentation/unreal-engine/hosting-and-networking-guide-for-pixel-streaming-in-unreal-engine).
5. Put the viewer beside the existing browser controls. Keep microphone capture on the established browser-to-backend route; leave Pixel Streaming `UseMic` disabled. Its microphone feature is a separate UE input/playback path and would otherwise create an unnecessary second route. [Epic microphone feature](https://github.com/EpicGames/PixelStreamingInfrastructure/blob/master/Frontend/Docs/Using%20the%20Microphone%20Feature.md).
6. Harden the reference signalling server; it is not a complete authenticated application. Protect streamer and player connections, do not ship secrets in Unreal, and do not enable remote console commands. Exact hooks depend on the pinned version. [Epic security guidance](https://github.com/EpicGames/PixelStreamingInfrastructure/blob/master/Docs/Security-Guidelines.md).
7. Keep Unreal as the speech playback owner and switch only its audible delivery transport from Shadow to the Pixel Streaming browser viewer; mute or close Shadow's sound. Only switching to voice-only browser playback transfers the speech lease away from Unreal. Test Safari/Chrome on the actual devices, autoplay permission, microphone denial, tab suspension, orientation, reconnect, and low bandwidth before optionally adding PWA installation.

**Gate A6:** a single browser view delivers authenticated avatar video/audio and controls, including a cellular/relay path; no double audio, cross-session access, or dependency on an open editor. Keep A5's working remote-desktop route available for rollback.

## Acceptance measurements

Initial engineering targets should be refined with Pete after a working sample exists. They are not promises about untested products.

| Test | Initial target / observable evidence |
|---|---|
| Visual delivery | Stable 1080p/30 FPS in the simple scene; record actual frame times and stream drops |
| Speech response | Measure end-of-user-turn to first audible assistant sample over 20 turns; report median and p95, with tool wait separated; aim for ≤5 s p95 for simple chained replies |
| Lip synchronization | Aim for audio/mouth onset within about 150 ms and no increasing drift over a 60-second fixture; visual/audio recording plus runtime sample counters |
| Stop speaking | Aim for ≤500 ms audible stop on the tested network; stale chunks and mouth motion must not resume |
| Reconnect | Disconnection visible promptly; reconnect within 30 s once connectivity returns where host permits; no automatic replay of old speech |
| Independence | Backend conversations/approved state persist after full renderer shutdown and restart |
| Policy fidelity | Tool authority/approval exactly matches backend tests; avatar has zero direct tool execution privilege |
| Durability | Clean packaged start, 60-minute soak, crash recovery, known-good rollback, redacted evidence bundle |

Do not use an average latency alone to declare success. Record the slowest representative cases and whether network, TTS, solver lookahead, or rendering caused them. A successful editor preview is evidence for that preview only.

## Suggested future source tree

```text
apps/control-web/             browser UI; shared backend auth contracts
services/avatar-bridge/              Windows connection/audio bridge
avatar/ExecutiveAvatar/          project/config/C++ source; asset references
avatar/ExecutiveAvatar/Plugins/  custom runtime adapter source
scripts/avatar/                 doctor/build/start/stop/diagnostics
config/avatar-build-profile.json
contracts/avatar-protocol.schema.json
tests/avatar/                   audio fixtures, cancellation/bridge tests
docs/avatar/                    setup, topology, packaging, operator runbook
evidence/avatar/                redacted results/manifests; private media elsewhere
```

These are recommended deliverables to create during an authorized build, not files asserted to exist now. An AI executor should treat the backend contract as authoritative, verify current source APIs, implement one work package at a time, attach evidence to its gate, and leave an explicit `next_action` and blocker record. It should never mark the overall avatar complete while the packaged runtime solver or actual streamed audio route remains untested.

## Future execution prompt

> Build Project B using this plan after confirming the authorized scope and resources. Start by reading the repository's current status, backend contract, build profile, and applicable instructions. If this invocation activates Executive Agent mode, first complete the required live constitution bootstrap; a planning document is not a substitute. Work in a branch, preserve existing data, and use fixtures before real conversation data. Complete A0 through A5, one verified gate at a time; pursue A6 only if included in the authorized scope. The baseline is push-to-talk transcription → backend-controlled response/tool execution → speech PCM → outbound Windows bridge → packaged Unreal avatar → Shadow video/audio. Keep one audio playback owner. Prove runtime lip synchronization with the editor closed before visual polish. Record exact dependency versions, commands, redacted evidence, rollback, and remaining defects. Prepare a concrete option before requesting any new purchase/permission not already granted. Stop at the agreed milestone; do not create schedules or buy always-on capacity from this prompt alone.
