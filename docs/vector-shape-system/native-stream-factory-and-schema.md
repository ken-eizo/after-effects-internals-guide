---
status: research-active
last_verified: 2026-10-11
evidence: E0-G + E0-H + E2-X + E2-L + H
versions: AE2026 in-host/AE2025+2026 BEE+TDB runtime/SDK25.6
---

# Native Shape Factory — Creator Registration, Canonical Streams and Indexed Group Admission

## The actual goal

CompNodeAE should someday provide **its own host-native editable vector objects and Contents hierarchy**, participating in the AE Timeline, native Pen and Selection tools, expression/animation/Undo, host-native vector evaluation and rasterization, without depending on an extra standard Shape Layer. Copying paths into an existing Shape Layer, drawing an overlay through Drawbot or returning PF_World pixels fails this goal.

The project has now found a concrete native factory/registration boundary. This is a significant step beyond public AEGP traversal, **but it remains internal Adobe ABI, not a documented plug-in extension**.

## Confirmed layered architecture

```text
AE project / layer owner
   |
   |  BEE_Layer::RegisterStreams(bool) [BEE.dll]
   |    -> TDB.dll!Get_AE_StreamFactory()
   |    -> TDB_ScRegisterStreams::Register(match name, creator)
   |          -> TDB_StreamFactory::RegisterFactoryFunc(...)
   |             -> TDB_StreamFactory::CreateStream(...)
   |             -> Canonical stream / separated dimensions registration
   |
   +-- TDB_IndexedStreamGroup / TDB_NamedStreamGroup
   |     -> child admissibility (CanStore / AEGP_CanAddStream)
   |     -> UILayout and child insert/move/remove notification
   |
   +-- BEE_VectorLayer / BEE_VectorStream
   |     -> authored Contents / Path / Fill / Stroke / Filter
   |     -> PopulateVectorArt(time, stream-path)
   |     -> BEE_VectorArt::OriginInfo(TDB_StreamIDPath)
   |
   +-- BEE_SelLayer / BEE_GetSelectedShapePathsVec / Selection
   |
   +-- AGM / BEE_VectorLayer::Rasterize2DGraph / RG
          -> pixel materialization, only at the final rendering stage
```

This is a reconstructed *boundary map*. Direct call edges among `BEE_Layer`, `Get_AE_StreamFactory`, `TDB_ScRegisterStreams::Register`, `RegisterFactoryFunc` and `CreateStream` have offline code/IAT evidence. The exact connection between custom TDB child creation, native Pen editing and the production renderer is a **hypothesis** until host-tested.

## Internal factory entrypoints found in BOTH AE2025 and AE2026

| TDB function | 2025 RVA | 2026 RVA | Evidence meaning |
| --- | --- | --- | --- |
| `Get_AE_StreamFactory()` | `0x8100` | `0x81B0` | no-argument getter loads a global factory pointer |
| `TDB_StreamFactory::RegisterFactoryFunc` | `0x27400` | `0x285D0` | registers creator by MatchName; static code locks mutex and performs further setup |
| `TDB_ScRegisterStreams::Register` | `0x27060` | `0x28220` | wrapper calls RegisterFactoryFunc |
| `TDB_StreamFactory::RegisterCanonicalInstance` | `0x27130` | `0x28300` | canonical/prototype registration mechanism |
| `TDB_StreamFactory::CreateStream` | `0x26710` | `0x27920` | materializes native TDB stream from registered match name |
| `TDB_ScRegisterStreams::UnregisterAll` | `0x287A0` | `0x29850` | calls UnregisterFactoryFunc |
| `TDB_StreamFactory::UnregisterFactoryFunc` | `0x28BC0` | `0x29C10` | removes creator registration |

Exact MSVC signatures and DLL hashes: `research/findings/F-VECTOR-008-tdb-native-factory-registration.md`, and raw `datasets/ae-tdb-native-stream-factory-2025-2026.json`.

The register callback is a C++ `std::function` that returns `TDB_StreamBase*` and takes a `TDB_MatchName const&`, `TDB_StreamFactory*` and additional arguments. That is **not a stable C plug-in ABI**. It depends on private class layouts, compiler C++ ABI, allocator ownership, callback lifecycle, canonical stream ownership, and host shutdown sequencing. Merely discovering the function address does not solve those problems.

## Native Contents admission is partly a string grammar, not just a type enumeration

`BEE_VectorStream::VectorsStreamGroup::CanStore(TDB_MatchName const&)` disassembly refers to three **literal** strings in BOTH versions:

```
ADBE Vector Shape -
ADBE Vector Graphic -
ADBE Vector Filter -
```

The function calls a string-search-like helper and compares the returned address with the beginning of the candidate name. This is consistent with **prefix recognition**; a fourth direct `TDB_MatchName` equality check also exists. Whether an unknown prefixed MatchName is admitted by public `CanAddStream` must be measured independently. The native group may still reject its creation if no matching factory callback exists.

