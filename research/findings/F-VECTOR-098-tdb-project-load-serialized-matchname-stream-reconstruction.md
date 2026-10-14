---
date: 2026-10-15
status: PASS offline strict AE2025/2026 native TDB group serialization-to-creator-to-owned-child reconstruction
evidence: E2-L SHA-pinned original TDB.dll PE, native StreamGroup/Named/Indexed vtables and bounded x64 CALLs; not an actual foreign AEP roundtrip
---
# F-VECTOR-098 — Native StreamGroup project deserialization: serialized MatchName → Creator → indexed insertion → child Read

## Core discovery

The private native project loader is **not** equivalent to deserializing an arbitrary object or cloning the canonical prototype. The built-in `TDB_StreamGroup::Read` reads each child `TDB_MatchName` and uses a **virtual per-group `ReadAndStore`** entry at **vtable `+0x1B8`**.

Both `TDB_NamedStreamGroup` and `TDB_IndexedStreamGroup` implement that virtual slot. The child loader invokes **`TDB_StreamFactory::CreateStream` with the serialized child's MatchName**. In the Indexed case, a successfully constructed child is appended to the native group **before** its virtual `Read` method is called.

```text
TDB_StreamGroup::Read(file, chunk)
  ├─ read base stream state / unique Stream ID
  ├─ SLU nested-list chunk iterator
  └─ repeat for children:
      ├─ TDB_MatchName::Read(file, childChunk)
      ├─ TDB_MatchName::IsEndOfGroupMarker()
      └─ virtual ReadAndStore [vtable +0x1B8]
           ├─ TDB_IndexedStreamGroup::ReadAndStore
           │    ├─ TDB_StreamFactory::CreateStream(saved MatchName)
           │    ├─ skip remainder if no child object returned
           │    ├─ GetNumStreams  [virtual +0x168]
           │    ├─ InsertStream   [virtual +0x210 AE2025 / +0x218 AE2026]
           │    │    └─ CanStore, reverse-index, cached path, SetParent
           │    └─ child->Read(file, chunk) [virtual +0x118]
           └─ TDB_NamedStreamGroup::ReadAndStore
                ├─ TDB_StreamFactory::CreateStream(saved MatchName)
                ├─ locate existing named child
                ├─ conditionally EnsureUILayoutComplete / native upgrade route
                └─ read newly created/mapped child's state
```

This establishes the missing implementation connection between **registered native class provider** (F-VECTOR-093–097), **parent admission/identity** (F-VECTOR-084/097), and **project load**. A type provider that is available only while the user adds a property, but not when an AEP reopens, cannot be assumed capable of restoring the same document hierarchy.

### Exact code anchors

| Native operation | AE2025 TDB.dll RVA | AE2026 RVA |
| --- | --- | --- |
| `TDB_StreamGroup::Read` | `0x3D4C0` | `0x3E040` |
| Read child's `TDB_MatchName` | `0x3D556` | `0x3E0D6` |
| Test end-of-group marker | `0x3D560` | `0x3E0E0` |
| Virtual `ReadAndStore` dispatch `+0x1B8` | `0x3D58C` | `0x3E10C` |
| Native Indexed `ReadAndStore` body | `0x3D6E0` | `0x3E260` |
| Indexed child `CreateStream` call | `0x3D717` | `0x3E28C` |
| Indexed child GetNumStreams | `0x3D72F` | `0x3E2A4` |
| Indexed child InsertStream dispatch | `0x3D749` | `0x3E2B7` |
| Indexed child virtual Read | `0x3D76D` | `0x3E2D8` |
| Native Named `ReadAndStore` body | `0x3D7A0` | `0x3E300` |
| Named child `CreateStream` call | `0x3D7DE` | `0x3E333` |
| Named child upgrade dispatch `+0x1B0` | `0x3D898` | `0x3E3D9` |

The **virtual slot names** were not inferred merely from numeric offsets: both versions' exported `TDB_NamedStreamGroup` and `TDB_IndexedStreamGroup` vtables resolve `+0x1B8` to their real `ReadAndStore` exports, and `TDB_Stream` vtable `+0x118` resolves to exported `Read`. The checked real `TDB_IndexedStreamGroup` vtable maps the insertion slot to the appropriate version's `InsertStream` implementation.

The named-group loader takes two broad paths depending on whether a named child exists. The exact meaning of all flags and upgrade methods has **not** been exhaustively resolved: it must not be described as guaranteed user-editable custom group migration.

## Native write side — names, IDs and end marker

`TDB_StreamGroup::Write` is the counterpart to the group loader, and in both inspected versions its native success path:

- enters an SLU chunk/list writer;
- writes base stream state and `WriteUniqueStreamID`;
- iterates children and consults `TDB_StreamFactory::GetCanonicalStream` for canonical-relative metadata decisions;
- emits the child `TDB_MatchName::Write`;
- writes each child through virtual streaming callbacks;
- finishes using `TDB_MatchName::WriteEndOfGroupMarker` and `SLU_EndChunkWrite`.

Selected source code callsites:

| Native operation | AE2025 | AE2026 |
| --- | --- | --- |
| `TDB_StreamGroup::Write` | `0x43EF0` | `0x44A50` |
| `WriteUniqueStreamID` | `0x43F71` | `0x44AD6` |
| `GetCanonicalStream` | `0x44084`, `0x440F8` | `0x44BF8`, `0x44C78` |
| `TDB_MatchName::Write` | `0x4427B` | `0x44DFC` |
| WriteEndOfGroupMarker | `0x442A4` | `0x44E1F` |

This is **implementation evidence of the native group serialization machinery**, not an undocumented public AEP file-format specification and not a demonstration that unsupported foreign class data survives AE save and reopen.

## Unregistered or otherwise invalid child types

Both `TDB_IndexedStreamGroup::ReadAndStore` versions have an explicit **null-return branch** immediately after `CreateStream`. That branch skips the subsequent Insert/Read body for that child. The preceding `CreateStream` function also has its own flags and error-reporting behavior. Thus:

- we have shown the positive **Creator-dependent load sequence**;
- we have shown a null case in which no reconstructed Indexed child reaches Insert/Read;
- we have **not** proven how every malformed/unknown/unregistered type affects the full host AEP load, warnings, roundtrip serialization or Undo history;
- we must not claim unknown Stream payload is always safely preserved or always dropped.

Moreover, a matching Creator alone is insufficient: actual `InsertStream` rechecks the parent's `CanStore` and index constraints, even in the read path. A foreign child with a spoofed Shape prefix and a working factory still has to satisfy host ownership/editing/render/persistence contracts.

## Private ABI drift

The 2025 Indexed `InsertStream` virtual slot is `+0x210`, whereas AE2026 uses `+0x218` for the short `InsertStream(index,child)` wrapper and `+0x210` for the options-taking overload. This is directly observed **inside the native document reconstruction callsites**, further demonstrating that any private external subclass/vtable ABI is version-specific.

## Verification and remaining product gates

Strict independent 2025+2026 validator:
```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_tdb_document_instance_create_insert_load.py"
```

Data: `datasets/ae-tdb-document-instance-create-insert-load-2025-2026.json` (per-version original SHA-256 and precise sites).

No private functions were executed, no AEP was modified, no foreign native CNL Stream was registered or round-tripped. Product state remains **NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM**.

This finding is integrated by topic into `docs/state-model/native-property-system/stream-instance-creation.md`, `indexed-group-insertion.md` and `document-stream-serialization.md`. Do not replace the individual API docs with this experimental record.
