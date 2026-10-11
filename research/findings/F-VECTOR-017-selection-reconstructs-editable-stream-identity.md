---
status: strongly-supported-static
last_verified: 2026-10-11
evidence: E2-L + H
versions: installed AE2025 and AE2026 BEE.dll + TDB.dll
---
# F-VECTOR-017 — Native vector selection resolves editable/canonical host streams from hierarchical identity

## What is confirmed

AE's generic BEE_StreamSpec takes a BEE_Layer pointer and a TDB_StreamIDPath. BEE_Selection::SelectStream(BEE_StreamSpec*, bool) has 20 direct native callsites in each installed BEE version; BEE_SelectGroup(BEE_Layer*, TDB_StreamIDPath const&, ...) also calls SelectStream. These symbols belong to a general BEE layer/stream selection substrate, not solely native shapes.

Two native functions which directly call BEE_SelLayer::IsPathOrChildSelected have been disassembled in each version. Their actual x64 .pdata-bounded code invokes:

- TDB_StreamIDPath::GetLength, GetComponent, GetTail, AddHead, AddTail, RemoveTail, and stream-ID matchname comparisons.
- BEE_VectorStream::IsGroup and TDB_StreamBase::GetCanonicalStream.
- BEE_Selection::IsLayerSelected, GetSelLayer and BEE_SelLayer::IsPathOrChildSelected.
- Crucially, TDB_StreamGroup::FindEditableStream in the same second function.

| Function with selection/identity processing | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| Hierarchical group and selection normalization | 0x6665e0–0x666863 | 0x681e30–0x6820b3 |
| Path/child selection and editable source resolution | 0x6727f0–0x672bf9 | 0x68e700–0x68eae8 |

In AE2026 the second region calls IsPathOrChildSelected at RVA 0x68e8a1, FindEditableStream at 0x68ea08 and GetCanonicalStream at 0x68ea8d. This is strong static evidence that native shape-selection-related logic resolves authored editable source streams, not merely geometric point highlighting. It is not proof these calls always execute in that order.

## Boundaries

No in-host Pen-tool test has shown external editable geometry. We have not connected evaluated BEE_VectorArt::OriginInfo dataflow all the way into native hit-test -> draggable vertex handles. The BEE_GetSelectedShapePathsVec export has no direct BEE-internal CALLs in the scanned versions, which **does not** establish it is unused. Selected exports may be called indirectly, from other modules, or dynamically.

A top-level import-table audit of 443 installed AE2026 DLL/EXE/AEX modules found no *statically named* imports for the selected vector editing entrypoints. This is not a disproof of host usage; only a scoped negative import result.

## Practical product opportunity (hypothesis)

If an independent effect could own authentic persistent TDB streams with real BEE_StreamSpec identities and be accepted by the selection subsystem, its property selection could potentially use the native Timeline instead of a custom fake hierarchy. Native Pen vertex editing remains a different proof gate. A fabricated IDPath without ownership and editable stream lookup would not satisfy this.

## Reproducibility

Datasets: ae-native-vector-editor-owner-export-frontier-2025-2026.json, ae-native-vector-selection-hit-test-callgraph-2025-2026.json, ae-native-vector-selection-origin-consumers-2025-2026.json and ae-native-vector-cross-module-imports-2026.json (all in datasets/). Source-only scripts: audit_vector_editor_owner_exports.py, trace_native_vector_selection_hit_test.py, audit_selection_origin_consumers.py and audit_vector_crossmodule_imports.py (under experiments/vector-shape/probe-src/tools/).
