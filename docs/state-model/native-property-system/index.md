---
status: active-reconstruction
last_verified: 2026-10-15
evidence: E0-G + E0-H + E0-S + E2-L + E2-X + H
versions: Windows After Effects 2025 / 2026; SDK 25.6; no equivalent macOS native ABI verified
---

# Native Property System — Lifecycle, Object Model and API Atlas

After Effects' **native property system** is a host-owned hierarchy of layers, effects, stream groups, leaf values, time-dependent state and renderer-facing identities. This section reconstructs the system **in execution order, from application initialization to shutdown**, rather than presenting disconnected lists of SDK calls or individual reverse-engineering experiments.

This is an *internal architecture guide*, not a supported C++ SDK. It distinguishes observed Adobe behavior from local binary analysis and the still-unproven possibility of a third-party native property-type provider. Start with [Application startup to shutdown](startup-to-shutdown.md).

## How to read this system

| Plane | What it answers | Canonical chapter |
| --- | --- | --- |
| Host boot / shutdown | When do native type providers and their factories become available? | [Startup to shutdown](startup-to-shutdown.md) |
| Stored object | What is a `TDB_StreamBase`, `TDB_Stream`, group, leaf or identity path? | [Native stream object model](stream-object-model.md) |
| Class provider | Who supplies a MatchName, typed C++ Creator and canonical instance? | [Factory registration and lifetime](factory-registration-lifetime.md) |
| Instance construction | How does an already registered Creator produce a Stream with native default-state initialization? | [Native instance creation](stream-instance-creation.md) |
| Parent insertion | Which CanStore, index, parent and cached-path steps actually adopt a child? | [Indexed child insertion](indexed-group-insertion.md) |
| Document persistence | How do saved MatchNames reconstruct native named/indexed Stream children? | [StreamGroup Read / Write](document-stream-serialization.md) |
| Parent schema | Why does one indexed parent accept a child and another reject it? | [Canonical groups and admission](canonical-groups-admission.md) |
| Concrete families | What do Paint, Text Animator and Shape Contents *actually* build? | [Paint, Text and Shape](paint-text-shape-hierarchies.md) |
| Editing lifecycle | How are properties addressed, animated, edited and persisted? | [Property operations](property-operations.md) |
| Owner / rendering | How does a stream relate to a comp layer, Timeline, Undo and BEE render? | [Owner, editor and renderer](owner-editor-renderer.md) |
| API boundary | What is supported in SDK 25.6 versus first-party private C++? | [Public and internal API atlas](api-atlas.md) |
| Audit / unknowns | Which claim is observed, version-limited or still hypothetical? | [Verification and version matrix](verification-and-version-matrix.md) |

## The central reconstructed architecture

```text
After Effects process / aelib native startup
  ├─ OM_Birth (Mask native Stream provider)
  ├─ FLT_Birth (Effect / Mask native Stream providers)
  └─ BEE_Birth (Layer, Text, Paint, Vector etc. built-in provider families)
       └─ TDB type factory registry (MatchName → C++ Creator)
            └─ eager canonical prototype
                 └─ leaf OR TDB_StreamGroup canonical layout
                      └─ parent-allowed child grammar

Project loading / user creates a layer or effect
  ├─ BEE layer/comp ownership (separate from TDB type registration)
  ├─ TDB Stream instance hierarchy + ID/path addressing
  └─ host Timeline property presentation
        ├─ values / keyframes / expressions
        ├─ editor commands and Undo / selection
        └─ native effect/vector evaluation, render graph and persistence

Shutdown and module teardown
  ├─ ensure all owned stream objects and callbacks can be released
  └─ unregister canonical prototype and creator; host-owned DLL shutdown
```

This is a **boundary map**, not a fully reconstructed scheduling trace. The `OM_Birth → FLT_Birth → BEE_Birth` code order and reciprocal death callsites occur inside the analyzed native `aelib.dll` initialization/teardown functions. It is not proven that every startup branch executes them identically, nor that a third-party AEX runs at an equivalent registration phase. The project/render/editor paths are distinct and must not be fused into one undocumented function.

## Three objects that must never be conflated

1. **Type registration:** a MatchName and Creator in a native `TDB_StreamFactory`. Registration proves neither that a user can add the type to a group nor that AE renders it.
2. **Canonical prototype and parent grammar:** a host-constructed native Stream template and the parent group's canonical list, `CanStore` policy and UILayout. `AEGP_CanAddStream` can be true for an unknown Shape prefix without any registered Creator.
3. **Document-owned instance and runtime:** an actual Layer/Effect/Stream object attached to host project state, with editor routing, keyframes, AEP persistence, render dependencies and safe lifetime.

