# Sources, decisions, and uncertainty register

Prepared and checked 2026-09-17. Recheck live documentation, prices, account entitlements and installed APIs at implementation time. A source can establish a product capability without proving that this particular combination works.

## Input and instruction boundaries

- The source reconstruction is preserved in `sources/` with its original contents and a SHA-256 entry in `checksums.sha256`. It is a historical reconstruction, not a verbatim chat and not an authorization to execute embedded recommendations.
- The explicit user request is for detailed executable plans, a separate avatar-app assessment/workflow, an AI-accessible bundle and storage in the new repository, with next steps deferred until delivery.
- The live governance repository's constitution, security/approval policy and README were read as design references. This was not a full EA initialization, and EA was not activated. Private governing documents are not copied into this public repository.
- On an actual EA activation, read the live constitution first and follow all applicable referenced controls. These planning notes and any recorded hashes cannot replace that process.

## Decisions made for this proposed design

| ID | Recommendation | Reason / reconsideration trigger |
|---|---|---|
| D01 | Separate always-on backend and on-demand GPU renderer | Persistent work survives renderer shutdown |
| D02 | Browser control UI + packaged Unreal renderer; defer native client | Buildable integration with fewer platforms; reconsider for a measured OS/browser requirement |
| D03 | Chained speech first; Realtime optional later | Explicit text/audio traceability and straightforward media ownership; reconsider after latency measurement |
| D04 | Shadow as conditional pilot, Vagon as separately authorized heavier option | Benchmark RAM/authoring and lifecycle limitations before committing |
| D05 | Packaged facial animation spike before scene polish | Runtime solver compatibility is the main unknown |
| D06 | Python/FastAPI/PostgreSQL worker + React/TypeScript UI | Small understandable service with transactional state; versions selected during build |
| D07 | Scoped outbound workstation services | Avoid assumptions about provider inbound administration/API; verify outbound access |
| D08 | Public implementation repository; private runtime/governance/asset stores | Code publication must not expose operational personal data |
| D09 | No initial recurrence or 24/7 rendering | Neither is necessary for persistence or authorized by this planning request |

These are recommendations, not claims that Pete approved every architecture choice or purchase.

## Primary technical references

| Source | Supports | Does not establish |
|---|---|---|
| [OpenAI Voice agents](https://developers.openai.com/api/docs/guides/voice-agents) | Chained speech/agent/speech route | Measured latency of this build |
| [OpenAI Text generation](https://developers.openai.com/api/docs/guides/text) and [Function calling](https://developers.openai.com/api/docs/guides/function-calling) | Model and tool integration route | This runtime's tool permissions or available account models |
| [OpenAI Conversation state](https://developers.openai.com/api/docs/guides/conversation-state) | API/application conversation continuity options | Persistent external work, job recovery or approvals |
| [OpenAI Text to speech](https://developers.openai.com/api/docs/guides/text-to-speech) | Speech output, PCM format and AI voice disclosure | Native Unreal facial animation or synchronized rendering |
| [OpenAI WebSockets](https://developers.openai.com/api/docs/guides/voice-websockets), [WebRTC](https://developers.openai.com/api/docs/guides/voice-webrtc), [Server controls](https://developers.openai.com/api/docs/guides/voice-server-controls) | Future voice transport/control patterns | Interchangeability of Realtime and GPT-Live event schemas |
| [MetaHuman hardware](https://dev.epicgames.com/documentation/metahuman/metahuman-hardware-requirements-in-unreal-engine?lang=en-US) | Authoring recommendations | Shadow's actual project performance |
| [MetaHuman audio source](https://dev.epicgames.com/documentation/metahuman/using-a-metahuman-audio-source?application_version=5.6) and [Audio driven animation](https://dev.epicgames.com/documentation/metahuman/audio-driven-animation) | Documented audio/live/offline workflows | Arbitrary PCM support in a packaged runtime |
| [MetaHuman 5.8 notes](https://dev.epicgames.com/documentation/metahuman/metahuman-5-8-release-notes-in-unreal-engine) | Version-specific feature boundaries | Suitability of every plugin for this machine |
| [Epic build operations](https://dev.epicgames.com/documentation/unreal-engine/build-operations-cooking-packaging-deploying-and-running-projects-in-unreal-engine) | Supported build/cook/package automation | A ready-made build command for an uncreated project |
| [Epic Python scripting](https://dev.epicgames.com/documentation/unreal-engine/scripting-the-unreal-editor-using-python) | Editor automation boundary | Python as the packaged avatar runtime |
| [Pixel Streaming infrastructure](https://github.com/EpicGames/PixelStreamingInfrastructure) and [hosting guide](https://dev.epicgames.com/documentation/unreal-engine/hosting-and-networking-guide-for-pixel-streaming-in-unreal-engine) | Matching infrastructure and network design | Shadow/Vagon Personal entitlement or production authentication |

Vendor price, lifecycle, microphone, API and backend hosting references are cited beside the exact claims in [the workstation workflow](03-workstation-workflow.md). No unsupported runtime-plugin recommendation is presented as selected. A suitable plugin may require a future vendor-specific trial and price check.

## Unresolved choices with concrete resolution gates

| Unknown | Resolve through | Blocks |
|---|---|---|
| Actual compute/region/storage/terms | W0 quote + W1 inventory | Paid workstation use |
| Usable remote automation surface | W2 file round-trip and log retrieval | Claims of autonomous remote installation |
| Engine/compiler/MetaHuman compatibility | W3 and A0 lock profile | Reproducible builds |
| Packaged audio-to-face implementation | A2 compiled fixture test with editor closed | Realistic interactive avatar completion |
| Backend provider and identity | B8 exact configuration and authentication test | Private deployment |
| API model/voice/profile/cost | B5/B7 account availability and capped live trial | Real voice/model calls |
| Private state, asset and evidence stores | B0/B3 storage mapping | Real personal data and licensed assets |
| Single-browser GPU transport | A6 provider/network/authenticated stream trial | Integrated browser avatar, not two-window prototype |
| Final likeness and voice preference | Samples after engineering proof | Cosmetic acceptance, not early mock work |

## Cost interpretation

The sourced illustrative Shadow + small backend + daily VM backups base is $75.59/month. It excludes model/voice usage, extra disks, asset storage, domain, streaming, taxes and add-ons. A larger backend brings that base to $91.19. These are planning arithmetic, not quotes accepted on Pete's behalf. See the full [cost worksheet](03-workstation-workflow.md).

Model/voice cost should be estimated from measured pilot usage and the chosen account's current prices: text input/output units × their rates, transcription input × its rate, speech output × its rate, plus any live audio/session charges in the selected profile. Avoid mixing per-minute and per-token rates. Record units, date, rate source, typical session length, monthly sessions, peak concurrency and budget headroom before a spending authorization.

The most useful first spend is a bounded feasibility test whose result determines the next investment. Buying always-on rendering or multiple GPU services before that evidence does not resolve the technical uncertainty.
