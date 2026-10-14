---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E2-L + H
versions: Windows AE2025 / AE2026 native TDB/SLU; no foreign custom AEP runtime tested
---

# TDB_StreamGroup::Read / Write — Native Property Serialization

`TDB_StreamGroup` persists a **native group of Stream objects** through Adobe's internal **SLU** serialization layer. These methods are not SDK APIs or a public specification of the AEP file format. They are concrete C++ operations performed by an Adobe-owned object as part of host state persistence.

The critical implementation condition is that **loading a group reconstructs children from saved MatchNames using the active native Creator factory**, instead of merely retaining unknown opaque bytes.

## Write path: group, identity, child names and values

```text
TDB_StreamGroup::Write(SLU_File)
  ├─ SLU_BeginChunkWrite
  ├─ TDB_StreamBase::Write
  ├─ TDB_StreamBase::WriteUniqueStreamID
  ├─ iterate native group child streams
  │    ├─ inspect authored / canonical state
  │    ├─ TDB_StreamFactory::GetCanonicalStream(matchName)
  │    ├─ TDB_MatchName::Write
  │    └─ virtual child Write + native metadata
  ├─ TDB_MatchName::WriteEndOfGroupMarker
  └─ SLU_EndChunkWrite
```

The internal direct calls and vtable offsets are observed in both builds. Canonical lookup is used twice in the examined group writer, showing that written child metadata may be interpreted relative to the host's registered canonical native class. We have not decoded or published complete SLU atom/chunk binary layouts or all conditional metadata tags.

## Read path: group and per-child reconstruction

```text
TDB_StreamGroup::Read(SLU_File, chunk)
  ├─ construct temporary TDB_MatchName
  ├─ SLU_ScDescendList (nested list)
  ├─ TDB_StreamBase::Read / ReadUniqueStreamID
  └─ loop:
       ├─ TDB_MatchName::Read(next child)
       ├─ IsEndOfGroupMarker -> if true, stop
       └─ virtual ReadAndStore (+0x1B8)
            ├─ IndexedStreamGroup::ReadAndStore
            │    ├─ CreateStream(saved child MatchName)
            │    ├─ if null, no child Insert/Read call
            │    ├─ GetNumStreams
            │    ├─ InsertStream (parent admission, path and parent update)
            │    └─ new_child->Read(SLU_File, child chunk)
            └─ NamedStreamGroup::ReadAndStore
                 ├─ CreateStream(saved child MatchName)
                 ├─ look up existing named member
                 ├─ optional EnsureUILayoutComplete / UpgradeChildStream
                 └─ read the relevant new or upgraded child
```

The virtual `ReadAndStore` slot `+0x1B8` is resolved directly in the original compiled `TDB_IndexedStreamGroup` and `TDB_NamedStreamGroup` **vtables**, not guessed from the exposed C++ function name. Each implementation makes an actual direct call to `TDB_StreamFactory::CreateStream`.

### Original-machine-code order

| Native method/call | AE2025 TDB.dll RVA | AE2026 RVA |
| --- | --- | --- |
| `TDB_StreamGroup::Write` | `0x43EF0` | `0x44A50` |
| Write native UniqueStreamID | `0x43F71` | `0x44AD6` |
| Write child's MatchName | `0x4427B` | `0x44DFC` |
| Write end-of-group marker | `0x442A4` | `0x44E1F` |
| `TDB_StreamGroup::Read` | `0x3D4C0` | `0x3E040` |
| Read child's MatchName | `0x3D556` | `0x3E0D6` |
| Virtual ReadAndStore dispatch `+0x1B8` | `0x3D58C` | `0x3E10C` |
| Indexed ReadAndStore body | `0x3D6E0` | `0x3E260` |
| Indexed child `CreateStream` | `0x3D717` | `0x3E28C` |
| Indexed child `InsertStream` | `0x3D749` | `0x3E2B7` |
| Indexed child virtual `Read` `+0x118` | `0x3D76D` | `0x3E2D8` |
| Named child `CreateStream` | `0x3D7DE` | `0x3E333` |
| Named `UpgradeChildStream` `+0x1B0` | `0x3D898` | `0x3E3D9` |

## The hidden precondition: a matching registered Creator must exist

Project load is not independent of the **current factory registry**. Each child is reconstructed through `CreateStream` and is then subjected to the group's admission/owner contract. A plugin that manages to register an external Stream class only after a project has already been loaded may be too late to reconstruct saved instances of that class.

A positive native type provider must therefore establish how startup/project-load ordering ensures its Creator is available at the right time. Internal Adobe providers `OM_Birth`, `FLT_Birth` and `BEE_Birth` are called from the host's native initialization code; this is **not** a supported third-party AEX registration phase (F-VECTOR-093).

### Unknown types and failure handling

**The native missing-type error-report flag differs by group.** Both AE2025 and AE2026 Named ReadAndStore callers pass 0 and Indexed callers pass 1 for the same fifth CreateStream argument. The factory's absent-Creator branch uses it to skip or reach an Adobe U.dll reporting function. This is a static finding, not a host-tested project load outcome. See [Native Archive Type Compatibility](archive-type-compatibility.md) and F-VECTOR-100.

The Indexed loader has an explicit null check after `CreateStream`; if it returns null, the usual insertion and child-read calls are skipped in the inspected branch. However, `CreateStream` also contains error-reporting and optional assertions governed by its flags. This does **not** prove what happens when a real AE instance opens an AEP containing a genuinely unknown or incompatible type.

Do not claim any of the following without an isolated host test:
- unsupported custom property data is silently preserved for a future reopen;
- unsupported data is always dropped;
- a missing Creator always fails safely without project corruption;
- the host supports arbitrary unknown type migrations;
- an inserted arbitrary C++ class correctly serializes, clones or participates in Undo/Redo.

## Versioned virtual insertion difference

The Indexed loader calls its virtual `InsertStream` using **slot `+0x210` in AE2025**, but **`+0x218` in AE2026**; the latter has a new `InsertStreamOptions` overload at `+0x210`. This is a real private ABI difference in the load path, not just binary address relocation. See [Indexed Group Insertion](indexed-group-insertion.md).

## Persistence identity vs editable state

A native `UniqueStreamID`, `TDB_StreamIDPath`, a serialized MatchName, a keyframe value and a Script/AEGP `StreamRefH` are **different identities or access representations**. The fact that a Group writer emits a native UniqueStreamID does not mean AEGP's session UniqueStreamID will remain constant after an AEP reopen. The identity/path semantics require separate verification.

Native leaf values add their own `TDB_Stream::Read/Write` machinery, including key data, expression state and SLU atom value serialization. Native groups can contain `NO_DATA` leaves such as the special Paint Path, which are not necessarily exposed as public `AEGP_StreamValue2` values.

## Related feature reference

- [Native Stream Object Model](stream-object-model.md)
- [CreateStream and instance initialization](stream-instance-creation.md)
- [Indexed Stream insertion and parent ownership](indexed-group-insertion.md)
- [Factory registration/lifetime](factory-registration-lifetime.md)
- [Property Operations and Undo](property-operations.md)
- [AEP archive and project state](../../persistence/aep-binary-model.md)

Evidence: F-VECTOR-025 (native clone/serialization), F-VECTOR-093–098. Strict 2025/2026 SHA-pinned static verifier: `experiments/vector-shape/probe-src/tools/verify_tdb_document_instance_create_insert_load.py`. Dataset: `datasets/ae-tdb-document-instance-create-insert-load-2025-2026.json`.

**Scope:** no private host functions called, no actual foreign native `CNL:` Stream saved/reopened; experimental goal remains unachieved.
