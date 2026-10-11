---
status: observed-static-only
last_verified: 2026-10-11
evidence: E2-L
versions: AE2025 / AE2026 BEE.dll and TDB.dll
---
# EXP-SHAPE-017 — BEE shape selection resolves persistent editable StreamIDPaths

**Question:** Are native selection structures tied to an authentic editable property path, not only geometry overlays?

**Method:** Enumerate BEE selection/stream exports, then scan BEE2025/BEE2026 executable CALL/JMP sites with Capstone's bounded-memory disassembly. Resolve exact caller .pdata spans for IsPathOrChildSelected and compare direct calls to TDB IDPath, GetCanonicalStream and FindEditableStream inside the same functions. This was static-only and never invoked a private function from the running AE.

**Result:** Generic BEE_Selection::SelectStream(BEE_StreamSpec*, bool) has 20 direct callers in both binaries. Two native functions in each version call IsPathOrChildSelected, manipulate TDB_StreamIDPath components, use BEE_VectorStream::IsGroup and GetCanonicalStream, and in the second function call TDB_StreamGroup::FindEditableStream. Version-specific RVAs are listed in F-VECTOR-017. The absence of a direct BEE-local CALL to GetSelectedShapePathsVec and BEE_CompHitCheckSelection does not establish non-use.

**Product opportunity:** An independent effect-hosted native Contents owner might reuse generic host selection IF it produces authentic BEE_Layer/StreamSpec/IDPath, passes FindEditableStream and survives Undo/reopen. Native Pen vertex editing remains **unproven**.

**Datasets:** ae-native-vector-editor-owner-export-frontier-2025-2026.json, ae-native-vector-selection-hit-test-callgraph-2025-2026.json, ae-native-vector-selection-origin-consumers-2025-2026.json. A cross-module import scan of 443 AE26 modules is separately recorded in ae-native-vector-cross-module-imports-2026.json and found no static named imports of selected entrypoints. It cannot resolve dynamic lookups/indirect calls.
