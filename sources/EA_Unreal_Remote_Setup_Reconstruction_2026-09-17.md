# Remote Unreal Engine Executive Agent — Conversation Reconstruction

Reconstructed for Pete on September 17, 2026.

## Recovery status

This reconstructs the recommendation and architecture recovered from context for the missing conversation titled **Cloud Compute Rental**, begun September 16, 2026. It is not a verbatim transcript. The original workflow-chart asset was not recovered; the text chart below is a reconstruction. No cloud account, server, application, or repository was created or modified by preparing this note.

## The recovered recommendation

**Use Shadow PC Power Pro as the remote Unreal Engine/Blender workstation; keep the Executive Agent on a separate small always-on backend; present that agent through an Unreal MetaHuman with live voice.** Use Vagon Blaze for occasional heavier workloads rather than making an hourly GPU computer the permanently running home of the agent.

The central principle was: **the avatar is the interface, not the agent.** Agent persistence should not depend on whether Unreal Engine is running.

### Remote graphics workstation

The recovered recommendation named **Shadow PC Power Pro at $59.99/month**. The configuration described in that conversation was Windows 11, an RTX A4500-class GPU with 20 GB VRAM, 28 GB RAM, and 8 vCPUs. The live U.S. offers page rechecked for this reconstruction confirms $59.99/month, 28 GB RAM, 20 GB VRAM, and a Windows 11 cloud PC. The exact GPU and CPU allocation should be confirmed before purchase rather than treated as newly verified here. [1]

The role of this machine in the proposed setup is to run the Unreal editor, the avatar application, Blender, and graphics work while Pete operates it remotely from his Mac. Shadow provides macOS and browser access. This is a recommendation for a starting workstation, not a benchmark guarantee for an unbuilt project. [1]

### Persistent EA backend

The recovered discussion proposed a separate small always-on server with a **$10–30/month planning allowance**. No particular server provider was recovered. This figure is an estimate for basic hosting, not a confirmed quote or an all-inclusive assistant budget.

In the proposed architecture this backend would load the EA's live repository instructions, manage approved memory and task state, enforce permissions and approvals, connect to authorized tools, and make model/API calls. The small server would coordinate the system rather than be assumed to host the language model itself.

The EA repository identified by Pete is `6t8hggfm44-tech/persistent-ai-agent-`. This reconstruction does not activate Executive Agent mode or assert that the repository has been loaded in this session.

### Occasional heavier work

The recovered alternative was **Vagon Blaze at $3.57/hour**. The current pricing page lists 16 cores, 64 GB RAM, and a 24 GB A10G GPU. Vagon also charges a monthly storage fee, and pricing can vary by region; the hourly figure is not an all-inclusive monthly price. [2]

## Reconstructed workflow chart

This is a functional overview, not a finalized network-routing specification.

```text
               YOUR EXISTING EA REPOSITORY
        Constitution | policies | preferences | records
                              |
                              v
                  ALWAYS-ON EA BACKEND
          Approved memory | task state | permissions
                 Authorized tools | model calls
                              ^
                              |
                              v
                 LIVE CONVERSATION LAYER  <--- Your microphone
             Conversation API | spoken responses
                              |
                       Reply audio/events
                              v
                   REMOTE GPU WORKSTATION
                     Shadow PC Power Pro
                              |
                              v
                 UNREAL ENGINE + METAHUMAN
              Avatar | facial animation | 3D scene
                              |
                      Streamed video/audio
                              v
                       YOUR MAC / PHONE
                     The face and voice you see
```

The intended speech loop is: Pete speaks; the conversation system consults the repository-governed EA; the system generates a reply; the reply's audio and animation signals drive the avatar; Pete sees and hears the result remotely.

The GPU workstation was also intended to support the separate creative workflow: **Blender asset work -> Unreal scenes and interactive projects**. That creative environment is distinct from the EA's stored identity, instructions, and authorized task state.

## The first prototype that was proposed

The recovered prototype was deliberately small:

**Cloud Windows PC -> Unreal Engine -> one MetaHuman -> microphone input -> conversational agent -> spoken response with facial animation.**

A practical reconstructed build order is to validate remote Unreal/Blender operation, make one avatar in a simple scene, connect a working voice conversation, then integrate and test the EA's repository loading, memory, tools, and approval checks. This is a reconstruction of the build sequence, not evidence that those steps were completed or that every implementation component was selected.

The project would require an integration application joining the conversation, backend, and avatar. It would not require creating a new graphics engine or training a language model. Continuity should be implemented by loading approved repository instructions and authorized state, not by assuming that this ChatGPT conversation or its tools automatically move into a separate application.

## What was not recovered as a settled decision

The retrieved context did not establish a final choice of voice API, lip-sync plugin, browser-streaming stack, or small-server provider. Those details should not be represented as already selected.

As a current technical reference, OpenAI's Realtime API supports speech-to-speech conversations, tool calls, and browser/server connection patterns. It is a possible implementation route, not a confirmed recovered selection. [3] Epic describes MetaHuman as its framework for creating and animating digital human characters, including real-time facial-animation workflows. Connecting generated assistant speech to an avatar still requires implementation and testing. [4]

## Budget and always-on distinction

Using the original hosting allowance, Shadow plus the small backend would be approximately **$70–90/month before AI/voice API usage, additional storage, taxes, optional Vagon usage, and any streaming or always-on extras**. That arithmetic is not an all-inclusive operating-cost forecast.

OpenAI API usage is billed separately from a ChatGPT subscription. [5]

**An always-available EA is different from a continuously rendered 3D avatar.** The architecture was intended to let the inexpensive backend remain available while the graphics workstation runs only when needed. Availability does not imply continuous model inference or unrestricted autonomous action.

Shadow's current U.S. comparison lists a 210-hour monthly fair-use allowance for Pro, 8-hour sessions, a 120-minute idle limit, and an Always On option. The base subscription should therefore not be described as an unlimited unattended GPU server. A genuinely 24/7 visible avatar needs a separately verified hosting arrangement and budget. [1]

## Bottom line

**Rent the graphics horsepower, preserve the EA separately, and give it a live Unreal interface.** The aim was a persistent assistant with a face and voice—not an assistant whose existence depends on leaving the Unreal editor open.

## Sources rechecked for this reconstruction

[1] Shadow, U.S. offers and plan comparison: https://shadow.tech/us/shadowpc/offers/

[2] Vagon, Cloud Computer pricing: https://vagon.io/cloud-computer/pricing

[3] OpenAI, Getting started with the Realtime API: https://developers.openai.com/api/docs/guides/realtime

[4] Epic Games, MetaHuman: https://www.metahuman.com/?lang=en-US

[5] OpenAI, Managing billing for ChatGPT and the API platform: https://help.openai.com/en/articles/9039756

The sources above support current product capabilities and published prices. They are not sources for the historical conversation itself; that portion comes from recovered conversation context.
