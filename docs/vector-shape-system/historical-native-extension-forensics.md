---
status: research-active
last_verified: 2026-10-11
evidence: E0-G + E0-H + E0-S + E2-L + E3 + H
versions: AE 3.0 / AE 5.0 historical documentary surfaces; CS3 (8.0) feature introduction; CS6 / CC2014 / SDK 25.6 headers; AE 2025 / AE 2026 binaries
---

# Native Shape System Forensics: Forgotten Hooks, Factories and ABI Frontiers

## Goal: independent native shape ownership

The aim is NOT adding paths to an existing shape layer. Success requires a third-party plug-in to make AE recognize a **new**, independently owned, mutable native Contents-like hierarchy, accept its paths into native selection/Pen editing, and render those paths via AE's production vector evaluator/rasterizer without first creating a standard Shape Layer. For CompNodeAE this would add a non-pixel geometry result type, not merely a Drawbot UI overlay or effect pixel output. Currently **no supported or independently verified route achieves all three**.

Separate at least **six contracts**: factory/type definition, runtime host registration, native owner/identity attachment, Timeline tree display/undo, path editor identity binding, native vector evaluation/render handoff. A function taking a `TDB_StreamFactory*` proves none of the latter five by itself.

## Product chronology: the pre-shape API is not the Shape Layer API

| Date/version | Evidence | Scope |
| --- | --- | --- |
| 1995 / AE 3.0 | Adobe's feature history: Bezier masking, Illustrator continuously rasterized footage | Native vector mask *tooling* predates shape layers. Do not project Contents or BEE_VectorStream back into AE 3.0. |
| AE 5.0 | Historical and current SDK `PF_PathQuerySuite1`/`PF_PathDataSuite1` headers annotate their version-1 contract as frozen in AE 5.0 | Ancient and frozen **mask path reference/query** surface; not a vector result/output contract. |
| 2007 / AE CS3 (8.0) | Adobe feature-history project and contemporaneous 2007 Shape Layers article | Native Shape Layers with editable paths/fills/strokes/shape operators added to product. |
| 2012 / CS6 | Locally archived distributed `AE_GeneralPlug.h` and `AE_GeneralPlugOld.h` | AEGP stream grouping, indexed-group mutation, and mask suites present by this SDK, not proof of a CS3 third-party custom factory. |
| 2014 / CC2014 | Locally archived headers | Same distinctive public AEGP shape-adjacent functions; no evidence from these selected headers of an external type-factory registration contract. |
| SDK 25.6 | Locally distributed headers/Adobe Streamie sample | Enumerate/modify *existing* stream groups; not creator of arbitrary native stream classes. |
| AE 2025/2026 | Locally installed `BEE.dll` PE export and bounded disassembly | Internal per-layer registration-named routines and vector-stream/art/raster functions persist, but callers and registrability remain private. |

Sources: https://github.com/AdobeDocs/after-effects-feature-history (AE history; AdobeDocs); https://www.provideocoalition.com/shape_layers/ (2007 article); https://ae-plugins.docsforadobe.dev/effect-details/working-with-paths/ (current official Effect path API); `datasets/ae-shape-native-extension-lineage-2026.json` (local header/binary source hashes).

## An older substrate than Shape Layers

The **distributed SDK 25.6** explicitly calls the dynamic-stream interface `new Dynamic Streams API for AE6` and marks its DynamicStreamSuite4 version as `frozen in AE 9.0`. Adobe’s feature history dates Shape Layers to CS3/8.0 (July 2007). Thus, a dynamic property/stream substrate existed **before** native Shape Layers; shape-specific Contents likely built atop a reusable stream representation. The external registration of an arbitrary native type is nevertheless unproved. A much later public `AEGP_GetUniqueStreamID` is available from AE22.5 onward and is **session-unique**, not guaranteed persistent across save/reopen. See [Native Vector Editability and Provenance](native-edit-and-provenance-bridge.md).

## Public contract, literal SDK 25.6 semantics

The distributed `AE_GeneralPlug.h` enumerates `AEGP_StreamGroupingType_NONE=-1`, `LEAF=0`, `NAMED_GROUP=1`, `INDEXED_GROUP=2`. Its comment on `AEGP_GetNumStreamsInGroup` says **error on leaf** and `AEGP_GetNewStreamRefByIndex` says **legal for namedgroup, indexedgroup, not leaf**. `AEGP_AddStream`, `AEGP_DeleteStream` and `AEGP_ReorderStream` expressly operate in the scope of *existing* indexed groups. The public Effect SDK's parameter topics do not dynamically instantiate a host-owned indexed Contents type.

