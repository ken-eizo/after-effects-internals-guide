---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E0-H + E2-L + H
versions: Windows AE2025/2026 BEE and TDB modules, SDK25.6
---

# Native Structural Commands and Undo

An After Effects property operation crosses several systems: an underlying TDB Stream mutation, a BEE document-edit command, a public AEGP operation and the Timeline's interaction state. These are not identical APIs.

## Native structural command families

| BEE internal command | Operation |
| --- | --- |
| BEE_CmdAddToIndexedStreamGroup | Construct a registered native child and request insertion |
| BEE_CmdRemoveIndexedGroupEntry | Remove a child using its TDB_StreamIDPath |
| BEE_CmdDuplicateIndexedGroupEntry | Duplicate an existing indexed property |
| BEE_CmdReorderIndexedGroupEntry | Reorder an existing child |
| BEE_CmdSetStream | Apply a typed change payload to a native Stream |

These are first-party private C++ exports, **not supported SDK function declarations**.

## Shared first-party submission envelope

The original AE2025 and AE2026 machine code verifies that each of the four indexed operations — Add, Remove, Duplicate and Reorder — obtains the Layer's UndoContext and calls in this order:

~~~text
BEE_StartGroupWithNameFromStreamOperation
  → BEE_DoCommand(BEE_UndoContext, BEE_CommandInfo)
  → BEE_EndGroup(BEE_UndoContext)
~~~

This verifies **command submission and grouping**, not the full inverse task implementation or replay.

### Add also constructs the child through the native TDB factory

The native Add command imports **TDB_StreamBase::CreateStream** from TDB.dll. That method is a short trampoline to **TDB_StreamFactory::CreateStream**. This call is before the opening of the named Undo group in the examined code.

~~~text
BEE native Add command
  ├─ TDB_StreamBase::CreateStream [cross-DLL]
  │    └─ TDB_StreamFactory::CreateStream
  │         └─ registered native C++ Creator
  ├─ BEE_StartGroupWithNameFromStreamOperation
  ├─ BEE_DoCommand
  └─ BEE_EndGroup
~~~

Thus construction and Undo enrollment are two separate steps. The native call graph does **not** establish that a crashing Creator is rolled back by the command subsystem.

## Version-pinned x64 callsites

| Evidence | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| BEE Add command entry | 0x657820 | 0x672A20 |
| Add invokes TDB native CreateStream | 0x657937 | 0x672B4F |
| Add begins named Undo group | 0x6579EF | 0x672C07 |
| Add submits BEE_DoCommand | 0x657A1A | 0x672C32 |
| Add closes group | 0x657A24 | 0x672C3C |
| BEE Remove entry | 0x65CF50 | 0x678540 |
| Remove opens Undo group | 0x65D005 | 0x6785FC |
| Remove submits command | 0x65D0DA | 0x6786D1 |
| Remove closes group | 0x65D0EC | 0x6786E3 |
| BEE Duplicate entry | 0x65BA60 | 0x676F90 |
| BEE Reorder entry | 0x65DB90 | 0x6791A0 |

Detailed receipts also include the Begin/Do/End sequence for Duplicate and Reorder.

## Generic Undo task execution, history requeue and cleanup

Both native BEE_Undo and BEE_Redo pop a history record from a TaskStack, invoke a common native replay helper and enqueue the task record it produces on the opposite stack. The history record's native task pointer is held at offset +0x20; the replay calls the task's virtual +0x08 and stores its returned pointer into the new record at +0x20. The native BEE_UndoContext destructor also invokes a common stack-clear helper for both Undo and Redo stacks; the helper conditionally calls each task object's deleting destructor before removing the history list range. This is **E2-L verified in AE2025 and AE2026**. More recent concrete evidence establishes that an inverse Add task can own and conditionally destroy an indexed child Stream; see [BEE Undo Task Lifecycle](undo-task-lifecycle.md) (F-VECTOR-101) and [Indexed Add/Remove ownership](indexed-property-undo-task-ownership.md) (F-VECTOR-102).

## Important remaining ownership boundaries

TDB_IndexedStreamGroup::RemoveStream detaches a child and returns the original Stream pointer, clearing its parent field. This native operation alone does not identify who owns that pointer afterward.

F-VECTOR-102 identifies the **specific native Add/Remove inverse task pair**. The Remove task executes and returns an owning Add task for the detached Stream; on the owned, noncanonical branch, the Add task destructor calls the Stream virtual deleting destructor. Still unknown are every failure/rollback branch, behavior after project close in a live host, foreign type participation, and full safe module unload.

For an external C++ Stream provider this is critical because host-retained native objects can keep foreign vtable and destructor pointers alive beyond a plugin menu command. **No external CNL native class has passed these acceptance gates.**

## Public SDK boundary

The documented AEGP_DynamicStreamSuite4 provides Add/Delete/Duplicate/Reorder operations on preexisting host-supported indexed groups and documents undoability and StreamRef disposal. It does not register a foreign C++ type or expose a BEE_UndoContext.

See [Indexed Group Removal](indexed-group-removal.md), [Indexed Group Insertion](indexed-group-insertion.md), [Factory Lifetime](factory-registration-lifetime.md), [API Atlas](api-atlas.md) and [Adobe AEGP Suites](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/).

Evidence: F-VECTOR-099, original SHA-pinned AE2025/2026 TDB/BEE binary calls and datasets/ae-tdb-native-detach-bee-command-undo-2025-2026.json.
