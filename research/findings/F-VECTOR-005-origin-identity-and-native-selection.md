---
status: observed-static-only
last_verified: 2026-10-11
evidence: E2-L + E0-H + H
versions: AE 2025/2026 BEE.dll + Adobe SDK 25.6
---

# F-VECTOR-005 — Rendered VectorArt retains StreamIDPath provenance while selection models also use StreamIDPath

## Static evidence (distinct from runtime/ABI claims)

The BEE export inventories in `datasets/ae-vector-origin-identity-2025-2026.json` expose, in *both* binaries:

- `BEE_VectorArt::OriginInfo(TDB_StreamIDPath const&)`
- `OriginInfo::GetStreamIDPath()`, `GetCompletePath()`, `SetStreamIDPath(...)`
- `OriginInfo::AppendSyntheticIndex(unsigned int)`, `AppendSyntheticPath(...)`, `GetSynthIDPath()`, `IsOriginSynthetic()`
- `BEE_GetSelectedShapePathsVec(BEE_Layer*, std::vector<TDB_StreamIDPath>*)`
- `BEE_SelLayer::IsPathOrChildSelected(TDB_StreamIDPath const&)`
- `C_AGMDLTranslatePort::LayerSelectSetupPrePlayback(...)` and `LayerSelectTeardown()`
- `BEE_VectorLayer::GetVectorArt(...)` and `BEE_VectorStream::PopulateVectorArt(...)`

These are decorated export names, not verified stable binary contracts. In particular, *LayerSelect* naming is not sufficient to establish native Pen-tool editing or hit-test semantics. `OriginInfo` synthetic-path operations are compatible with evaluated instances (e.g. Repeater) but no proof of that specific origin has yet been captured.

The **public** SDK 25.6 `AEGP_StreamSuite6::AEGP_GetUniqueStreamID(AEGP_StreamRefH, int32_t*)` explicitly returns a host unique stream identifier. Its returned value is documented by Adobe as **session-unique**; the private representation and mapping to `TDB_StreamIDPath` remain unproven. Do not assume an ID is stable across project reopen. In header it first appears as a Stream Suite 6 addition and is marked `frozen in AE 22.5`. A direct equivalence between public UID and private path would be an unsupported leap.

## Two separable hypotheses

**H-SHAPE-004A**: evaluated `BEE_VectorArt` objects preserve the original TDB stream ID path for associating geometry with host edit selection, with synthetic paths representing non-timeline evaluated objects. Test through static call/dataflow + controlled native path selection + Repeater observation; falsified if provenance is used exclusively for diagnostics/cache without editor link.

**H-SHAPE-004B**: public unique stream IDs can be related to stable elements in the private `TDB_StreamIDPath`. Falsified by measured incompatible scope, reuse across groups/layers or differing identities after reorder/undo.

## Critical gap

There is currently **no** confirmed callback to register an external path as a native host selection target, no known mechanism to create independent host-owned Contents, and no proven effect-to-native VectorArt output channel. Provenance data within a native object is evidence of the *built-in* architecture, not evidence that external code can inject one.

## Further evidence

- Host-confirmed AEGP projection: `experiments/vector-shape/EXP-SHAPE-001-host-success.md`.
- Local symbol corpus: `datasets/ae-vector-origin-identity-2025-2026.json`.
- Read-only StreamSuite6/CanAdd probe: `D:\Developer\ShapeLayerAE\src\ShapeLayerProbe.cpp`, build-only until explicitly host-tested.
