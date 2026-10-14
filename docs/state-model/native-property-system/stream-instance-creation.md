---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E2-L + H
versions: Windows AE2025/AE2026; no public SDK equivalent
---

# TDB_StreamFactory::CreateStream — Native Instance Construction

`TDB_StreamFactory::CreateStream` constructs a **new C++ Stream instance** from a previously registered native type Creator. This method is distinct from `RegisterFactoryFunc`, which sets up type metadata and eagerly creates a canonical prototype. This is a **private Adobe C++ implementation reference**, not a supported third-party extension API.

## Purpose and declaration

The exported C++ symbol in the two installed versions is:

```cpp
// Conceptual name/signature reconstructed from private export only.
// Do not compile against this; arguments, flags, allocator and ABI are private.
TDB_StreamBase* TDB_StreamFactory::CreateStream(
    const TDB_MatchName& match_name,
    bool initial_state,
    unsigned int type_or_flags,
    bool behavior_flag_1,
    bool behavior_flag_2);
```

The names of the boolean and integer parameters above are *placeholders*, not recovered parameter semantics. The original decorated symbol is `?CreateStream@TDB_StreamFactory@@QEAAPEAVTDB_StreamBase@@AEBVTDB_MatchName@@_NI11@Z` in both versions. The exact behavior of every flag remains unknown.

## Native execution sequence

```text
1. Get the host's recursive StreamFactory mutex
2. Search the Creator table (factory +0x28) using TDB_MatchName
3. Copy the matching native std::function callback to temporary storage
4. Unlock the factory mutex
5. Invoke the copied Creator (indirect std::function dispatch)
6. On nonnull native TDB_StreamBase*:
     - virtual GetAsLeaf()
     - where applicable, virtual InsertDefaultKey(initial U_Time)
     - where applicable, TDB_Stream::SetConstant(...)
7. If allowed by flags + TDB_ShouldAlwaysDecanonicalize():
     - virtual GetAsGroup()
     - TDB_DecanonicalizeAllChildStreamsDeep(...)
8. Release the temporary copied std::function callback
9. Return the new Stream pointer
```

This is the observed success-path call graph, not proof of all error/unwind branches. Specifically, **Creator invocation takes place after the factory's explicit mutex unlock**. The callback is held locally, but the safety of registering/unregistering an independently loaded DLL concurrently with callback invocation is unproven.

## Type-dependent initialization

| Method | Native virtual slot | Applies to | Evidence |
| --- | ---: | --- | --- |
| `GetAsLeaf` | `0x80` | Leaf candidate | F-VECTOR-097; E2-L |
| `InsertDefaultKey` | `0x190` in `TDB_Stream`/derived leaf | Eligible leaf values | F-VECTOR-097; E2-L |
| `SetConstant` | Direct native TDB method | Conditional leaf behavior | F-VECTOR-097; E2-L |
| `GetAsGroup` | `0x90` | Group candidate | F-VECTOR-097; E2-L |
| `TDB_ShouldAlwaysDecanonicalize` | Exported host policy | Canonicalized graph behavior | F-VECTOR-097; E2-L |
| `TDB_DecanonicalizeAllChildStreamsDeep` | Exported host recursive helper | Conditional group subtree | F-VECTOR-097; E2-L |

**Canonical prototype vs instance:** the registered prototype has its own canonical group layout. `CreateStream` can conditionally alter the constructed object's default-key/constant status or de-canonicalize its child group state. A prototype in the registry must therefore not be assumed equivalent to an authored layer/document Stream instance.

## Important ordering and version matrix

| Code site | AE2025 | AE2026 |
| --- | --- | --- |
| `CreateStream` entry RVA | `0x26710` | `0x27920` |
| RecursiveMutex lock call | `0x2677D` | `0x2798D` |
| Success-path unlock | `0x2688B` | `0x27A04` |
| Actual native Creator invoke | `0x268D7` | `0x27A50` |
| `GetAsLeaf` | `0x26953` | `0x27ACC` |
| `InsertDefaultKey` | `0x26983` | `0x27AF5` |
| `SetConstant` | `0x26995` | `0x27B0B` |
| Global policy predicate | `0x269A3` | `0x27B1D` |
| `GetAsGroup` | `0x269B2` | `0x27B2C` |
| Deep decanonicalization | `0x269C0` | `0x27B3A` |

Addresses are original installed **RVA** locations, not callable SDK addresses, and not stable across Adobe versions.

## Callers and ownership

`TDB_StreamFactory::RegisterFactoryFunc` calls `CreateStream` for canonical initialization. In the archive reconstruction path, both `TDB_NamedStreamGroup::ReadAndStore` and `TDB_IndexedStreamGroup::ReadAndStore` call this *same* function for each serialized child MatchName. The resulting raw Stream must then be admitted by a parent, adopted and read. See [Document Stream Serialization](document-stream-serialization.md) and [Indexed Group Insertion](indexed-group-insertion.md).

The return of a new Stream pointer alone does not mean it is visible in AE's standard Timeline, participates in native editing or survives a saved AEP. Creating a foreign class additionally requires an authentic host-approved registration route, a correct C++ ABI and native editor/evaluator integration.

## Unknowns and safety conditions

**Unresolved:** meaning of all five arguments, exception safety and rollback, Creator callback ownership under concurrency and module unload, allocation and derived class memory lifetime for unknown types, exact runtime choice of decanonicalization, and macOS private ABI.

This is an **E2-L static finding**. No private host function was invoked to obtain this analysis. The independent verification code is `experiments/vector-shape/probe-src/tools/verify_tdb_document_instance_create_insert_load.py`, which pins the original TDB DLL SHA-256 and checks actual CALL ordering.

Further reading: [Factory registration and lifetime](factory-registration-lifetime.md), [Native Stream model](stream-object-model.md), [Parent admission](canonical-groups-admission.md). Research proof F-VECTOR-097.
