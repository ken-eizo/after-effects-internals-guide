---
status: architecture-reference
last_verified: 2026-10-14
evidence: E0-G + E0-H + E0-S + E2-L + E2-X + H
versions: SDK25.6 (exact installed public headers), AE2025 / AE2026 private Windows binaries
---

# Public and Internal Native Property API Atlas

This reference is organized by **operation and named type**, following the After Effects C++ SDK Guide's conventions. Functions, structures and suite names appear in code style. Public SDK APIs and private reverse-engineered exports are never presented as one uniform support surface.

**Authoritative public baseline:** [Adobe AEGP Suites](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/) and the installed `E:/ae25.6_61.64bit.AfterEffectsSDK/Examples/Headers/AE_GeneralPlug.h`. Some current online SDK pages document suites introduced *after* the installed 25.6 header; do not automatically ascribe their version to the local header.

## AEGP_GetStreamType and temporal value APIs

| Symbol | Public suite | Operation | Important precondition |
| --- | --- | --- | --- |
| `AEGP_GetStreamType` | `AEGP_StreamSuite6` | Determine exposed value type | Native `NO_DATA` may still contain private editable value |
| `AEGP_GetNewStreamValue` | `AEGP_StreamSuite6` | Retrieve value at given time | Valid type, correct pre-/post-expression flag, dispose value |
| `AEGP_CanVaryOverTime` | `AEGP_StreamSuite6` | Determine whether animation is permitted | Not the same as currently animated |
| `AEGP_IsStreamTimevarying` | `AEGP_StreamSuite6` | Determine if current effective state varies | Not equivalent to keyframe count |
| `AEGP_GetUniqueStreamID` | `AEGP_StreamSuite6` | Obtain session-unique stream number | Not persistent across AE sessions |
| `AEGP_GetStreamNumKFs` | Keyframe/Stream operation | Count keyframes on a valid eligible leaf | Must not call on arbitrary `NO_DATA` |

The exact suite names above reflect the installed SDK25.6 declarations or the source investigation. Confirm names/signatures in that header before compiling; API names/returns vary by suite version.