This explains why two distinct gates matter:

- **Structural parent admissibility**: Is this category of child allowed under this indexed parent? (`CanStore` / `CanAddStream` surface)
- **Type construction**: Does the factory know how to instantiate that precise match name? (`RegisterFactoryFunc` / `CreateStream`)

One gate passing never implies the other.

AE2026 E2-X data: 36/36 successful non-mutating CanAdd queries distinguished Shape Contents/Effects. Native vector names were allowed in Contents but rejected in Effect Parade; `ADBE Slider Control` showed the opposite. Experimental **unknown-prefixed** names will be tested through a distinct explicit menu command, NEVER through actual `AEGP_AddStream` until the factory relationship is proven.

## The stream UID anomaly is a separate potential feature-gate issue

AE2026 E2-X capture returned **0 for all 359 stream UIDs** while every UID API error field was zero. This contradicts the *expected utility* of the documented session-unique ID, but it does not prove that the function is generally broken. In local runtime export/import evidence, `TDB_Project::TDB_AreTDBStreamScriptingIDsEnabled` and AEIG's historical `EnableTDBStreamScriptingIDs` Beta flag suggest a related identity prototype, but there is **no verified causal connection**.

The new ShapeLayerAE v3 performs two UID calls with distinct nonzero output-buffer sentinels to distinguish host-written zero from untouched memory; that experiment is **compiled but not host-tested**.

## Five breakpoints to independent native objects

1. **Factory access**: pinned `TDB.dll` exact runtime and matching decorated `Get_AE_StreamFactory` symbol; read-only getter call and nonnull pointer test, no dereference. This is a prepared opt-in experiment, NOT yet executed.
2. **Custom matchname structural admissibility**: query unknown but matching Shape/Graphic/Filter prefix with `AEGP_CanAddStream` against Contents. Do not add.
3. **Creator+canonical registration**: recover TDB_MatchName private layout and std::function ABI; prove a complete, reversibly registered custom stream in a disposable host. Critical: callback code/vtable lifetime must outlive any host-owned instance and be correctly unregistered before unloading; save/reopen behavior must be tested.
4. **Native owner and Timeline**: attach a TDB_IndexedStreamGroup to a genuinely *independent plug-in-owned native object*, not to an ordinary Shape Layer. This may require internal BEE owner type dispatch. A generic group showing in some UI is insufficient.
5. **Native vector renderer/editor**: custom stream must provide evaluated art accepted by `BEE_VectorStream::PopulateVectorArt` and `BEE_VectorArt::OriginInfo`, expose native selection/vertex tools, and produce host AGM/RG pixels with correct caching and Undo. Registering a new data stream alone does not establish the vector-provider contract.

The architecture supports a plausible new native **stream class** experiment, but a full native **vector class/layer** remains a separate, harder question.

## Research and safety plan

- EXP-SHAPE-005 — real AE2026 public topology, metadata/UID and built-in admissibility (host verified).
- EXP-SHAPE-008 — read-only TDB factory export, per-version import/callsite/dataflow and string grammar (static verified).
- EXP-SHAPE-009 — **opt-in** unknown prefixed names CanAdd, plus UID sentinel control (built, not host-tested).
- EXP-SHAPE-010 — **opt-in** pinned private factory pointer Getter: verify module, decorated export, first-instruction fingerprint and call the zero-argument getter only, record nonnull Boolean. No pointer dereference, no registration, no factory callback; compiled but not host-tested.
- Future gated tests of creator registration ONLY on a disposable AE installation, clean project, exact pinned binaries, with crash capture and rollback plan; do not inject into an active working AE session or write third-party type definitions directly into production projects.

Production effects must still respect AE cache dependencies and rendering contracts: a native factory object is not an effect output channel. Custom Comp UI and Drawbot are separate UI facilities. Adobe SDK is not extended by these private findings.

## Source of truth

- `research/findings/F-VECTOR-008-tdb-native-factory-registration.md` — internal call graph.
- `research/findings/F-VECTOR-009-canstore-and-zero-uid.md` — user-confirmed E2-X vs static prefix predicate.
- `research/hypotheses/H-SHAPE-005-creator-registration-native-contents.md` — falsification and alternate models.
- `experiments/vector-shape/runs/EXP-SHAPE-005/20261011-user-host-v2` — raw sample.
- `datasets/ae-tdb-register-callsite-disasm-2025-2026.json` — bound direct/import calls.
- `datasets/ae-tdb-vector-canstore-disasm-2025-2026.json` — grouped type-admission predicate.
- `E:/ae25.6_61.64bit.AfterEffectsSDK/Examples/Headers/AE_GeneralPlug.h` — public supported baseline.
- Adobe official https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/ — stream API contract.
