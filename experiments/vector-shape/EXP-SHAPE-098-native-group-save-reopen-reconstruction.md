# EXP-SHAPE-098 — Native TDB group Write/Read and Stream Creator-dependent archive reconstruction

**PASS — 2025/2026 original Adobe TDB.dll offline, x64 instruction and native vtable corroboration.**

## Verified

- `TDB_StreamGroup::Write`: native UniqueStreamID, canonical Stream lookup, child MatchName, end-of-group marker.
- `TDB_StreamGroup::Read`: reads per-child `TDB_MatchName` from an SLU descendant list and dispatches virtual `ReadAndStore` at +0x1B8.
- `TDB_IndexedStreamGroup::ReadAndStore`: *CreateStream(saved MatchName) → GetNumStreams → virtual InsertStream → child virtual Read*, with a checked null-Creator-result branch.
- `TDB_NamedStreamGroup::ReadAndStore`: also calls CreateStream and has native paths for named child lookup, `EnsureUILayoutComplete` and `UpgradeChildStream`.
- Native loader virtual `InsertStream` uses +0x210 in AE2025 but +0x218 in AE2026, matching the private ABI change from EXP-SHAPE-097.

Independent static verifier: `experiments/vector-shape/probe-src/tools/verify_tdb_document_instance_create_insert_load.py`. Pinned digest/callsites: `datasets/ae-tdb-document-instance-create-insert-load-2025-2026.json`.

**Limits:** No actual AEP with a foreign type was written/opened; failure recovery for missing or invalid Creator is **unknown**. No Adobe binaries or user projects were modified. See F-VECTOR-098 and feature page `document-stream-serialization.md`.
