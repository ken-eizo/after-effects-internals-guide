# EXP-SHAPE-094 — Exact OM native Stream object construction, allocator and teardown

**Status: PASS offline static, installed Windows After Effects 2025 + 2026.**

## What was proven

The C++ object behind the real Adobe `ADBE Mask Shape` native property is **not** an independent CNL model or a PF parameter. It is an actual `OM_Stream`, implemented by OM.dll and registered by OM_Birth through the native TDB factory.

Exact x64 compiled evidence:

- Native `OM_Stream::Create` uses `U.dll!U_MemTrackedObject::operator new(0x450)`, then calls the concrete `OM_Stream` constructor.
- Native `OM_Stream` constructor invokes `TDB_DerivedStream<OM_MaskShapeStreamTraits>` base constructor, installs the `OM_Stream` native vtable and initializes an object byte at offset `0x448`.
- Class allocation is 1104 bytes in **both** installed releases; *stable size alone does NOT prove a stable ABI*.
- OM_Birth allocates a 16-byte native MatchName object, constructs it from `ADBE Mask Shape`, and registers the exact object together with `OM_Stream::Create`.
- OM_Death calls `TDB_StreamFactory::UnregisterFactoryFunc`, **then** frees the original MatchName object using the native U.dll allocator and writes zero to the exported global pointer.
- Native class exports `CloneStream`, `Read`, `Write`, `GetValueEx`, `SetValue` and `CanHaveExpression` are present.

Exact code RVAs, U.dll import identities, typed base constructor, vtable and before/after order are in:
`datasets/ae-om-native-maskshape-stream-abi-and-teardown-2025-2026.json`.

## Verify

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\audit_om_native_stream_abi_and_teardown.py"
```

Expected `PASS 2/2`. No native Adobe code runs. Full note:
`research/findings/F-VECTOR-094-om-maskshape-native-cpp-stream-abi-and-teardown.md`.

**Product status unchanged** — this Adobe-internal native Stream implementation does **not** itself supply a supported external AEX registration API, editable unknown CNL group, save/reopen or editor integration. It is architectural source evidence for the next isolated test design, not a completed ChapeLayer plug-in.
