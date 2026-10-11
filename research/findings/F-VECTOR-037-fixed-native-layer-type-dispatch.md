---
status: strongly-supported-static-two-native-binaries
last_verified: 2026-10-12
evidence: E2-L
versions: exact installed AE2025/2026 BEE.dll
---

# F-VECTOR-037 — Native BEE layer factory is an eight-way type dispatcher with seven concrete constructors

## Why this is a product-level constraint

A plugin-defined native vector **layer** must be more than a registered `TDB_Stream` or `BEE_VectorStream::Operator`. The actual existing host layer construction function `BEE_Layer::CreateLayerFromType(int,BEE_CompItem*,unsigned char)` has now been independently decoded in both installed BEE versions. Its observable implementation is a bounded **image-relative switch table** with eight entries and direct construction of built-in BEE layer classes, rather than an arbitrary third-party MatchName-to-layer-creator lookup.

This excludes the naïve proposal that a foreign TDB MatchName registration alone will cause this *specific factory* to instantiate an entirely new layer class. It does **not** globally prove that no other Adobe extension route exists.

## Exact static evidence

| Native layer kind (integer) | AE2025 and AE2026 destination concrete native constructor |
| --- | --- |
| 0 | `BEE_AVLayer` |
| 1 | `BEE_LightLayer` |
| 2 | `BEE_CameraLayer` |
| 3 | `BEE_TextLayer` |
| 4 | `BEE_VectorLayer` |
| 5 | `BEE_ModelLayer` |
| 6 | `BEE_AVLayer` (shares kind 0 branch) |
| 7 | `BEE_ParametricMeshLayer` |

AE2025 export `CreateLayerFromType` is at RVA `0x2e3e10`, with jump table at `0x2e4108`; AE2026 export is at `0x2ecd00`, table RVA `0x2ecfe8`. Both functions compare the integer type to 7 and branch out of the table for greater types. The table entries were decoded directly as eight little-endian image-relative RVAs from the pinned BEE binary, not guessed from enum names. Each destination was followed into a direct call to the corresponding constructor. `BEE_VectorLayer` is specifically kind 4 in both versions. The function uses a `BEE_CompItem*`, TDB factory/MatchName state and native constructor arguments, NOT an open plugin-class factory parameter. AE2025 additionally gates kind 7 through `BEE_BetaFeature_Is3DParametricMeshEnabled`; that call is not present in AE2026's examined body.

The out-of-range branch reaches a native diagnostic/assert-related path rather than a new creator lookup; do not make broader claims about exceptions without real runtime evidence. These RVAs and the vtable indices of native classes differ across versions and are not a stable SDK.

## What this changes about our implementation strategy

**Creating a new BEE_Layer subclass through the existing integer dispatcher is not a demonstrated viable plugin feature.** A new type would need an additional registered owner dispatcher, a host-supported custom layer provider, or modification/replacement of this compiled dispatch (not an acceptable stable product approach). Without independent evidence for an alternative extension route, do not spend cycles implementing a foreign `BEE_Layer` vtable and hoping that `TDB_StreamFactory::RegisterFactoryFunc` constructs it.

The higher-priority open route is **a plugin-owned host-recognized Contents-like stream under a valid existing native owner**, which must then solve genuine Pen/edit identity and native VectorArt/RG delivery. This route avoids claiming to have created an entirely new BEE Layer kind, but a built-in Shape/Mask carrier is still unacceptable as the final result. Native Contents owner research must find a genuinely independent plugin-attached owner rather than reusing built-in Shape output.

## Falsification and boundaries

This proof is limited to `BEE_Layer::CreateLayerFromType` in the two pinned versions. It does not rule out another editor/importer factory, undocumented registration of Layer subclasses elsewhere, or future API support. The function's initial virtual call at vtable +0x68 and post-create virtual call may require host owner initialization; neither makes the switch open.

Evidence: `datasets/ae-native-layer-factory-type-dispatch-2025-2026.json`, `datasets/ae-native-layer-factory-jump-table-2025-2026.json`, `datasets/ae-native-layer-factory-closed-switch-verified.json`. Repro tools are in `experiments/vector-shape/probe-src/tools/`. No AEX installed, no AE native constructor invoked.
