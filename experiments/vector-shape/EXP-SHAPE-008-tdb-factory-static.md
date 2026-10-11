---
status: observed-static-only
last_verified: 2026-10-11
evidence: E2-L + E2-X admissibility context
versions: AE2025 / AE2026 exact installed BEE.dll and TDB.dll
---
# EXP-SHAPE-008 — Native TDB factory, creator registration and child-admissibility predicates

## Offline procedure

With the exact locally installed AE2025/AE2026 binaries, run these independent scripts under `D:/Developer/ShapeLayerAE/tools`:
- `locate_tdb_library.py`, `probe_tdb_imports.py` — map BEE's TDB PE import ownership.
- `audit_tdb_factory.py` — enumerate factory, canonical instance, registration and group types by decorated PE export symbols.
- `trace_bee_tdb_iat.py` — Capstone+PE IAT decode of BEE_Layer::RegisterStreams.
- `trace_tdb_factory_semantics.py` — bounded disassembly of getter, scoped registration, RegisterFactoryFunc, CreateStream and UnregisterAll.
- `trace_vector_canstore.py`, `decode_canstore_constants.py` — compare shape group CanStore conditional and RIP literal strings.
- `scan_shape_factory_inventory.py` — compare BEE module-local registered type constructor surface.

All are non-executing static analysis of AE binaries; no host injection, no call into Adobe DLLs.

## Findings corroborated in two versions

`BEE_Layer::RegisterStreams(bool)` imports/calls `TDB.dll!Get_AE_StreamFactory()`, invokes `TDB_ScRegisterStreams::Register`, and has an unregister branch invoking `UnregisterAll`. TDB's `Register` calls `TDB_StreamFactory::RegisterFactoryFunc`. The latter acquires a `RecursiveMutex`, checks a match-name key, calls `CreateStream` and `RegisterSeparatedDimensions`. This is a real creator/prototype registration mechanism (for Adobe's own types), not just symbol-name folklore.

`BEE_VectorStream::VectorsStreamGroup::CanStore` contains literal prefixes:
`ADBE Vector Shape -`, `ADBE Vector Graphic -`, `ADBE Vector Filter -`, with string-search-like code. It is not yet proven that **unknown** prefixed types return CanAdd=true. Host E2-X so far tested only built-in candidates.

The external plugin test status is **none** for factory registration; no C++ plugin has created a native custom stream. An exported private method may still be subject to private layouts, registration lifecycle, serialization, and rendering/editing restrictions.

## Exact artifacts

- `datasets/ae-tdb-native-stream-factory-2025-2026.json` SHA256 `F5DCA8E3CB9332BEC03C961D57B39AB7EE1D695860498970EDB90DC2BF5CB11C`.
- `datasets/ae-tdb-register-callsite-disasm-2025-2026.json` SHA256 `E5696920D6EC84924BE461D544CADEEC3B2B374A88BC33335981D28C3530E8C5`.
- `datasets/ae-bee-registerstreams-iat-targets-2025-2026.json` SHA256 `F522653C78DF4F7ECE980B7BEEE629A593D3D1D47EDE19DEB78A50779E635FF9`.
- `datasets/ae-tdb-vector-canstore-disasm-2025-2026.json` SHA256 `BF078A17672DBE05B58FC664F32AAA969FDA5C6DFD269D403D9C2DAEA2B82242`.
- `datasets/ae-vector-canstore-prefix-literals-2025-2026.json` SHA256 `0E25914370FC94F6686519CDA0A0ACA2FC5EE9677DAF0A047582678F8983E4B4` (RIP literal references).

All captured dataset archives include exact module hashes and decorated symbols for reproducibility.