Some contemporary third-party notes contradict the *real header* (for example a shape SDK KB displays `NONE=0`). Treat that note as a discovery lead only, not ABI fact. The supplied client error `{GetNumStreamsInGroup only works on groups}` follows directly from erroneously treating LEAF as a group. See the incident note `experiments/vector-shape/EXP-SHAPE-001-host-failure.md`.

## What the private binary *actually shows*

Two installed, different-version PE binaries were inspected **offline**, without executing their exports:

| Runtime signature / symbol | AE 2025 RVA | AE 2026 RVA | Strongest warranted inference |
| --- | --- | --- | --- |
| `BEE_GenericShapeStream(TDB_MatchName*, TDB_StreamFactory*, ...)` ctor | `0x2ACF0` | `0x2A930` | Shape-associated stream construction accepts factory/identity objects. No external registration implied. |
| `BEE_VectorLayer::RegisterStreams()` | `0x6E4100` | `0x708A30` | Per-layer registration-named routine persists across versions. Meaning must be reconstructed from callees, not title alone. |
| `BEE_TextLayer::RegisterStreams()` | `0x5AE290` | `0x5CD7E0` | Text layer also has a registration-named routine: not vector-only. |
| `BEE_Layer::RegisterStreams(bool)` | `0x2EC310` | `0x2F4E50` | Base layer has a related registration-named function. |
| `BEE_VectorStream::PopulateVectorArt(...)` | `0x6ECB60` | `0x710EE0` | Stream-to-evaluated-vector-art boundary present. |
| `BEE_VectorLayer::Rasterize2DGraph(...)` | `0x6E3E90` | `0x708720` | Vector layer owns raster graph materialization routine. |

Binary hashes and exact matches: `datasets/ae-shape-native-extension-lineage-2026.json`; bounded instruction and call-target sampling: `datasets/ae-vector-registerstreams-static-2025-2026.json`.

### Important disassembly-based counterevidence

The initial bounded instruction trace for `BEE_VectorLayer::RegisterStreams()` contains direct calls into `BEE_CmdSetStreamBaseFlag`, `BEE_CmdSetStreamVary`, `BEE_ResetStream`, `BEE_CmdSetExpressionEnabled`, `BEE_CmdSetExpression`, `BEE_CmdSetExpressionFlags` and `BEE_SelectKeyframe`. Similar patterns occur in 2026. The call to `RegisterStreams` may therefore install **commands/handlers for streams**, not exclusively stream *type registrations*. We must locate the actual registration data writes and callers before claiming a type factory.

`BEE_AVLayer::RegisterStreams` also calls `BEE_CmdReorderIndexedGroupEntry` in the analyzed window. This is a worthwhile cross-layer lead for native Timeline structural actions. The bounded disassembly is not a complete control-flow graph, and exports targeted by an indirect jump/call cannot be resolved simply from decorated names.

### Reconciling the counts

BEE's total exports: 13647 (2025) vs 14182 (2026). `BEE_VectorStream` substring appears in 1452 symbols in each version; `TDB_StreamFactory` in 365 vs 401 (full BEE export scan, more than the earlier **filtered** shape-only AEIG CSV). These counts are not independent evidence of type extension and cannot be equated to function counts: a class name can appear in many constructors/templated signatures.

## Actual TDB.dll native factory registration (revised frontier)

A separate 2025/2026 static audit found the host-owned `TDB.dll`, its globally accessed `TDB_StreamFactory`, and its internal `RegisterFactoryFunc`/`TDB_ScRegisterStreams::Register` machinery. Resolved BEE.dll import calls prove base layer initialization calls those registry functions. The vector Contents `CanStore` contains three native type-name prefixes. This is a deeper capability boundary than the older BEE symbol-only study; see [Native Stream Factory and Shape Schema](native-stream-factory-and-schema.md). It must not be represented as a public third-party plug-in SDK.

## Direct call-site confirmation of a central initialization sequence

