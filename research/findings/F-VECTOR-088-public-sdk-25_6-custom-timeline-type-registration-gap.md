---
date: 2026-10-14
status: PASS scoped audit of public AE SDK 25.6 headers; no supported foreign native Stream creator/provider found there; host-native product BLOCKED
evidence: E2 reproducible source audit of 70 installed Adobe SDK headers, public SDK 26.5 change history, official Adobe developer support
---
# F-VECTOR-088 — Public-SDK external native property-type registrar: scoped absence proof and product gate

## Exact original requirement

An independent third-party C++ AEX must define and place **new** `CNL:CustomProperty`, `CNL:CustomNamedGroup` and `CNL:CustomIndexedGroup` in **Adobe's own standard Timeline** as genuine native host-owned streams, just like built-in Paint Brush or Text Animator. It must not substitute its own panel, preexisting Shape/Mask/Text property carrier, a static PF topic or PF parameter, a pseudo-effect, or a CNL-only engine.

## Actual public SDK 25.6 findings

The installed `E:/ae25.6_61.64bit.AfterEffectsSDK/Examples/Headers` contains **70 .h/.hpp headers**.

All 70 were scanned via `experiments/vector-shape/probe-src/tools/verify_public_sdk_native_provider_gap.py`. The SHA-pinned audit dataset is `datasets/ae25_6_public_native_stream_provider_api_scope_audit.json`.

Specific positive/negative inspection:

- `AE_GeneralPlug.h:2745`: `AEGP_RegisterSuite5` contains **12** registration callbacks: command/update/death/version/about/Artisan/IO/idle/tracker/interactive Artisan/localized preset strings. **None register native TDB Stream C++ classes, Layer classes or arbitrary parent child-layout definitions.**
- `AE_GeneralPlug.h:1640`: `AEGP_DynamicStreamSuite4` contains **26** methods including `AEGP_CanAddStream` and `AEGP_AddStream`, which manipulate already host-registered admissible children.
- `AE_GeneralPlug.h:841`: `AEGP_CreateVectorLayerInComp` creates an existing Adobe vector Shape Layer, not a new foreign Layer class.
- No declaration of `TDB_StreamBase`, `TDB_StreamFactory`, `TDB_ScRegisterStreams`, `BEE_Layer`, `RegisterStreamFactory`, `RegisterNativeStream` or `RegisterNativeLayer` found in any of the 70 public headers.

**This is a scoped absence result, not a proof of nonexistence in Adobe internal/partner SDKs or future releases.** Matching substring absence would not rule out an unnamed generic native provider API in a different SDK, which is why all exposed registration and dynamic-stream suites were also enumerated.

The community-maintained Adobe C++ plugin guide's 26.5 (Sept 2026) notes add guides, parametric mesh creation and StreamSuite7 per-layer render stage, **not** a foreign TDB/BEE stream class provider. Official developer entry: `https://developer.adobe.com/developer-support/`; C++ SDK guide: `https://ae-plugins.docsforadobe.dev/intro/whats-new/`.

## Why the Adobe built-in Paint AEX does not imply third-party parity

Paint is genuinely provided as `Required/Paint.aex`, but:
1. Its `Paint Suite` resolves to a **host-registered** `AfterFXLib.dll!PaintEffectEntryPoint`; ordinary SDK effect parameters do not own this suite implementation.
2. The `BEE_PaintAtom`, `BEE_PaintStrokesGroup`, `BEE_PaintEffect` factories are registered by **host** `BEE_AVLayer::RegisterStreams` through TDB private C++ factories, as confirmed in F-VECTOR-080 and 081.
3. Its parent `BEE_PaintStrokesGroup` accepts only known canonical children; actual AE2026 host measurement denied synthetic `CNL:PaintAtom` (F-VECTOR-083, 087).
4. The Paint Path native leaf reports `AEGP_StreamType_NO_DATA`, illustrating the special private value semantics (F-VECTOR-087).

The existing independent C++ CNL typed timeline is a legitimate engine, but does not solve host stream creation/ownership/UILayout/Undo/keyframing/archive. No unsupported call has been executed, no Adobe installation DLL patched and no native foreign type inserted.

## Formal shipping decision for the exact desired product

**Current status: `NOT_IMPLEMENTED_NATIVE_ADOBE_TIMELINE_CUSTOM_TYPE`.**

A legitimate PASS requires direct observed AE2026 native Timeline proof of a third-party-owned `CNL:` type or group, native edits and keyframes, save/reopen .aep, undo/redo, correct unload and both Windows/macOS behavior. **None of these are achieved for a foreign class.** Do not label AEGP can-add TRUE or CNL-only engine PASS as fulfilment.

Do not unconditionally invoke private `TDB_ScRegisterStreams::Register` inside the user's running AE to fake progress; private ABI, host startup order and process lifetime remain unsolved. Mock host experiments can validate C++ ABI assumptions but do not bypass admission.

## Missing authority / next decisive route

Seek a documented **native Stream Provider and parent canonical UILayout extension ABI** from Adobe After Effects C++ SDK team. Ask specifically whether `TDB_ScRegisterStreams`/BEE native types or an alternate partner SDK are offered for third parties, and if not whether arbitrary native groups will be supported.

Draft: `docs/vector-shape-system/adobe-native-property-provider-sdk-inquiry.md`.

Without such an interface, a safe, robust third-party AEX that meets the exact requested native property semantics **cannot currently be delivered from the inspected public SDK**. Other implementations (PF static topic, pseudo effect, Shape carrier, separate UI) are distinct products and not acceptable as silent substitutes.
