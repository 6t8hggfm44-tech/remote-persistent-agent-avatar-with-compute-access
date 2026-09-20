# Next build: the Unreal character

Prepared 2026-09-20. This is the current execution order and supersedes older instructions to build more repository/chat features first. EA integration remains deferred. No remote workstation has been purchased, Unreal installed, or character scene built.

Pete has authorized preparation. Provider payment is separate from OpenAI billing and remains Pete's step after reviewing the final checkout price and recurring storage charge. Preparation is not authority for autonomous checkout or a new paid recurrence.

## Concrete workstation proposal

Use one Vagon Personal Windows computer with Blaze performance for a bounded authoring pilot. Published specifications are 64 GB RAM, 24 GB A10G GPU memory and 16 advertised cores; virtual cores are not established as equivalent to Epic's physical-core recommendation. Benchmark the actual machine before treating it as proven.

Published base compute is $3.57/hour, with region variation. Plan for a 225 GB disk: the 75 GB Personal disk starts at $7.99/month and three 50 GB expansions are listed at $5 each. That implies approximately $22.99/month storage. Five hours at the base rate plus that storage is $40.84 before tax and other charges. Verify expansion billing, available region, final rate and total in checkout. Proposed initial ceiling: $50 including fees, with at most five powered-on hours. This is a proposal, not spending authority. [Vagon pricing](https://vagon.io/cloud-computer/pricing), [regional rates](https://vagon.io/region-prices)

The recurring storage subscription is separate from compute and requires explicit approval. The proposed recurring cap is $30/month including fees; the estimate is $22.99 before tax. These caps remain a proposal pending Pete's review of the final checkout price; preparation is authorized, but no purchase or recurring charge has been completed or authorized for autonomous checkout. OpenAI credit cannot pay this provider. Do not enable automatic balance top-ups. If the quoted configuration exceeds the proposed total, return the revised quote before purchase. Five hours is a time limit, not a completion guarantee; downloads and shader compilation consume time too.

Shadow Power Pro remains a lower fixed-price alternative at $59.99/month, but its 28 GB RAM falls below Epic's 32 GB authoring recommendation. It has 8 virtual CPU cores and a 20 GB A4500. Storage descriptions conflict between current official pages and require checkout verification. Do not buy both providers. [Shadow Pro specifications](https://support.shadow.tech/hc/en-us/articles/33442461134609-Shadow-PC-Pro-Offers-Frequently-Asked-Questions), [U.S. offers](https://shadow.tech/us/shadowpc/offers/), [Epic requirements](https://dev.epicgames.com/documentation/metahuman/metahuman-hardware-requirements-in-unreal-engine?lang=en-US)

## Why Vagon rather than Oracle Always Free

Oracle's Always Free compute consists of CPU-only AMD/Arm instances with eligible Linux images; it does not include a graphics GPU. It could host a later lightweight backend, subject to actual capacity and testing, but it is not the proposed Windows Unreal character workstation. An existing Oracle account could still be useful. This phase has not verified Pete's Oracle account or instances; do not infer that they are absent. [Oracle Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)

Paid Oracle GPU infrastructure is an alternative. Oracle documents an NVIDIA RTX virtual workstation route with driver installation and RTX vWS licensing; we would also need to establish GPU quota/capacity, network access and a usable remote display. Vagon is proposed to reduce that infrastructure setup for the first character test, not because Oracle cannot run graphics. That is an engineering choice pending verified access and cost, not a claim of lower total price. [Oracle RTX workstation deployment](https://docs.oracle.com/en/learn/deploy-nvidia-rtx-oci/)

## Account and control gate

1. Pete signs in or creates a [Vagon account](https://app.vagon.io/) and handles password creation and account terms. Do not request credentials in chat. The unauthenticated login page was reachable; checkout and remote control are not yet verified.
2. Prepare the exact Windows/Blaze/disk/region selection and recurring charge for Pete's review. Pete handles checkout/payment after seeing the final price; do not complete purchase, subscribe or accept paid recurrence autonomously. Terms acceptance may require an action-time confirmation under the computer-use tool policy.
3. Record the real powered-on rate, prepaid balance, storage renewal date and stop procedure privately. Verify whether Personal exposes automatic stop or budget controls; Teams and Streams features are not evidence of Personal support. Closing a browser tab must not be treated as stopping billing.
4. Prove remote desktop control with a harmless file in a new avatar-only workspace. Verify actual RAM, GPU, driver, free disk and reboot/reconnect. The local Mac shell is not a remote Windows shell. No public RDP/SSH/WinRM or general-purpose build runner is needed.
5. At every paid session, set a stop deadline and a reserve for saving/shutdown. Use provider controls to stop; confirm its stopped state and usage afterward. Do not start unattended paid work without verified stop controls. Saved project files persist while compute is stopped, subject to the storage subscription.

## Execute the first character build

1. Use official Epic downloads. Pete completes Epic sign-in and applicable license prompts. Select a supported Unreal/MetaHuman version set and record the exact versions; install only necessary engine components and MetaHuman Creator Core Data. Add the supported compiler/SDK when packaging requires it. Check disk space before downloads.
2. Create a new isolated project and a small scene. Enable the required MetaHuman plugins, create a preset character in the in-engine Creator, rig it and assemble a UE Optimized character. Do not use the retired web onboarding route for a new MetaHuman account. [Creator setup](https://dev.epicgames.com/documentation/metahuman/getting-started-with-metahuman-creator-in-unreal-engine?lang=en-US), [assembly](https://dev.epicgames.com/documentation/metahuman/assembly)
3. Add camera, lighting and an idle animation. Use a temporary appearance until Pete reviews the rendered character. Appearance is not the AI persona; keep a stable character identifier for the later connection.
4. Use a fabricated greeting: “Hello, Pete. This is the first character test. My appearance and scene are saved. Project conversations will be connected in a later step.” Generate or record this sample without a paid API call or personal source material. Import the WAV, create audio-driven facial animation, and play sound and face from the same sequence. [Audio-driven animation](https://dev.epicgames.com/documentation/metahuman/audio-driven-animation)
5. Save, close and reopen the scene. Verify appearance, idle behavior, audible greeting and mouth movement. Then attempt a small Windows package using the exported animation and audio. Record editor and packaged results separately.
6. Capture a short demonstration, record memory/GPU usage and failures, preserve project/assets outside temporary build folders, and stop the rented machine. Keep licensed character assets and binaries out of this public source repository unless distribution rights and publication scope are verified.

Success for this increment is one actual Unreal character, a working sample spoken line, and repeatable reopening. An editor animation demonstration does not establish arbitrary live speech lip-sync in a packaged app. That runtime path needs a separate test. Persistent identity and saved files are also distinct from continuous 24/7 operation.

## Connection stages after the visual demo

The next integration is microphone → speech/text service → generated reply audio → Unreal playback and animation, with explicit mute and cancellation. Before enabling it, establish a new voice usage allowance and the exact permissions needed; the historical $1 allowance covered the initial text connection test.

Only after the character works should report access be considered. Proposed route: approved report excerpts → restricted read-only service → AI explanation → audio and optional captions → Unreal. Unreal receives no repository credential, report retrieval endpoint or OpenAI key. A service can deny writes, cloning and bulk export and enforce approved paths/revisions. Reading still copies text into memory, and cloud inference sends excerpts to the provider; zero-copy access cannot be promised.

Presence currently retains imported report snapshots locally. Preserve them. A future no-retained-report mode requires implementation and validation; clearing the selected report does not by itself exclude saved memories or conversation history. Keep this first character project entirely disconnected from that existing context.

## Executor stopping conditions

- Stop at unavailable account/payment/terms authority; record the exact missing action.
- Stop paid work before the approved time or financial limit is exhausted.
- Stop before granting the avatar personal-data access or live API use in this increment.
- If character authoring exceeds machine resources, save evidence and revise the host proposal; do not silently add a second subscription.
- Never mark a host, scene, package, lip-sync path or persistence test complete without actual execution evidence.