A fourth boundary exists for genuinely **new native Layer families**: obtaining a TDB class does not enroll an owner in `BEE_CompItem` or make it a selectable new layer kind.

## Evidence shorthand in these pages

AEIG uses the existing [Evidence Model](../../foundations/evidence-model.md):

- **E0-G/H/S** — supported Adobe documentation / SDK header / Adobe sample; public contracts are allowed for third-party development.
- **E2-L** — locally installed Adobe PE export/import/disassembly or static data, usually SHA-pinned to the exact installed Windows version. It establishes *implementation evidence*, not a supported plugin interface.
- **E2-X** — controlled actual AE host observation; annotate fixture size and whether the host was changed.
- **H** — explicit assumption or unproven cross-boundary bridge, with an acceptance/falsification test.

Important: `E2-L` alone is not a behavioral claim about a fabricated external Stream. Host-observed data and mocks are different kinds of proof. See also [Streams and Properties](../streams-properties.md) and [System Overview](../../architecture/system-overview.md).

## Research coverage and the product boundary

| Question | Current qualified result | Strongest source |
| --- | --- | --- |
| Do Adobe DLLs register their own C++ Stream classes across DLL boundaries? | **Yes**, OM/FLT/BEE, both Windows releases | F-VECTOR-093/094, E2-L |
| Does `RegisterFactoryFunc` immediately build and initialize a native prototype? | **Yes**, including virtual canonical layout dispatch | F-VECTOR-095, E2-L |
| Does factory unregister release its own prototype? | **Yes**, on the analyzed successful branch | F-VECTOR-096, E2-L |
| Does native instance creation invoke the registered callback while holding the factory mutex? | **No on the verified success path**; callback is copied under lock, called after unlock | F-VECTOR-097, E2-L |
| Does indexed child insertion enforce native CanStore before changing parent state? | **Yes**, then index/cache and SetParent operations | F-VECTOR-097, E2-L |
| Can the native loader reconstruct a child without consulting registered Stream Creators? | The verified Named/Indexed loaders **call CreateStream using the saved MatchName** | F-VECTOR-098, E2-L |
| Can AEGP inspect brush-generated native Paint Strokes? | **Yes**, AE2026 read-only Paint fixture | F-VECTOR-083/087, E2-X |
| Can an unknown Stream class automatically join Paint/Text/Shape? | **No such general rule**; separate grammar/factory gates | F-VECTOR-084/065, E2-L + E2-X |
| Can a third-party AEX declare a completely new host-native C++ Stream/Group via SDK 25.6? | **No supported registrar identified in the scoped SDK audit** | F-VECTOR-088, E0-H/E2-L |
| Has a foreign custom CNL group been created in Adobe's standard Timeline? | **No; NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM** | EXP-SHAPE-090/091, F-VECTOR-095/096 |
| Can a foreign BEE Layer be attached and used as a fully independent new layer kind? | **Unproven**; additional owner/editor/render/persistence gates | F-VECTOR-055/071/079 |

## Precise feature terminology

The Paint feature here is the **Paint effect created by using AE's Brush tool** (the effect with nested Strokes and Brush). It is *not* Paint Bucket or Brush Strokes filters. The installed `Required/Paint.aex` is a real AEX, but its native property grammar is registered by Adobe's BEE/TDB host and the AEX uses an internal host `Paint Suite`.

A collapsible `PF_ADD_TOPIC`, pseudo-effect, preexisting Shape Layer carrier, hand-rolled timeline or Drawbot panel is not equivalent to registering a new host-native type. These surfaces remain useful for other products, but do not satisfy the native-provider research goal.

## Reproducibility and compatibility

These chapters synthesize F-VECTOR-037/054–096 and EXP-SHAPE evidence. Original evidence and source receipts remain in `research/findings/`, `experiments/vector-shape/` and `datasets/`. Individual chapters name the relevant exact files and version-scoped offsets. No Adobe binaries are redistributed.

The analyzed private ABI was observed in Windows x64 AE2025/2026, **not certified as stable**. No macOS equivalent Creator/ABI has been validated, and the private-registration disposable AEX has **not** been run in AE. Production projects and Adobe installations were not modified by these reconstructions.
