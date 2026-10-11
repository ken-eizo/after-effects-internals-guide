---
status: mixed-host-and-static-evidence
last_verified: 2026-10-11
evidence: E2-X + E2-L + E0-H + H
versions: AE 2026 host experiment, AE2025/26 BEE/TDB.dll
---
# F-VECTOR-009 — Native indexed-group admissibility and anomalous AEGP stream UID on AE2026

## Host-confirmed E2-X: specific parent/child capabilities

The user executed ShapeLayerAE v2 and generated the three TSV outputs. At capture time 2026-10-11 18:45:17 local, `AEGP_GetUniqueStreamID`, dynamic flags, StreamType and `AEGP_CanAddStream` were read against the **selected Shape Layer** with nested Shape Groups, Path, Fill, Stroke, and Effect Parade. All raw inputs are archived under `experiments/vector-shape/runs/EXP-SHAPE-005/20261011-user-host-v2`.

- 359 valid stream records, tree max depth 6; no nonzero recorded API error.
- 36 `AEGP_CanAddStream` queries; no query errors.
- `ADBE Root Vectors Group` and nested `ADBE Vectors Group`: allow native `ADBE Vector Group`, `ADBE Vector Shape - Group`, `ADBE Vector Shape - Rect`, `ADBE Vector Graphic - Fill`, `ADBE Vector Graphic - Stroke`, but reject `ADBE Slider Control`.
- `ADBE Effect Parade`: rejects those tested native vector types, allows `ADBE Slider Control`.
- `ADBE Mask Parade` and `ADBE Layer Sets`: reject all six tested names; this does not exhaust their accepted child types.

**Conclusion scope:** AEGP's indexed-group API delegates to heterogeneous parent-specific child admission. It does **not** mean that the Effect Parade can be converted to a vector Contents tree or that a plug-in can add arbitrary custom type definitions.

## Native CanStore assembly: a testable prefix hypothesis

The private class `BEE_VectorStream::VectorsStreamGroup::CanStore(TDB_MatchName const&)` exists in both BEE versions. Static x64 analysis shows calls to `TDB_MatchName::GetName`, followed by a string-search-looking helper whose return address is compared to the original name pointer. The local constant strings found in the exact binaries are:

- `ADBE Vector Shape -`
- `ADBE Vector Graphic -`
- `ADBE Vector Filter -`

A separate MatchName equality check also exists. These instructions are **consistent with a prefix-admission rule** for shape operators and graphics. The actual complete predicate and interaction with factory availability are not established from this single routine alone.

Strong falsification: an **unregistered** name such as `ADBE Vector Shape - ShapeLayerAEProbe` would be accepted by `CanAddStream` but still be non-creatable without `RegisterFactoryFunc`. This is deliberately separated into an optional read-only probe, because an actual `AEGP_AddStream` on an unknown MatchName may hit host assertions or project corruption.

## UID anomaly — 359 zero values despite successful calls

All 359 `AEGP_GetUniqueStreamID` calls produced `outID=0`; all 359 error fields were zero. The C++ observer initialized its `int32_t` output to `-1`, so this is a **host-written zero**, not simply leaving the initial buffer untouched. The program also captured 0 error codes for other queries and SDK depth matched traversal depth for every record.

This is an **unexpected host-specific observation**, not an established general bug in Adobe's API. Possible causes to test: stream ID namespace not initialized on that version/build/fixture, StreamSuite6 limitations, implementation defect, or a condition on the host's internal ID feature flag. AEIG already contains `F-STATE-005` about `EnableTDBStreamScriptingIDs`, and TDB exports `TDB_Project::TDB_AreTDBStreamScriptingIDsEnabled`; **no causation is established** between that feature flag and this result.

The next compiled probe initializes two different nonzero sentinel values and calls the UID suite twice to differentiate persistent 0, uninitialized output, and per-call differences. It must be tested in AE and on a second layer/host build before asserting a systemic defect.

## Provenance and status

- Full raw TSv hashes and summary: `experiments/vector-shape/runs/EXP-SHAPE-005/20261011-user-host-v2/analysis.json`.
- Native CanStore code: `datasets/ae-tdb-vector-canstore-disasm-2025-2026.json`; recovered ASCII constants with precise RVAs: `datasets/ae-vector-canstore-prefix-literals-2025-2026.json` (SHA256 `0E25914370FC94F6686519CDA0A0ACA2FC5EE9677DAF0A047582678F8983E4B4`).
- SHA-256 in experiment manifest and datasets. E2-L symbol names alone cannot establish runtime registration.
