# EXP-SHAPE-097 — Native TDB CreateStream and Indexed Group InsertStream

**PASS — 2025/2026 Windows original Adobe TDB.dll static x64 disassembly; zero private host API calls.**

## Verified

- `TDB_StreamFactory::CreateStream`: Creator lookup under RecursiveMutex, callback copy, **unlock before copied std::function invocation**.
- Returned instance optionally calls `GetAsLeaf → InsertDefaultKey → SetConstant` and global `TDB_ShouldAlwaysDecanonicalize → GetAsGroup → TDB_DecanonicalizeAllChildStreamsDeep` (branch-dependent).
- `TDB_IndexedStreamGroup::InsertStream`: parent `CanStore` gate before indexed mutation, count checks, reverse-index update, path-cache reset, incoming pointer ownership transfer, native `SetParent`.
- **AE2026 private ABI divergence:** `InsertStream(index,child,InsertStreamOptions&)` at virtual offset +0x210 and simple wrapper at +0x218; simple method is at +0x210 in AE2025.

Machine-readable callsite evidence: `datasets/ae-tdb-document-instance-create-insert-load-2025-2026.json`. Read-only deterministic verifier: `experiments/vector-shape/probe-src/tools/verify_tdb_document_instance_create_insert_load.py` (SHA-256 pins both original source DLLs).

**Remaining:** No third-party Creator registered, no native CNL Timeline child inserted, no safe teardown/Undo/export demonstrated. See F-VECTOR-097 and feature pages `stream-instance-creation.md`, `indexed-group-insertion.md`.
