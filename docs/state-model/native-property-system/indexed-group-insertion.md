---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E0-H + E2-L + E2-X
versions: Windows AE2025 / AE2026; SDK25.6 AEGP DynamicStreamSuite4
---

# TDB_IndexedStreamGroup::InsertStream — Native Child Adoption

`TDB_IndexedStreamGroup::InsertStream` attaches a newly created `TDB_StreamBase` to an **ordered native parent Stream group**. This is the core Adobe-owned structural operation behind a group that contains ordered repeatable child properties. It is not the same as the supported AEGP `AEGP_AddStream` API, although the public API can eventually request insertion of existing Adobe-owned types.

## Required conditions

A native child cannot be inserted merely because its MatchName has a corresponding Creator. Three independent conditions must be distinguished:

| Stage | Native source of authority | Observed behavior |
| --- | --- | --- |
| Constructability | `TDB_StreamFactory::CreateStream` | Construct a concrete registered C++ Stream |
| Parent policy | Virtual `CanStore` (vtable `+0x1C0`) | Parent can refuse that specific MatchName |
| Actual host ownership | `InsertStream` and `SetParent` | Index bookkeeping and parent relationship must be updated |

A public `AEGP_CanAddStream` returns a **preflight result** for a parent; it is not a replacement for constructing a child and attaching it through native host operations. A successful factory registration alone does not override the Paint/Text/Shape parent's CanStore policy.

## Native insertion algorithm

```text
IndexedStreamGroup::InsertStream(index, U_ScAutoPtr<TDB_StreamBase> child, options)
  ├─ virtual CanStore(child.MatchName) [vtable +0x1C0]
  ├─ if false: take native failure/error branch
  ├─ virtual GetNumStreams() [vtable +0x168]
  ├─ verify 0 <= insert index <= current stream count
  ├─ splice native child into indexed storage
  ├─ UpdateReverseIndexVector(index)
  ├─ ResetCachedCapsulePathsFromIndex(index) [subject to options in AE2026]
  ├─ relinquish caller U_ScAutoPtr ownership
  ├─ TDB_StreamBase::SetParent(this)
  └─ additional internal notification/event helper
```

The C++ signature above is a **conceptual representation** of recovered exports, not a supported header. The order of the native exported and virtual calls is verified, but internal helper parameters and all error cleanup branches are not.

### CanStore is called before the indexed list changes

In both installed versions, the first relevant virtual call is **`+0x1C0`** (the `CanStore` method for the verified real `TDB_IndexedStreamGroup` vtable). If it returns false, control transfers out of the normal insertion path before the group count or vector is mutated.

This matters for user-defined Shape/Paint/Text Stream types: a valid class Creator does not make an Adobe-owned parent permissive. Paint Strokes uses a strict canonical `ADBE Paint Atom` policy, while Shape Contents has an Adobe Vector Group exact-MatchName condition and three Shape/Graphic/Filter prefixes. See [Canonical Groups](canonical-groups-admission.md).

### Index bookkeeping and StreamIDPath

Successful insertion updates **`UpdateReverseIndexVector`** and resets affected **cached capsule paths** through `ResetCachedCapsulePathsFromIndex`, followed by **`SetParent`**. `SetParent` itself is separately observed to invoke `NotifyParentsStreamStored` and `TDB_RescaleStream` under conditions.

An indexed child's group position and its cached `TDB_StreamIDPath` references are therefore not passive metadata: child insertion participates in host bookkeeping and can invalidate addresses. Do not retain stale dynamic child references across insertion/reorder/delete.

## A significant AE 2025 / AE 2026 private ABI change

| API or callsite | AE2025 | AE2026 |
| --- | --- | --- |
| Full native `InsertStream` RVA | `0x3BB30` | `0x3C6A0` |
| `CanStore` virtual call | `0x3BB6D` | `0x3C6E5` |
| `GetNumStreams` virtual call | `0x3BB81` | `0x3C6F9` |
| `UpdateReverseIndexVector` call | `0x3BCF8` | `0x3C860` |
| `ResetCachedCapsulePathsFromIndex` call | `0x3BD03` | `0x3C872` |
| `SetParent` call | `0x3BD18` | `0x3C885` |
| Virtual entry for simple `InsertStream(index,child)` | `+0x210` | `+0x218` |
| Options-taking `InsertStream(index,child,Options&)` | Not seen | `+0x210` |
| Separate simple wrapper | Not seen | `0x3C680` |

This **private virtual ABI drift** is stronger than a mere changed address. In 2025, `+0x218` was `DuplicateStream`; in 2026, `+0x218` is the simple `InsertStream` wrapper. The options-taking version is used internally, and specific cache reset/ownership behavior changes with a flag. **Never copy a native vtable layout from AE2025 into AE2026**.

## What happens on project load

`TDB_IndexedStreamGroup::ReadAndStore` receives a saved child's MatchName, calls `TDB_StreamFactory::CreateStream`, then calls `GetNumStreams` and virtual `InsertStream`, and finally the child's virtual `Read`. This is the *same* parent admission and bookkeeping path, exercised during native project reconstruction. See [Document Stream Serialization](document-stream-serialization.md).

The exact archive failure behavior for an unknown type remains unverified. Inserting a new class that passes preflight but has no serialization contract does not establish a working .aep roundtrip.

## Public API counterpart

The supported public AEGP calls are `AEGP_CanAddStream`, `AEGP_AddStream`, `AEGP_DeleteStream`, `AEGP_ReorderStream`, and `AEGP_DuplicateStream` on an existing **indexed** group. These operations operate on registered native types; they do not register a new C++ group class.

See [AEGP_DynamicStreamSuite4](../../host-integration/cpp-sdk/aegps/dynamic-stream-suite.md) for signatures, UTF-8 MatchName and Undo/disposal rules.

## Evidence and unresolved requirements

Static original Windows AE2025/2026 `TDB.dll` imports, exports, the exact `TDB_IndexedStreamGroup` vtable and bounded machine-code calls were independently verified (F-VECTOR-097). The verifier stores source SHA and per-version RVA in `datasets/ae-tdb-document-instance-create-insert-load-2025-2026.json`.

**No external ChapeLayer Stream was inserted** into a live AE project. The native class provider, Timeline editor, AEP persistence, native rendering and safe unload remain separate gates.
