---
status: strongly-supported-static
last_verified: 2026-10-11
evidence: E2-L + H
versions: AE2025 and AE2026 exact installed BEE binaries
---
# F-VECTOR-006 — Native vector origin identity and selection operate on stream paths

The private installed-runtime MSVC export names (E2-L) establish `BEE_VectorArt::OriginInfo` as a type storing `TDB_StreamIDPath`, including the functions `GetStreamIDPath`, `GetCompletePath`, `AppendSyntheticIndex`, `AppendSyntheticPath`, `GetSynthIDPath`, and `IsOriginSynthetic`. Independent selection-named symbols `BEE_GetSelectedShapePathsVec` and `BEE_SelLayer::IsPathOrChildSelected` also explicitly mention `TDB_StreamIDPath` in decorated signatures.

A separate executable-section direct-reference scan of *both* binary versions found 7/8 direct references to `AppendSyntheticIndex` (2025/2026), 2/2 to `GetStreamIDPath`, 2/2 to `IsPathOrChildSelected` and 3/4 to `C_AGMDLTranslatePort::LayerSelectSetupPrePlayback`. This strengthens the conclusion beyond exported declarations: these routines are referred to by direct instructions in the installed runtime. It does **not** independently verify when they execute, their role in native Pen-tool editing or third-party ability to supply selectable geometry.

The `AEGP_StreamSuite6::AEGP_GetUniqueStreamID` is public and session-unique; mapping to private `TDB_StreamIDPath` remains open. A pointer to `PF_World` in an AGM display-list translation constructor indicates a pixel output bridge and must not be construed as a geometry-return API.

**2026-10-11 extension:** F-VECTOR-016 directly locates `OriginInfo::AppendSyntheticIndex` calls **inside both native Repeater operator implementations** (not just anonymous xrefs), alongside native `SymbolGroup` construction and `SetOriginInfo`. These calls narrow the original finding but do not prove editable selection of synthetic copies.

Raw provenance: `datasets/ae-vector-origin-identity-2025-2026.json` and `datasets/ae-vector-selection-origin-xrefs-2025-2026.json`. For the mechanistic program and falsification see `docs/vector-shape-system/native-edit-and-provenance-bridge.md`.
