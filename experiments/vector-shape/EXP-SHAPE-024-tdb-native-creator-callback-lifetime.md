---
status: pass-static-no-host-registration
last_verified: 2026-10-12
evidence: E2-L
versions: pinned installed AE2025 and AE2026 TDB.dll
---

# EXP-SHAPE-024 — Native TDB Creator callback and cleanup contract

## What would qualify as success

A new external plugin-defined native TDB Stream type must be registered, instantiated, cloned, saved, undone and unloaded correctly without creating a Mask or Shape Layer. A valid stream alone is not equivalent to independent native editable Contents or BEE VectorArt output. The first required step is to reconstruct the actual type-registration ABI and its lifetime obligations.

This experiment covers ONLY this ABI reconstruction and is intentionally offline.

## Input and tools

Read the two versions of TDB.dll already installed on the user's computer (2025, 2026) using PE export metadata, unwind/PData boundaries and capstone x64 instruction disassembly. No Adobe code is executed, no memory modifications or AEX installation occurs. Retain only scripts and compact evidence in AEIG, not the proprietary binaries.

Reproduce from the user's SDK/AE installation:

    python D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\audit_tdb_external_registration_lifetime_contract.py
    python D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\audit_tdb_stream_eager_vtable_methods.py
    python D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_tdb_external_creator_abi_crosscheck.py

## Results (both years)

- Native MSVC erased std::function clone via virtual +0, invoke via +0x10, delete/callable release via +0x20.
- Factory RegisterFactoryFunc synchronously invokes CreateStream, which calls through the type's erased creator. Registration is **eager** and immediately requires a valid native subclass.
- The factory tests TDB_StreamBase virtual IsLeaf (+0x58) and GetAsLeaf (+0x80), then TDB_Stream leaf IsSeparationLeader (+0x298); SetupCanonicalLayout (+0x150) is conditionally dispatched.
- TDB_ScRegisterStreams::Register records successful registrations; UnregisterAll explicitly walks registered names BACKWARD and unregisters each.
- The helper **destructor does not call UnregisterAll**; it only frees its vector storage. Never assume destructor is equivalent to unregistration.
- UnregisterFactoryFunc_NullOK removes creator and canonical registry entries and invokes a native virtual destruction on the removed object.
- Separate factory destructor and project-owned streams make unload and restart nontrivial.

The local cross-validation program PASSED for both AE2025 and AE2026. No third-party custom type was registered.

## Pass/fail evidence

| Condition | State |
| --- | --- |
| Private creator entrypoints/erased callback ABI located | PASS (static) |
| Synchronous newly-created Stream virtual method identities | PASS (static) |
| Reverse explicit deregistration, helper destructor non-deregistration | PASS (static) |
| Canonical/prototype lifetime safely externalized | NOT PROVEN |
| Third-party new TDB stream type installed in AE | NOT TESTED |
| Independent Effect/Layer owner with native indexed Contents | NOT TESTED |
| Native Pen/VectorArt/RG integration | NOT TESTED |

## Next experiment gates

1. Reconstruct native TDB_StreamBase clone, destructor, serialization, canonical stream and project ownership in addition to IsLeaf/GetAsLeaf.
2. Determine WHEN native layer startup registers all factory types, when UnregisterAll is called and whether an external plugin can legally register after global initialization.
3. Reconstruct the private BEE evaluator registry's own refcounted operator creation/deletion in a version-pinned, non-mutating test.
4. Only after full ABI and host-lifetime coverage: propose a gated, reversible registration experiment in an isolated AE copy at the user's initiative. Do not register dummy callbacks or call private exports from the active AE session.
5. Distinguish an external registered type under built-in Shape Contents from genuinely independent plugin-owned Contents. Only latter meets structural milestone.

## Source records

Research F-VECTOR-026 and compact datasets starting with ae-native-stream-private-registration-lifetime, ae-tdb-stream-vtable-creator-required-methods, and ae-native-registration-required-methods-crosscheck (2025-2026).
