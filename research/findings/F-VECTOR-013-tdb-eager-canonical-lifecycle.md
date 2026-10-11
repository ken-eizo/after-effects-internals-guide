---
status: strongly-supported-static
last_verified: 2026-10-11
evidence: E2-L; no private registration executed in host
versions: AE2025/AE2026 TDB.dll
---
# F-VECTOR-013 — Native creator registration eagerly constructs a TDB Stream and canonical derivatives

## Claim

`TDB_StreamFactory::RegisterFactoryFunc` is **not just a passive registration table insertion**. The native code locks a `dvacore::RecursiveMutex`, checks for a duplicate match-name key, inserts the creator, then synchronously calls `TDB_StreamFactory::CreateStream` for that name before the registration routine has returned.

AE2026 exact references:
- `TDB_ScRegisterStreams::Register` at RVA `0x28220` calls `RegisterFactoryFunc` at `0x2828d`.
- `TDB_StreamFactory::RegisterFactoryFunc` at RVA `0x285d0` calls `CreateStream` at `0x2874b`, and `RegisterSeparatedDimensions` at `0x287bb` on the constructed stream if the tested virtual predicates succeed.
- `CreateStream` at RVA `0x27920` resolves a match name and invokes its registered creator through a C++ function-object virtual call at `0x27a50` (`call [rax+0x10]`), then invokes additional virtual methods on the created `TDB_StreamBase`/derived object.
- `RegisterSeparatedDimensions` at RVA `0x289c0` may call `RegisterCanonicalInstance` at `0x291c4`.
- `TDB_ScRegisterStreams::UnregisterAll` calls `UnregisterFactoryFunc`; duplicate registration and ownership also have explicit branches.

AE2025 independently confirms the same ordered call edges at RVAs `0x270be`, `0x2757f`, `0x275ef`, `0x280ba`, `0x287da`.

## Implications

A plugin attempting to register a new type must already have a **complete, valid stream object and callable C++ ABI before registration begins**: a native compatible `TDB_MatchName`, `std::function` callback, allocator, virtual methods, destructor, type identity, canonical prototype and proper ownership. A dummy callback which just returns a pointer or null may cause synchronous host assertions or memory corruption **during registration**.

The factory's mutex means re-entrant behavior is possible, but this does not authorize registering from arbitrary threads or unloading plugin callback code while a host-owned type instance survives. Returning a non-null `Get_AE_StreamFactory` pointer from user-executed AEGP remains **read-only E2-X** and does not demonstrate ability to call any method on it.

## Falsification barriers

Before a disposable AE host experiment, reconstruct layout, callback signature, allocation/destruction, canonical assignment and rollback; then test clean startup/Undo/Save/Reopen/version changes separately. No private method is invoked by the current ShapeLayerAE v3 except the pinned no-argument getter.

## Reproducible raw evidence

`datasets/ae-tdb-factory-lifetime-canonical-controlflow-2025-2026.json` and `experiments/vector-shape/probe-src/tools/audit_tdb_factory_lifetime.py`. All reverse-engineering is static from locally installed Adobe binaries; no binary redistributed.
