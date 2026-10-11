---
status: research-active
last_verified: 2026-10-11
evidence: E0-G + E0-H + E2-L + E2-X + H
versions: SDK25.6 / AE2026 in-host / AE2025-2026 BEE.dll
---

# Native Vector Editability and Object Provenance — A Cross-System Research Program

## Why this boundary matters

CompNodeAE's ambition is **not** to produce a bitmap, create a separate Shape Layer, copy shape paths into one, or simulate the Pen tool with a Custom Comp UI. The target is a plug-in-owned native **stream/object** that the AE Timeline, tool/selection subsystem, VectorArt evaluator and AGM/RG renderer recognize in one coherent host architecture. Those four native effects do not follow merely from C++ access to a path array.

The current AE2026 real-host AEGP capture confirms the public `ADBE Root Vectors Group` is an INDEXED_GROUP, with named Rectangle/Fill children, while the Effect Parade is another indexed group on the same layer. That demonstrates a shared **AEGP stream traversal** surface, not that external effects can define a new typed/native Contents group.

## Four independent identity domains

1. **Public AEGP StreamRef** — opaque, short-lived `AEGP_StreamRefH`. It is not a serializable pointer.
2. **Public session UID** — `AEGP_StreamSuite6::AEGP_GetUniqueStreamID` (added AE 22.5). Official Guide says **session-unique numeric ID**, not stable persistent ID across sessions. The returned ID must be considered only within the session unless a contrary controlled test proves a stronger guarantee.
3. **Private authored TDB path** — `TDB_StreamIDPath` used by native stream/path commands and selection. Its exact layout and relationship to the public UID is not known.
4. **Evaluated art's origin path** — `BEE_VectorArt::OriginInfo` embeds/returns StreamIDPath, with extra synthetic path information; it is not the same object as the authored stream and should not automatically be assigned the authored object's lifetime.

## Independently observed static sites in two host binaries

| Private function family | AE2025 | AE2026 | Evidence |
| --- | ---: | ---: | --- |
| `OriginInfo::AppendSyntheticIndex` | 7 direct CALLs | 8 | executable-section Capstone direct-reference scan |
| `OriginInfo::GetStreamIDPath` | 2 | 2 | direct-reference scan |
| `BEE_SelLayer::IsPathOrChildSelected` | 2 | 2 | direct-reference scan |
| `C_AGMDLTranslatePort::LayerSelectSetupPrePlayback` | 3 | 4 | direct-reference scan |
| `BEE_VectorLayer::GetVectorArt` | 5 | 6 | direct-reference scan |
| `BEE_VectorStream::PopulateVectorArt` | 3 | 3 | direct-reference scan |
| `BEE_VectorArt::GetBounds` | 4 | 4 | direct-reference scan |

`BEE_GetSelectedShapePathsVec` and `OriginInfo::GetCompletePath` each had zero **direct** references, which does not establish non-use. They may be called through indirect callbacks, virtual dispatch, or another module. The code-section scanner used Capstone SKIPDATA, scanned ~4.49M and ~4.63M instructions and produced `datasets/ae-vector-selection-origin-xrefs-2025-2026.json`. Its inferred “nearest preceding export” is **not** a verified function boundary; treat as location hint only.

**Strongest current inference:** synthetic origin append operations and origin stream-path lookup are part of executed-looking code paths inside the native vector runtime, not simply type declarations. A native selection subsystem also consumes TDB stream paths. **Still not established** is the precise dataflow from rendered `OriginInfo` through hit testing into a selected editable path, nor any externally registerable native edit target.

## Strong compatibility clues and limits

- `BEE_VectorArt::OriginInfo(TDB_StreamIDPath const&)` exists in 2025 and 2026.
- `OriginInfo::AppendSyntheticIndex` and `AppendSyntheticPath` imply separate authored and evaluated/synthetic child paths. **Hypothesis:** path modifiers/repeaters may create synthetic instances without independent authored Timeline nodes. Do not promote to proof for any particular modifier without runtime traces.
- `C_AGMDLTranslatePort` constructors include `PF_World*` and a `BEE_IllusShapeTarget` reference; this is strong static evidence of a **raster materialization bridge**. It does not provide an Effect SDK geometry output return type.
- The Adobe-distributed `AEGP_INTERNAL` gate references a non-distributed `AE_GeneralPlug_Private.h` with host-owned stream and layer types. An opaque public handle does not authorize direct cast to those private types. See `F-ABI-011`.
- `BEE_GetSelectedShapePathsVec` exists, takes `BEE_Layer*` and `std::vector<TDB_StreamIDPath>*` according to MSVC decoration, but has no validated plug-in-facing lifetime, ownership or thread contract.

## Controlled tests and falsification

**EXP-SHAPE-005** (built but not yet loaded into the host): dump UID, internal grouping flags, stream type, and a non-mutating `CanAddStream` matrix for known built-ins, in addition to the original topology; never call `AddStream`. The plugin is located at `D:\Developer\ShapeLayerAE`, and the source is mirrored under `experiments/vector-shape/probe-src`.

Then collect successive snapshots of the **same host session** before/after native Timeline child reorder and a group Path edit, and before/after Undo. Compare public session UIDs and topology, not `StreamRefH` pointer values. Test a Shape Layer, a nonshape layer with a normal effect, an empty Shape Layer, and a Repeater case. Full parity remains conditional on independent native type registration, host Pen selection, evaluation and project persistence.

**Failure criteria**: a plugin-only custom indexed group cannot be instantiated as a native persistent stream type; a synthetic evaluated instance is not associated with a selectable Timeline stream; or VectorArt can only be drawn through a raster bridge. Each failure narrows the native extensibility frontier without negating successful public AEGP traversal.

## Sources / raw artifacts

- Adobe official AEGP Stream Suite reference: https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/ (`AEGP_GetUniqueStreamID` is explicitly session-unique; AE 22.5+).
- Distributed local SDK `E:\ae25.6_61.64bit.AfterEffectsSDK\Examples\Headers\AE_GeneralPlug.h`: DynamicStreamSuite versioned interface, group type enum and GetUniqueStreamID declaration.
- `experiments/vector-shape/EXP-SHAPE-001-host-success.md` and raw `experiments/vector-shape/runs/EXP-SHAPE-001/20261011-first-success/shape_layer_stream_tree.tsv`.
- `datasets/ae-vector-origin-identity-2025-2026.json`, SHA-256 `E6B96B78AE68E77C274B71F8BA31644E0F5D8F81FA9E1E70739251E7E3AE7C7D`.
- `datasets/ae-vector-selection-origin-xrefs-2025-2026.json`, SHA-256 `EE9B818E0DE72405E6116E1C6CC006F663789C026802757135BCD85DAFB8E253`.
