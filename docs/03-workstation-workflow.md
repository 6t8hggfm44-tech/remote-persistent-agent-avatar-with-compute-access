# Workstation and infrastructure execution plan

**Current order — 2026-09-20:** follow [Unreal character first](12-unreal-character-first.md) for the isolated character demo. Vagon Blaze is the proposed pilot, pending exact cost approval and verified access; Shadow Power Pro is an alternative. No host is purchased or installed. Keep the existing app/data intact and defer report access, live APIs, EA and backend expansion. The research and broader workflow below remain reference material; their earlier Shadow-first and integration ordering does not override the current milestone.

Prepared 2026-09-17. Status: researched plan; no subscription, machine, remote-access service, or deployed software has been created. The attachment is source context, not a grant to buy services or activate Executive Agent mode.

## Recommendation and verification boundary

Use a small Linux server for persistent agent services and a separately switched-on Windows GPU workstation for Unreal and Blender. Shadow Power Pro remains a reasonable **conditional pilot** for the small scene and packaged avatar. It is not yet a validated workstation for all MetaHuman authoring operations. Use Vagon Blaze only for measured workloads that need more RAM/CPU, or as the pilot alternative if Shadow fails the feasibility gate. A public browser avatar should have a separate streaming-host decision; owning a remote desktop does not establish permission or technical ability to host Pixel Streaming from it.

### Current evidence