For the full parameter table, use [Adobe's AEGP Stream Suite](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/#stream-suite). This AEIG page focuses on observed internal semantics, not a verbatim copy of Adobe documentation.

## AEGP_DynamicStreamSuite4 — structural operations

| Symbol | Purpose | Host ownership / constraints |
| --- | --- | --- |
| `AEGP_GetStreamGroupingType` | Determine Leaf vs Named vs Indexed | Required before group enumeration |
| `AEGP_GetNumStreamsInGroup` | Child count | Group only; leaf precondition matters |
| `AEGP_GetNewStreamRefByIndex` | Child by index | Indices may change on edits |
| `AEGP_GetMatchName` | Semantic child class ID | Not a unique instance ID |
| `AEGP_CanAddStream` | Check parent admission | **Does not** prove a Creator is registered |
| `AEGP_AddStream` | Add an accepted existing native type | Indexed parent only; undoable |
| `AEGP_ReorderStream` | Change indexed order | Reacquire stale refs afterward |
| `AEGP_DuplicateStream` | Duplicate a native child | Preserve host disposal/owner conventions |
| `AEGP_DeleteStream` | Remove native child | Old references may invalidate |

This suite is public and intended for manipulation of **already supported/registered** host streams. Adobe's Streamie sample is a first-party example for Paint Strokes. It is **not a type provider**.

### The negative API boundary

A scoped audit of **70** installed SDK25.6 `.h/.hpp` files found:
- `AEGP_RegisterSuite5`: **12** public registration functions, none a native `TDB_StreamBase` class/parent-layout provider.
- `AEGP_DynamicStreamSuite4`: **26** functions, which operate on existing Streams.
- `AEGP_CreateVectorLayerInComp`: creates existing **Adobe Shape Layer**, not a foreign BEE Layer kind.
- No public `TDB_StreamFactory`, `TDB_ScRegisterStreams`, `BEE_Layer` or arbitrary native C++ Stream/Group registration declaration in that inspected SDK corpus.

This is a **bounded observation**; it does not establish nonexistence in a private Adobe partner SDK or a future version. See F-VECTOR-072/088.

## Internal TDB API — observed implementation, not public SDK

| Internal C++ symbol | Module | Responsibility | Verification |
| --- | --- | --- | --- |
| `TDB_MatchName` | `TDB.dll` | Type-key object with native comparison | F-VECTOR-065/093 |
| `Get_AE_StreamFactory` | `TDB.dll` | Native singleton-style factory getter | F-VECTOR-010/093 |
| `TDB_StreamFactory::RegisterFactoryFunc` | `TDB.dll` | Creator registry, eager canonical object, group setup | F-VECTOR-095 |
| `TDB_StreamFactory::CreateStream` | `TDB.dll` | Invoke native creator | F-VECTOR-095 |
| `TDB_StreamFactory::GetCanonicalInstance` | `TDB.dll` | Locate registered native prototype | F-VECTOR-084 |
| `TDB_StreamFactory::UnregisterFactoryFunc` | `TDB.dll` | Remove prototype/callback and destroy owned prototype | F-VECTOR-096 |
| `TDB_ScRegisterStreams::Register` | `TDB.dll` | Scoped first-party registration wrapper | F-VECTOR-080/093 |
| `TDB_ScRegisterStreams::UnregisterAll` | `TDB.dll` | Scoped teardown | F-VECTOR-093 |
| `TDB_StreamBase::SetupCanonicalLayout` | `TDB.dll` | Empty base default | F-VECTOR-095 |
| `TDB_StreamGroup::SetupCanonicalLayout` | `TDB.dll` | Canonical group construction and UILayout | F-VECTOR-095 |
| `TDB_StreamGroup::CanStore` | `TDB.dll` | Default allowable canonical children | F-VECTOR-084 |
| `TDB_StreamIDPath` | Native TDB/BEE | Hierarchical property path | AEIG state-model, E2-L |

These private C++ methods have reverse-engineered callsite/vtable evidence in **installed AE Windows builds**. Names and export presence do not imply third-party supported ABI stability.

## First-party implementations of native property classes

| Module/class | Kind | Relevant methods |
| --- | --- | --- |
| `OM.dll : OM_Stream` | Native Mask Path leaf | `Create`, `Read`, `Write`, `CloneStream`, `SetValue`, `GetValueEx` |
| `FLT.dll : FLT_Mask / FLT_MasksParade` | Native effect/mask Stream groups | `Create` and scoped TDB registration |
| `BEE.dll : BEE_PaintAtom` | Native brush stroke node | `Create`, `FillInCanonicalUILayout`, archive/clone |
| `BEE.dll : BEE_TextAnimatorStreamGroup` | Text Animator group | `FillInCanonicalUILayout` |
| `BEE.dll : BEE_VectorStream::VectorsStreamGroup` | Shape Contents indexed group | `FillInCanonicalUILayout`, custom `CanStore` |
| `BEE.dll : BEE_VectorLayer` | Shape Layer owner | `RegisterStreams`, vector evaluation and rasterization |

An actual third-party AEX has not been shown to create any of these *new* native types; the types listed above are Adobe-owned and pre-registered.

## API support status labels

Use these labels when navigating AEIG:

- **Supported public contract**: found in Adobe Guide, distributed current headers or Adobe samples (E0-G/H/S); use documented versions/contexts only.
- **Native private implementation**: independently inspected in installed binaries (E2-L); do not link/invoke as third-party SDK.
- **Host observation**: controlled real AE fixture (E2-X); facts scoped to tested build/project/session.
- **Hypothesis / extension frontier**: source symbols suggest a path but untested third-party registration or unexplained behavior remains.

Do not turn the two rows of methods into one copyable C++ header or pretend a private C++ export is automatically a partner SDK.

## Further references

[Streams and Properties](../streams-properties.md), [Canonical Groups](canonical-groups-admission.md), [Factory Registration](factory-registration-lifetime.md), [Property Operations](property-operations.md), [Official Adobe AEGP Suites](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/). Evidence: F-VECTOR-080–096, SDK25.6 header audit F-VECTOR-088.
