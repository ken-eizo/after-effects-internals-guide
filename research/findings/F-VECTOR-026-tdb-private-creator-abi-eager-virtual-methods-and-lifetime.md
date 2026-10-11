---
status: strongly-supported-static
last_verified: 2026-10-12
evidence: E2-L + H
versions: installed AE2025 / AE2026 TDB.dll, x64
---

# F-VECTOR-026 — Native TDB Creator: erased callback ABI, eager virtual methods, lifetime and unregistration

## Research objective

Implement an independently owned, editable host-native vector type, without creating normal Masks or Shape Layers or returning PF_World pixels. This finding reconstructs the internals of Adobe's TDB native stream type registry, one necessary contract for the goal. It does NOT implement or prove a third-party registration or native BEE VectorArt integration.

## Verified native function-object behavior in BOTH AE2025 and AE2026

The C++ exported registration methods use an MSVC std::function-based creator, not a plain C callback. Native code demonstrates:

1. RegisterFactoryFunc invokes virtual slot 0 to clone/copy the erased std::function into its internal map and virtual slot +0x20 to destroy its temporary callable.
2. It synchronously calls CreateStream for the newly registered MatchName before RegisterFactoryFunc returns. This means an incomplete stream class fails potentially while still registering.
3. CreateStream resolves and copies the callable, releases its own map lookup lock, and invokes the erased std::function through virtual slot +0x10 with native MatchName/factory/configuration parameters.
4. RegisterFactoryFunc invokes virtual methods on the newly created TDB_StreamBase to categorize its type and register canonical/separated dimensions. This is not merely storing a name.
5. Creator and canonical instance maps are separate. Successful MatchName admissibility is not synonymous with an actual live native stream.

Raw decorated C++ signatures are part of the captured binary export metadata. The complete semantic meaning of all creator parameters and internal object layout is not yet an externally safe C++ ABI.

## Native virtual methods mapped by their actual vtable pointer targets

Actual exported TDB_StreamBase and TDB_Stream native vftables were decoded and target addresses were matched against exported C++ methods in both binaries:

| Vtable byte offset | Base class / Stream class virtual | Native role |
| --- | --- | --- |
| +0x58 | IsLeaf | distinguish a leaf stream |
| +0x80 | GetAsLeaf | retrieve a leaf object when available |
| +0x90 | GetAsGroup | identify a group object |
| +0x150 | SetupCanonicalLayout | initialize native canonical layout |
| +0x298 | TDB_Stream leaf: IsSeparationLeader | separated-dimensions eligibility |

IMPORTANT: the last +0x298 offset is valid for the TDB_Stream leaf vtable. It is not a safe generic offset for TDB_StreamBase or all group-derived vtables. TDB_StreamGroup overrides +0x150 with its own SetupCanonicalLayout. The factory registration code calls +0x58 and +0x80 on the created base and +0x298 on the retrieved leaf when appropriate; conditional +0x150 setup is also observed. The exact x64 callsite evidence is stored in the local source analysis.

## Newly identified cleanup trap: destructor does not unregister

- TDB_ScRegisterStreams::Register forwards to TDB_StreamFactory::RegisterFactoryFunc; on success it records MatchNames in its own contiguous vector.
- TDB_ScRegisterStreams::UnregisterAll walks those names backwards in 16-byte steps and invokes UnregisterFactoryFunc for each.
- The independently disassembled TDB_ScRegisterStreams destructor does NOT call UnregisterAll. It frees its vector allocation, without automatically deregistering registered types.
- UnregisterFactoryFunc_NullOK removes entries from the factory map and canonical map, unlocks the registry lock, then makes a native virtual destruction call on the removed native stream object.
- The distinct TDB_StreamFactory destructor itself performs additional map and separation-data cleanup. This does not prove no project-owned Stream instances survive when a plugin unloads.

A plugin must NOT assume ordinary RAII destruction of the helper deregisters its native type. The callbacks are C++ erased objects retained by a host-owned registry, so premature module unload would risk dangling code pointers and virtual methods. Full RefCounted/allocator ABI, project lifetime, Undo, saved-instance and shutdown constraints remain unknown.

## Native factories vs full independent vector system

Even a registered native Stream type would not prove an independent Contents owner. At least four additional contracts remain unproven: persistent host object/Timeline owner, native Pen and Selection edit identity, BEE's *separate* MatchName-to-Operator evaluator registry, and native Layer Rasterize2DGraph/VectorArt render dispatch. F-VECTOR-025 independently proves production Shape renderer dispatch is a native BEE_VectorLayer virtual override, not a PF_Render selector.

## Reproducible evidence

- ae-native-stream-private-registration-lifetime-2025-2026.json: concise two-build callback/cleanup machine-code receipts.
- ae-tdb-stream-vtable-creator-required-methods-2025-2026.json: exact exported method RVAs in both native TDB stream class vtables.
- ae-native-registration-required-methods-crosscheck-2025-2026.json: independent machine-code/virtual method consistency checks.
- experiments/vector-shape/probe-src/tools/audit_tdb_external_registration_lifetime_contract.py.
- experiments/vector-shape/probe-src/tools/audit_tdb_stream_eager_vtable_methods.py.
- experiments/vector-shape/probe-src/tools/verify_tdb_external_creator_abi_crosscheck.py.
- F-VECTOR-013: earlier evidence for eager stream creation.
- F-VECTOR-014 and F-VECTOR-025: separate BEE vector evaluator and renderer/owner contracts.

This is E2-L evidence from exact installed TDB DLLs; it is NOT proof that a third party may register custom streams. No private host functions were executed. No AEX was installed or host GUI used.

## Large product frontier

If we can implement a complete and legal plugin-controlled native type and attach it to a new Timeline editor/render owner, CompNodeAE might emit its own true host-native persistent vector values. Procedural path/geometry types, user-written CNL vector operators, 2D/3D path hierarchies, AE Pen selection and native vector evaluation could become new plugin-authored AE functionality. That possibility remains speculative until all owner/editor/evaluator/render gates pass.
