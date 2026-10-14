---
status: architecture-reference
last_verified: 2026-10-14
evidence: E0-H + E2-L + E2-X
versions: AE2025 / AE2026 Windows x64 and public 25.6 SDK
---

# Native Stream Object Model

A **Stream** is a host-side property object addressed within a layer, effect or another property group. A scripting `Property` and a public `AEGP_StreamRefH` are **interfaces into that hierarchy**, not a guarantee of a one-to-one correspondence with a given private C++ object.

This chapter documents the native value and group abstractions separately from their class registration, UI, identity, storage and rendering. See [Factory registration](factory-registration-lifetime.md) and [Canonical group grammar](canonical-groups-admission.md).

## Core native classes

| Private C++ type | Observed responsibility | Public counterpart | Evidence |
| --- | --- | --- | --- |
| `TDB_MatchName` | Semantic type identifier for lookup and group matching | `AEGP_GetMatchName`, scripting `matchName` | F-VECTOR-065, 093; E2-L |
| `TDB_StreamBase` | Common polymorphic stream interface and virtual methods | `AEGP_StreamRefH` is a reference, **not** this class | F-VECTOR-084/095; E2-L |
| `TDB_Stream` / `TDB_DerivedStream<Traits>` | Concrete or typed/adapted stream value behavior | `AEGP_GetStreamType`, value/animatable queries | F-VECTOR-094; E2-L |
| `TDB_StreamGroup` | Native group hierarchy, admissible children, UILayout | Named and indexed scripting groups; AEGP grouping type | F-VECTOR-084/095; E2-L |
| `TDB_StreamIDPath` | Internal path-based address for property operations | AEGP/Scripting structural property coordinates | AEIG state-model; E2-L |
| `BEE_StreamSpec` | BEE owner-associated stream selection/evaluation coordinate | Selected property/AEGP collection item | AEIG AEGP/BEE bridges; E2-L |
| `TDB_StreamFactory` | Name-to-Creator registry and canonical prototype cache | **No public general provider API identified** | F-VECTOR-093–096 |

Do not equate `AEGP_StreamRefH` with `TDB_StreamBase*`, an in-memory `TDB_StreamIDPath`, a serialized ID, or a user-facing property. Each can have a different invalidation and lifetime contract.

## Distinct identities

**MatchName** answers: *Which semantic class is this?* Many children of an indexed group may share `ADBE Paint Atom`. MatchName alone cannot identify one specific stroke or one property instance.

**Hierarchy path** answers: *Where is this stream under a particular owning object?* It includes child order, repeated names and named/indexed group semantics. Reordering may change address coordinates.

**Session identity** answers: *How do I identify this stream within the running AE session?* `AEGP_GetUniqueStreamID`, introduced in StreamSuite6, is documented as session-unique, but it is not a cross-save persistent identity. One AE2026 Shape audit returned zero for 359 IDs in its fixture despite zero API errors; the cause is not proven (F-VECTOR-009/063).

**Document identity** answers: *What survives save/reopen?* Do not substitute a raw pointer or session ID for an AEP-level identity without experimental evidence.

**Evaluation identity** answers: *What state, time and dependency graph contributed to a rendered result?* A stream path or value is not the same as a render GUID/receipt. See [State and stream identity](../streams-properties.md) and [Render Graph](../../render-graph/render-graph-model.md).

## Leaf and group semantics

```text
TDB_StreamBase
 ├── leaf-style native typed streams
 │    ├── numeric, spatial, color, enum
 │    ├── paint/mask path specialized values
 │    └── derived / evaluated stream implementations
 └── TDB_StreamGroup
      ├── Named Group (host-defined semantic children)
      └── Indexed Group (repeatable ordered children)
```

The tree illustrates observable **semantic** grouping. It does not purport to be exact MSVC inheritance for every stream subtype; use native symbols and RTTI before asserting a private C++ relationship.

### Named groups

A Named Group exposes distinguished children with fixed semantic identities, for example a Paint Atom's Properties and Transform groups. Child display labels may be localized; use MatchNames for semantic lookup. Named groups are **not generally insert-anything containers**.

### Indexed groups

An Indexed Group provides an ordered sequence of admitted child types: Paint Strokes, Shape Contents, and some Text Animator/Selector arrays. Addition, removal, duplication or reorder can invalidate public reference handles. The parent may enforce strict names or an accepted prefix grammar.

### Leaf values and public type gaps

A host Stream can be fully real while its internal value type is **not materialized as a supported `AEGP_StreamValue`**. In the observed Paint AE2026 fixture, `ADBE Paint Shape` was an editable native Path leaf but `AEGP_GetStreamType` reported `AEGP_StreamType_NO_DATA`, meaning normal public `GetNewStreamValue` must not be assumed valid. This is a public API exposure limit, *not absence of a native path value* (F-VECTOR-087).

## Concrete first-party polymorphic stream: OM_Stream

The built-in mask-path native object is a concrete `OM_Stream` from `OM.dll`, not from TDB or BEE directly:

```text
OM_Stream::Create
  -> U_MemTrackedObject::operator new(0x450)
  -> OM_Stream::OM_Stream
       -> TDB_DerivedStream<OM_MaskShapeStreamTraits> base constructor
       -> assign OM_Stream vtable
```

Both installed versions allocate **0x450 (1104)** bytes, initialize the derived vtable and a field at `this + 0x448`. The exported C++ class includes `CloneStream`, `Read`, `Write`, `GetValueEx`, `SetValue` and `CanHaveExpression`. These are **observations of one Adobe internal class**, not an interface template ready to copy into a third-party AEX. In particular, equal allocation sizes in 2025/2026 do not imply universal ABI stability.

Exact evidence: [F-VECTOR-094](https://github.com/ken-eizo/after-effects-internals-guide/blob/main/research/findings/F-VECTOR-094-om-maskshape-native-cpp-stream-abi-and-teardown.md), `datasets/ae-om-native-maskshape-stream-abi-and-teardown-2025-2026.json`.

## Memory and lifetime invariants

- The factory owns canonical prototype instances, but document-owned instances can have distinct owners and longer lifetimes.
- AEGP `StreamRefH` accessors have explicit release rules. Reacquire after structural edits; do not persist raw handles across topology mutations.
- A Stream with callbacks or vtable functions in an external DLL can become unsafe if that DLL unloads while the object survives. TDB's successful unregister path **does not** prove every child instance or Undo record was destroyed.
- Native template methods exposed via exports may require host allocation, object conventions and version-specific vtable slots.
- Derived/evaluated values, keyframes and expression results require separate timelines of ownership and cache invalidation.

## Actual implementation questions that remain open

The exact complete `TDB_StreamBase` polymorphic ABI; classification and type conversion of every `TDB_DerivedStream<Traits>` subtype; native 2025/2026 object layout variation beyond measured OM; mapping `TDB_StreamIDPath` to AEGP unique IDs across sessions; canonical prototype persistence/clone semantics; parent-held versus factory-held object retention; and macOS ABI and unload behavior remain unresolved.

For the API surface and type-by-type status, continue with [Public and internal API atlas](api-atlas.md). Evidence baseline: F-VECTOR-084, 087, 092–096.
