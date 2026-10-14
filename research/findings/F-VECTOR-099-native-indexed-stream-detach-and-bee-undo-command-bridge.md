---
date: 2026-10-15
status: PASS SHA-pinned AE2025/AE2026 native TDB/BEE static machine-code cross-check; not a third-party native plugin
evidence: E2-L original Windows PE exports/imports, x64 virtual dispatch and ordered native callsites
---

# F-VECTOR-099 — Native Stream detachment, parent pointer and BEE Undo command bridge

## Verified mechanism

The actual parent member in TDB_StreamBase is stored at **object offset +0x20** in the installed AE2025 and AE2026 builds: the SetParent method writes to [this+0x20] and notifies the native owning group when given a non-null parent.

On the observed successful path, TDB_IndexedStreamGroup::RemoveStream(index) retains the **existing child pointer**, removes the corresponding pointer from the indexed array, updates the reverse-index map, writes **zero to [child+0x20]**, and **returns the same child pointer**. That is an ownership-detach operation, rather than proof that deleting a timeline item immediately invokes the child's C++ deleting destructor. The later responsibility of a caller/Undo command holding the detached object remains unproven.

Separately, the first-party BEE commands for native Indexed Group **Add, Remove, Duplicate, Reorder** all take the layer's UndoContext and call the ordered trio:

~~~text
BEE_StartGroupWithNameFromStreamOperation
  → BEE_DoCommand
  → BEE_EndGroup
~~~

For native Add there is an additional, important cross-DLL predecessor:

~~~text
BEE_CmdAddToIndexedStreamGroup
  ├─ TDB.dll!TDB_StreamBase::CreateStream (direct BEE import)
  │    └─ TDB_StreamFactory::CreateStream (native tail jump)
  │         └─ registered native C++ Creator
  ├─ StartGroupWithNameFromStreamOperation
  ├─ BEE_DoCommand
  └─ BEE_EndGroup
~~~

The factory delegation resolves exactly in **both** installed versions. This unifies previously separated evidence for first-party property creation, registered native C++ typed Creators, and Undo command submission. The Add command's object creation starts **before** the group-opening call on this success path; automatic Undo rollback after a crashing Creator is not established.

## Original native callsite evidence

| Callsite | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| TDB_StreamBase::CreateStream trampoline | 0x36170 | 0x36C00 |
| Direct JMP to TDB_StreamFactory::CreateStream | 0x36189 | 0x36C19 |
| TDB_IndexedStreamGroup::RemoveStream | 0x3E0C0 | 0x3EB90 |
| SetParent writes native child+0x20 | 0x3F0EA | 0x3FB2A |
| Shrink native indexed child pointer vector | 0x3E1B7 | 0x3EC68 |
| UpdateReverseIndexVector | 0x3E1D6 | 0x3EC85 |
| Clear child parent +0x20 | 0x3E228 | 0x3ECDA |
| Return same detached raw pointer | 0x3E29E | 0x3ED3F |
| BEE Add invokes TDB StreamBase::CreateStream | 0x657937 | 0x672B4F |
| BEE Add starts named Undo group | 0x6579EF | 0x672C07 |
| BEE Add dispatches BEE_DoCommand | 0x657A1A | 0x672C32 |
| BEE Add ends Undo group | 0x657A24 | 0x672C3C |

The Remove/Duplicate/Reorder command group callsites are retained in the machine-readable receipt.

## What it does NOT establish

- That detached child objects are universally reused, kept alive by Undo tasks or immediately deleted by the caller; this requires task implementation and lifetime proof.
- That BEE_DoCommand automatically rolls back failed factory creation or validates foreign native C++ types.
- That calling private TDB mutation from an AEX is the same as registering a supported Undo operation.
- That an externally implemented CNL Stream can participate in BEE's Undo task inventory.

The actual binary modules have not been loaded by this probe or changed; no user AEP or Adobe installation was modified. macOS ABI remains unverified. **Product status: NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM.**

## Reproduction

Run: experiments/vector-shape/probe-src/tools/verify_tdb_native_detach_bee_indexed_undo.py

Evidence dataset: datasets/ae-tdb-native-detach-bee-command-undo-2025-2026.json. Both TDB/BEE DLLs and both AE releases are SHA-pinned; PASS 2/2. Related: F-VECTOR-095–098 and the native-property-system Indexed Group Removal / Structural Command and Undo chapters.