| Item | Verified official information | Consequence / still unknown |
|---|---|---|
| Shadow Power Pro | U.S. advertised price $59.99/month; Windows 11; 28 GB RAM, 20 GB VRAM. Pro comparison shows 210 hours/month fair use, 8-hour sessions, 120-minute idle limit, and an optional Always On add-on. | Verify exact CPU/GPU allocation, storage layout, region, tax and checkout terms. Do not promise A4500 or 8 vCPUs from the reconstructed conversation. [Shadow offers](https://shadow.tech/us/shadowpc/offers/) |
| Shadow Always On | Paid add-on for eligible Pro plans; price appears in Manager. Documentation says it keeps the PC powered on without a connected/active client. Activation is billed for the full calendar month; documentation currently requires support for cancellation. | Obtain the actual quote and clarify its interaction with fair-use/session limits before any 24/7 plan. No fabricated price or assumption it is included. [Always On](https://support.shadow.tech/hc/en-us/articles/35433305315985-Enable-and-use-Always-On) |
| Shadow idle behavior | Ordinary background programs do not prevent automatic shutdown; peripheral input is used to determine activity. | Checkpoint before disconnecting; never implement artificial activity to evade provider limits. [Automatic shutdown](https://support.shadow.tech/hc/en-us/articles/33668011057937-About-Automatic-Shutdown-and-Shadow-PC-Pro) |
| MetaHuman authoring | Current Epic recommendations for Creator/Animator include 16 physical high-performance cores, 32 GB RAM and a supported GPU with at least 8 GB VRAM. Character assembly can use more than 32 GB. | Shadow's 28 GB is below the RAM recommendation. Treat successful assembly, packaging and a sustained session as purchase/continuation gates, not as guaranteed. Vagon's advertised cores are not established to be equivalent to Epic's physical-core recommendation. [MetaHuman hardware](https://dev.epicgames.com/documentation/metahuman/metahuman-hardware-requirements-in-unreal-engine?lang=en-US) |
| Vagon Blaze | Listed at $3.57/hour, 16 cores, 64 GB RAM, 24 GB A10G GPU. Personal storage is $7.99/month for a 75 GB disk; additional disk is listed at $5 per 50 GB. Region affects compute prices. Outbound file transfer above 10 GB/month is listed at $1.50 per additional 10 GB. | Requote region and disk size. A 75 GB disk is a poor planning assumption for engine, SDKs, project, cache and build copies. Measure the installation footprint and request the appropriate expansion. [Vagon pricing](https://vagon.io/cloud-computer/pricing) |
| Vagon automation | The Teams API documents start, graceful stop, machine inventory and temporary access links. Streams has separate application deployment/API facilities. | Neither establishes that a Personal Cloud Computer subscription includes an API, SSH or public inbound ports. Validate product, entitlement and authentication first. [Teams machines API](https://docs.vagon.io/teams/reference/machines), [Streams overview](https://docs.vagon.io/streams) |
| Always-on backend candidate | DigitalOcean Basic Regular: 1 vCPU, 2 GiB RAM, 50 GiB SSD, 2,000 GiB transfer at $12/month; 2 vCPU/4 GiB is $24/month. Daily percentage-based backups cost 30% extra. | Provisional single-user orchestration host, not local LLM or GPU inference. Start small, measure; move to 4 GiB if memory pressure warrants it. [Droplet pricing](https://www.digitalocean.com/pricing/droplets), [Backup pricing](https://docs.digitalocean.com/products/backups/details/pricing/) |

The hardware conclusion is an engineering inference from published specifications. No real benchmark has been performed. Prices were rechecked on the preparation date and must be rechecked immediately before spending.

## Actual access path the implementation agent can use

The baseline requires provider desktop access. The AI can prepare scripts and project source locally, navigate a permitted provider browser session, operate the remote Windows UI through screenshots/keyboard/mouse, and inspect generated logs. It must first prove that the available computer-use tool can actually see and control that session. A local shell in Codex does not automatically become a shell on the rented computer.

1. Pete completes or permits account login, payment, MFA and required license acceptance. Store no password, recovery code or long-lived key in Git or screenshots.
2. Open the provider's supported Mac app or browser desktop. Confirm control by creating and reading back a harmless test file inside the remote project directory.
3. Fetch the exact reviewed repository revision over HTTPS. Verify its commit ID in Windows. Run a read-only inventory/preflight script from that revision and retrieve its JSON report.
4. Execute named reviewed installation/build scripts through PowerShell in that desktop. Require structured exit codes and logs written into the workspace; collect these artifacts after each phase. Avoid giant pasted scripts and ambiguous UI-only completion claims.
5. If useful later, establish an explicitly authorized narrow remote-command channel. Prefer outbound authenticated HTTPS/WSS to the backend with device pairing, short-lived credentials, a command allowlist, exact commit/build IDs, time limits and logs. That is software the project must build and test, not an assumed provider feature. It must not accept unrestricted model-generated shell text.
6. If using a self-hosted build runner instead, dedicate it to a separate authorized private build repository (the new source repository is public), restrict workflows/branches and jobs, never execute untrusted pull-request code, and register it only after the required authority and secret handling are established. Do not install a general runner merely to avoid proving desktop access.
7. Do not expose RDP, SSH or WinRM publicly as a shortcut. Do not assume the provider supports an inbound address or port forwarding. A VPN is a separate access change requiring a tested rollback: Shadow warns that incorrect routing can cause loss of access and recommends split tunneling and avoiding its internal address ranges. [Shadow VPN guidance](https://support.shadow.tech/hc/en-us/articles/32731825500561-Setting-Up-a-VPN-on-Your-Shadow-PC)

Automation gate result must be one of `desktop_control_verified`, `approved_remote_executor_verified`, or `blocked_access`. Never label the build autonomous while it relies on an untested channel. If the stream cannot be reliably controlled, prepare and verify the runnable script bundle locally, then identify the exact remote action Pete must perform; do not invent successful execution.

## Workstation build workflow

| Phase | AI execution instructions after authorization | Human-dependent step | Evidence and exit condition |
|---|---|---|---|
| W0 — Quote and choose region | Recheck provider checkout, region latency test, precise SKU, storage, hourly/idle/session behavior, and license compatibility. Record a dated quote with budget scope. | Pete accepts provider, budget and terms; handles payment/MFA. | Accepted quote and reachable supported desktop. No purchase before this gate. |
| W1 — Inventory | Collect Windows build, CPU allocation, RAM, GPU/driver/VRAM, DirectX capability, disk/free space, display/audio devices, UTC/timezone and network diagnostics into `workstation-inventory.json`. Capture the provider's hardware screen and non-secret system reports. | Admin/UAC confirmation if required. | Actual allocation matches chosen scope; enough disk for engine plus cache, project and two packaged builds. |
| W2 — Prove access and recovery | Verify the access path above; create the project directory; test fetch of a reviewed commit; record restart/reconnect instructions. | First provider login or unavailable interactive controls. | Read/write and log retrieval verified; reboot/reconnect succeeds. |
| W3 — Install toolchain | Select one supported Unreal/MetaHuman/plugin version set at implementation time. Install official Epic Launcher/engine, matching Visual Studio C++ tools and Windows SDK, Git/Git LFS, Blender, and the project runtime dependencies. Pin exact versions in a machine-readable manifest. Reboot if required. | Epic account/license acceptance, installer UAC or gated downloads. | Tool versions recorded; blank Unreal project opens; a tiny Windows package builds and launches; Blender renders a simple frame. |
| W4 — Baseline avatar feasibility | Use one small scene and one optimized/preassembled MetaHuman. Measure editor and packaged-app RAM/VRAM, shader time, frame rate and crash logs. Test Creator/assembly separately when custom character authoring is needed. | Pete chooses appearance only where preference matters; AI uses a placeholder meanwhile. | Proposed initial target: 1080p/30 fps for 30 minutes, no crash, no sustained paging/memory exhaustion, usable remote input. These are project targets, not vendor promises. |
| W5 — Backend connection | Install the thin avatar bridge; pair to the backend with a revocable device credential. Use outbound HTTPS/WSS. First exchange health/state events and play a fixed test-audio file; only then connect live conversation. | Authorization for backend account/service access and microphone use. | Authenticated connection, correct reply/session IDs, no keys in client bundle, logged reconnection. |
| W6 — Audio | Choose exactly one microphone owner and one speaker output path. Test mute, push-to-talk, echo, device changes, loss of stream and reconnect. Start with headphones. | OS/browser microphone permission and a real spoken test. | Voice can be heard once; no feedback loop; user can stop listening and cancel speech; reconnect does not replay stale audio. |
| W7 — Package and recover | Package a Windows app with a desktop launcher and explicit connect/disconnect state. Keep the previous good build. Persist approved project/assets remotely and externally, then restart workstation and relaunch. | Validate interactive Windows login/session, GPU/audio access and provider reconnection after reboot; retain a manual-login fallback if needed. | Application works without Unreal Editor; a rollback restores the previous package; backend state remains intact while GPU machine is off. |
| W8 — Decide whether to retain Shadow | Compare measured experience and memory footprint with the approved budget. Use a bounded Vagon Blaze session for failed authoring workloads only after quoting it. | Any additional spend beyond authorization. | Decision record: retain, use Vagon for authoring, or replace provider. No second paid workstation by default. |

Installation/build scripts should be idempotent: inspect versions first, download only from official sources, fail before destructive replacement, return actionable errors, and record the repository revision used. Separate `preflight`, `install`, `build`, `launch`, `collect-diagnostics`, and `rollback` operations. Document every interactive exception. Generated binaries and Unreal intermediate/cache folders should not become normal Git commits; use Git LFS only for approved source assets and keep distribution packages in a release/artifact store.

## Microphone, stream and network decisions

The selected integration prototype uses the local browser microphone and disables Shadow microphone forwarding. For a separate diagnostic test, Shadow's native microphone forwarding or its browser microphone support is available. The Mac app exposes the device selector in Quick Menu → Audio. Browser access requires microphone permission and currently documents Chromium support, H.264, and fewer advanced features than the desktop app. Use the desktop client first for setup and benchmark the browser separately. [Shadow microphone guide](https://support.shadow.tech/hc/en-us/articles/33470084217745-How-to-connect-a-microphone-to-Shadow-PC), [Browser FAQ](https://support.shadow.tech/hc/en-us/articles/32731806257297-Shadow-PC-in-Browser-FAQ)

If the local web interface instead owns microphone capture, turn off remote-desktop mic forwarding. Route assistant audio through the chosen avatar playback path once, so lip movement and heard audio share the same stream/timing. The separate avatar integration plan should select that path; mixing local direct playback with delayed remote playback creates echo and mismatched lips.

The provider stream, speech round trip, animation buffering and local playback each contribute latency. Record timestamps at input end, first response audio, animation start and audible output. Do not promise sub-second performance before end-to-end measurement. For the chosen chained prototype, aim for at most 5 seconds p95 for simple replies and report measured median/p95 separately from tool wait time. Push-to-talk is the starting mode; full-duplex interruption is a later improvement.

Vagon Teams audio documentation confirms microphone/audio toggles and browser/local-device permissions; its Windows audio stack may require Voicemeeter. Verify the actual Personal configuration rather than assume the Teams procedure is identical. [Vagon audio guidance](https://docs.vagon.io/teams/troubleshooting/audio-io-issues)

A user-facing browser product can use a managed application-streaming product instead of attempting to expose the development PC. Vagon Streams documents microphone support, client-side integration and application deployment; it has its own product/price model and must be quoted independently of Blaze desktop pricing. [Vagon Streams](https://docs.vagon.io/streams), [Client SDK](https://docs.vagon.io/streams/integrations/client-side-communication/javascript-sdk)

## Minimal always-on deployment candidate

Provisional choice: one DigitalOcean Linux Droplet with the backend, reverse proxy and persistent datastore. Begin with the $12 size for a single low-traffic user if staging tests pass; the $24 size provides more margin. Keep model inference on the selected API provider. Use a small managed service only if its persistent process, WebSocket, storage, scheduler and sleep behavior are verified for this backend; a free sleeping web tier is not a substitute for reliable agent scheduling.

After spending/access authorization, the AI can query provider regions/images/sizes with the official API/CLI, create an exact reviewed configuration, install an SSH public key, limit administrative access, deploy versioned containers, provision HTTPS, inject secrets without printing them, verify service health, run persistence/restart tests, and record resource IDs and rollback commands. The operator must supply an authorized cloud account/token, billing and domain/DNS control where used. DigitalOcean documents both API and CLI automation rather than requiring an assumed remote-desktop API. [Create a Droplet](https://docs.digitalocean.com/products/droplets/how-to/create/)

The detailed backend build must define the service stack, auth, policy loader, task state, secrets and backups. Infrastructure success requires a health endpoint, an authenticated request, process restart recovery, a pending task surviving reboot, backup restoration to a disposable host, and a rollback to the previous release. A VM snapshot alone should not be treated as proven database recovery. Use database-consistent exports and restore tests; keep a copy outside the live machine.

## Cost worksheet

All numbers below are USD, pre-tax illustrations based on the cited prices, not accepted spending authority. Arithmetic excludes AI/model/voice tokens, extra asset storage, domain, egress, licensed plugins/assets, monitoring, streaming hosting, extra Windows storage and Always On. API usage requires a separate approved monthly cap and measured per-session costs.

| Scenario | Monthly base calculation | Illustrative base |
|---|---|---:|
| Persistent backend only | $12 VM + 30% daily backup | $15.60 |
| Shadow + small backend | $59.99 + $15.60 | $75.59 |
| Shadow + 4 GiB backend | $59.99 + $24 × 1.30 | $91.19 |
| Small backend + Shadow + 10 Blaze hours | $75.59 + $7.99 storage + 10 × $3.57 | $119.28 |
| Small backend + Shadow + 40 Blaze hours | $75.59 + $7.99 storage + 40 × $3.57 | $226.38 |
| Blaze left on for illustrative 730-hour month | $7.99 + 730 × $3.57, before backend/other costs | $2,614.09 |

Reusable formula: `total = backend + backups + shadow_base + shadow_addons + vagon_storage + (vagon_hours × actual_region_rate) + voice_and_model_usage + artifact_storage + egress + streaming_host + taxes`.

For hourly use, record start time, expected stop time and a maximum approved duration; save work before stopping; verify stopped status and final usage from the provider rather than assume closing a tab stops billing. Current Personal auto-stop options were not fully verified in this research and must be inspected during setup. Keep the persistent backend functioning independently throughout any GPU shutdown.

## Open gates to carry into implementation

- Exact selected engine/plugin version set and actual installed workstation specs.
- Region performance, provider terms at checkout and a measured avatar benchmark.
- Verified remote computer-use or narrow command-execution route.
- MetaHuman authoring on 28 GB RAM versus authoring on a larger temporary machine.
- Exact storage footprint and external asset/build backup location.
- Shadow Always On quote and fair-use interaction, only if continuous rendering is requested.
- Personal Vagon shutdown behavior/API entitlement; do not borrow Teams/Streams assumptions.
- Chosen microphone owner, reply-audio route, browser/mobile behavior and measured latency.
- Separate production streaming host and quote, if the user wants a single browser app.