Full executable-section static scans (4.49 million decoded instructions in AE 2025; 4.63 million in AE 2026) identified consecutive **direct** calls to multiple layer-class `RegisterStreams` routines from one shared code region in each build. The VectorLayer direct-call site is RVA `0x36DE38` in 2025 and `0x378858` in 2026. This is reproducible, cross-version evidence of a **central layer stream registration/initialization sequence**. The enclosing routine's name and registry data structures are not established, so it is not yet evidence that third-party types can be registered. The scan found three direct references to `PopulateVectorArt` per build but no direct `BEE_VectorLayer::Rasterize2DGraph` calls; virtual/indirect dispatch may explain the latter.

Raw E2-L artifact: `datasets/ae-vector-registerstreams-xrefs-2025-2026.json`. The first attempt without Capstone SKIPDATA prematurely stopped and was replaced; instruction decoding of an executable section is not a perfect function-boundary reconstruction.

## Private integration path: hypotheses with required proof

1. **Factory ownership / schema** — locate the host bootstrap that creates the factory, installs built-in type descriptors, owns/refcounts the resulting objects, and controls allowed match names. Is this a closed built-in registry? A callable export does not make an externally usable extension point. Alternative: registration routines are only operation-handler tables.
2. **Layer identity and object ownership** — compare `BEE_Layer`, `BEE_AVLayer`, `BEE_VectorLayer` construction/creation and attachments to a `BEE_CompItem`. Does the host Timeline require a private class tag? Test base and vector layer owner invariants separately.
3. **Timeline indexed mutation** — follow `BEE_CmdReorderIndexedGroupEntry`, selection flags, command dispatch, Undo and persistence. The ordinary `AEGP_DynamicStreamSuite` may be an adapter on top of this but cannot itself declare a new custom owner.
4. **Pen-tool target** — discover how a selected TDB path and `OriginInfo(TDB_StreamIDPath)` are converted into UI tool handles. A Drawbot custom overlay is insufficient; host Pen tool editing is mandatory for full parity.
5. **Geometry evaluation** — `PopulateVectorArt` maps a time-specific stream path into `BEE_VectorArt`; investigate path ownership and cache invalidation. A hand-created VectorArt in C++ proves little unless it participates in the host's dependency and property graph.
6. **Native renderer** — trace the VectorArt to AGM and `Rasterize2DGraph`, distinguish Shape-native rendering from an effect using AGM to emit `PF_World`. A pixel-output effect remains a raster effect even if it internally calls the same mathematics.
7. **Persistence, reproducibility and compatibility** — a native object must save/reopen, retain stable selection, support Undo/redo, keyframes and expression evaluation, survive AE restart, and render consistently. Major-version binary exports have different RVAs; no binary ABI stability is promised.

No use of private function calls or host memory patching is justified by the present evidence. Later experiments require an isolated disposable AE session, a backed-up project, frozen exact binary hash, runtime trace provenance, explicit crash/rollback strategy, and independently reproduced minimal hypotheses. Avoid shipping private Adobe headers or binary contents to source control.

## What counts as a breakthrough?

- **S0**: AEGP reads Shape Contents: baseline, **not success**.
- **S1**: an independent host-owned indexed property tree exists in the standard Timeline, without creating a Shape Layer: **structural breakthrough**.
- **S2**: host's native Pen/Selection tools edit and animate the new paths: **tool integration**.
- **S3**: CompNodeAE emits geometry and AE evaluates/rasterizes it via the native vector pipeline with correct time/cache/undo/save behavior: **full experimental parity**.
- **S4**: same extension works across at least two pinned AE builds without unsafe patching: **compatibility evidence**, not a promise of future versions.

## Evidence files / reproduce

- `research/findings/F-VECTOR-004-registerstreams-cross-version.md` — claim-level evidence summary.
- `research/hypotheses/H-SHAPE-001-native-stream-registration.md` and `H-SHAPE-002-native-vector-output.md`.
- `experiments/vector-shape/EXP-SHAPE-001-host-failure.md` — screenshot-reported precondition bug, repair and pending retest.
- `experiments/vector-shape/EXP-SHAPE-004-registerstreams-cross-version.md` — binary/probe receipt.
- `D:\Developer\ShapeLayerAE\tools\compare_vector_lineage.py`, `analyze_registerstreams.py`, and read-only AEGP observer.
