# EXP-SHAPE-095 — Adobe Native Type Registry → Canonical Group → Shape Contents, virtual call chain

**Status: PASS static, AE2025 and AE2026 exact installed native binaries.** This is not a new ChapeLayer host-native property created by an AEX.

## Discovery

The native `TDB_StreamFactory::RegisterFactoryFunc` eagerly constructs a prototype using `CreateStream`. That prototype is subjected to real virtual `IsLeaf`, `GetAsLeaf`, `IsSeparationLeader` and conditional `SetupCanonicalLayout` calls **during registration** — not only when the user later adds a stream to a project.

For native group-derived classes, `TDB_StreamGroup::SetupCanonicalLayout` dispatches virtual `FillInCanonicalUILayout` at vtable offset `0x1C8`. Real Shape Contents and Root Vectors vtables override that same slot with exported BEE methods, while the native `TDB_StreamBase::SetupCanonicalLayout` default is only `ret 0` (a no-op). After filling canonical children, the group routine invokes `SetupCanonicalLayoutForSeperatedDimensions` and `TDB_StreamGroup::SetUILayout` in that instruction order.

This is a direct native bridge from the factory registry to Adobe's native Shape hierarchy, **not** a separate Drawbot or pseudo-effect UI. The original OM Mask Path example independently corroborates the cross-DLL vtable ABI: its group/layout-relevant inherited virtual slots are imported `TDB.dll` JMP thunks, and `IsSeparationLeader` is an OM-specific override.

## Reproduction

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_tdb_eager_canonical_vtable_dispatch.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_tdb_group_bee_contents_canonical_dispatch.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_om_native_vtable_tdb_dispatch_bridge.py"
```

Machine-readable original-DLL SHA hashes, parent/child vtable slots and exact CALL sites:
- `datasets/ae-tdb-eager-canonical-vtable-2025-2026.json`
- `datasets/ae-tdb-group-to-bee-shape-canonical-dispatch-2025-2026.json`
- `datasets/ae-om-native-vtable-to-tdb-dispatch-2025-2026.json`

## Boundary

The attached reusable `CNLPrivateTDBDisposable.aex` **has not been run**. It only attempts a new key with a borrowed Adobe ParamPath *leaf* creator and does not define a group subclass. Even a successful disposable test would not demonstrate the requested new native parent/group, real Timeline editability, undo/save/render or stability. New stream creation needs compatible native C++ class inheritance, canonical group child grammar and host-scoped lifetime beyond passing `TDB_StreamFactory::RegisterFactoryFunc`.

Full report: `research/findings/F-VECTOR-095-native-tdb-registration-eager-canonical-shape-group-dispatch.md`.
