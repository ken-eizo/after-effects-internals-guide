---
date: 2026-10-15
status: PASS offline strict original AE2025/2026 x64 native TDB instance creation, indexed insert and parent/cache ownership flow
evidence: E2-L SHA-pinned original TDB.dll PE exports, native vtables, direct and indirect x64 CALL graph; no private runtime calls
---
# F-VECTOR-097 — TDB CreateStream and Indexed Group InsertStream: from registered C++ Creator to a native child instance

## New distinction: canonical class registration versus document instance construction

F-VECTOR-095/096 proved that `RegisterFactoryFunc` stores a Creator and immediately builds a canonical prototype. Here the host's **subsequent** `TDB_StreamFactory::CreateStream` implementation is verified in both installed Windows versions, along with the concrete `TDB_IndexedStreamGroup::InsertStream` path that adopts a resulting child.

The factory lookup and actual Creator callback execute on **opposite sides of an explicit unlock**. This is more precise than describing the operation as a single under-lock factory call.

```text
TDB_StreamFactory::CreateStream(matchName, options)
  ├─ lock factory's RecursiveMutex
  ├─ search internal Creator map by TDB_MatchName
  ├─ take a local std::function callback copy
  ├─ unlock factory's RecursiveMutex          <-- before Creator invocation
  ├─ invoke copied std::function (vtable + 0x10)
  │    └─ produce a new TDB_StreamBase*
  ├─ call virtual GetAsLeaf (+0x80)
  │    └─ possibly InsertDefaultKey (leaf virtual +0x190)
  │         └─ possibly SetConstant
  └─ optionally, depending on call flags and host global:
       TDB_ShouldAlwaysDecanonicalize()
       -> virtual GetAsGroup (+0x90)
       -> TDB_DecanonicalizeAllChildStreamsDeep(...)
```

**Branch qualifiers:** the default-key, constant-value and deep-decanonicalization calls are conditional, not unconditional requirements for every leaf/group. We verified the precise source vtable slots using real exported `TDB_Stream` and `TDB_NamedStreamGroup` methods rather than assuming a slot name from its numeric offset. Some failure/error branches return null or take Adobe error reporting paths; this is *not* evidence that all invalid registrations fail safely.

| Real native callsite | AE 2025 `TDB.dll` RVA | AE 2026 RVA |
| --- | ---: | ---: |
| `CreateStream` function | `0x26710` | `0x27920` |
| Factory RecursiveMutex lock | `0x2677D` | `0x2798D` |
| Success-path unlock | `0x2688B` | `0x27A04` |
| Copied Creator invocation | `0x268D7` | `0x27A50` |
| `GetAsLeaf` dispatch | `0x26953` | `0x27ACC` |
| `InsertDefaultKey` dispatch | `0x26983` | `0x27AF5` |
| `SetConstant` | `0x26995` | `0x27B0B` |
| `TDB_ShouldAlwaysDecanonicalize` | `0x269A3` | `0x27B1D` |
| `GetAsGroup` dispatch | `0x269B2` | `0x27B2C` |
| `TDB_DecanonicalizeAllChildStreamsDeep` | `0x269C0` | `0x27B3A` |

### A new extension safety constraint

A C++ Creator is called **outside the map's RecursiveMutex after the callback has been copied**. The static code by itself does not establish safe concurrent unregistration, the life of copied callbacks when a foreign DLL is unloading or whether all host threads have quiesced. Therefore simply observing a successful `UnregisterFactoryFunc` return cannot certify a foreign implementation's safe unload. The earlier F-VECTOR-096 two-map teardown and this unlocked invocation window must be analyzed together.

## Native indexed child insertion: the next gate after a valid Creator

`TDB_IndexedStreamGroup::InsertStream` enforces the parent group's **virtual `CanStore` at slot +0x1C0** before admitting a constructed Stream. It then checks indexed bounds (`GetNumStreams` +`0x168`), performs the insertion, updates the reverse-index map, invalidates affected cached capsule paths and connects the child to its owning parent through `TDB_StreamBase::SetParent`.

```text
TDB_IndexedStreamGroup::InsertStream(index, child)
  ├─ virtual CanStore(child.MatchName)  [+0x1C0]
  │    └─ reject/error branch if not permitted
  ├─ virtual GetNumStreams()           [+0x168]
  │    └─ check insertion index
  ├─ apply indexed vector insertion / reverse-index bookkeeping
  ├─ UpdateReverseIndexVector(index)
  ├─ ResetCachedCapsulePathsFromIndex(index)
  ├─ transfer child away from incoming U_ScAutoPtr
  └─ TDB_StreamBase::SetParent(this)
       └─ parent notification and potential stream rescale (see EXP-SHAPE-025)
```

For the **2026 options overload**, resetting cached capsule paths is *conditional on options flags*; the above is the observed default/normal branch, not unconditional in all configurations. The subsequent unnamed helper/event call after parent assignment has not yet been given a verified semantic label.

| Call / virtual slot | AE2025 | AE2026 |
| --- | ---: | ---: |
| Full native indexed insertion entry | `0x3BB30` | `0x3C6A0` |
| Initial virtual `CanStore` | `0x3BB6D` | `0x3C6E5` |
| Get child count | `0x3BB81` | `0x3C6F9` |
| Reverse-index update | `0x3BCF8` | `0x3C860` |
| Capsule path-cache reset | `0x3BD03` | `0x3C872` |
| SetParent | `0x3BD18` | `0x3C885` |

### A specific private ABI change in AE2026

The **2025** `TDB_IndexedStreamGroup` vtable's `+0x210` method is `InsertStream(index, child)`.

The **2026** vtable has **two insert forms**:
- `+0x210`: `InsertStream(index, child, InsertStreamOptions&)`, new options-taking native method.
- `+0x218`: `InsertStream(index, child)` short wrapper, forwarding through the virtual `+0x210` method.

That `+0x218` vtable entry was a different operation (`DuplicateStream`) in the examined 2025 layout. This is an actual change in the **private C++ StreamGroup vtable layout**, not just a relocation. A binary extension copying a 2025 vtable is consequently unsafe in AE2026.

## Why this matters for fully native ChapeLayer

Successful registration, `CreateStream`, and `CanStore` are different milestones. Even a native object that passes the gate must be **adopted** into a real host-owned parent, have its parent and cached path metadata updated, and survive authoring/Undo/archive. A separately rendered CNL effect/panel/mock is not equivalent.

This experiment did **not** create a foreign native Stream or attach it to a live AE document. No unsupported TDB function was invoked. Real AE2025/26 binaries were read only.

## Strict reproduction and linked pages

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_tdb_document_instance_create_insert_load.py"
```

Receipt: `datasets/ae-tdb-document-instance-create-insert-load-2025-2026.json`.

AEIG feature pages: `docs/state-model/native-property-system/stream-instance-creation.md`, `indexed-group-insertion.md`. Parent policy: F-VECTOR-084/065. Factory canonical registration and ownership: F-VECTOR-095/096. Serialization reconstruction continues in F-VECTOR-098.
