---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E2-L + H + E0-H
versions: Windows AE2025/AE2026 first-party BEE.dll; official SDK25.6 public editing boundary
---

# BEE Undo Task Lifecycle — Replay, Reciprocal Tasks and Destruction

BEE's first-party document-edit commands do not merely mutate the authored value of a property. The host's Undo/Redo subsystem maintains independent **Undo** and **Redo TaskStacks**, executes task objects, creates new history records and later destroys discarded tasks. This chapter reconstructs the actual BEE implementation from original installed Adobe machine code. These methods and C++ object layouts are **not a public third-party SDK**.

## Key native types and roles

| Internal type or operation | Verified role | Ownership boundary |
| --- | --- | --- |
| `BEE_UndoContext` | Owns the Undo/Redo TaskStack state and command transaction context | Host-side object |
| `BEE_TaskStack` | List-backed collection of history records; Redo stack at context +0x28 | Host-side collection |
| History record `+0x20` | Contains pointer to an executable native task object | Record/task ownership separate from TDB Stream |
| Native task's vtable slot `+0x08` | Executed during Undo/Redo; returns a pointer stored as new history task | Concrete Add/Remove indexed pair now verified; other task types unresolved |
| Native task's vtable slot `+0x00` | Deleting-destructor call made for retired tasks | Uses MSVC native delete flag 1 |
| `BEE_Undo` / `BEE_Redo` | Pop records, replay tasks and place generated records on opposite stack | History subsystem |

The machine-code-confirmed offsets are private implementation details and have only been checked for two installed Windows builds.

## A native Undo/Redo step

~~~text
BEE_Undo(BEE_UndoContext)
  ├─ obtain UndoStack
  ├─ LIST_Remove -> one history record
  ├─ shared native task replay helper
  │    ├─ source history record.task at +0x20
  │    ├─ invoke task virtual method at vtable +0x08
  │    └─ output history record.task at +0x20 = returned pointer
  ├─ insert generated history record into RedoStack
  └─ retire a consumed transient task pointer if present

BEE_Redo(BEE_UndoContext)
  ├─ obtain RedoStack
  ├─ LIST_Remove -> one history record
  ├─ the SAME task replay helper and task callback
  ├─ insert generated history record into UndoStack
  └─ retire a consumed transient task pointer if present
~~~

The replay helper's `+0x08` callback is consistent with an **inverse-task factory/execute** convention, since both Undo and Redo use it and pass its resulting task pointer to the opposite history stack. However, the vtable method's private C++ declaration and every derived task's behavior are not reconstructed. We therefore do not assume every task produces a valid reciprocal object or that failure recovery is guaranteed.

### Native history record and Stream identity are different

A **TaskStack history record** is not a `TDB_StreamIDPath`, a C++ `TDB_StreamBase`, or the public `AEGP_StreamRefH`. Its task pointer at `record+0x20` refers to a BEE command object; the command object may then refer to or own Streams. Native `TDB_IndexedStreamGroup::RemoveStream` returns a detached Stream pointer. **F-VECTOR-102 now establishes one concrete ownership chain**: Remove executes and constructs an inverse Add task which retains the Stream reference with its ownership flag set; if that Add task is deleted while it still owns an eligible noncanonical Stream, its destructor calls the Stream's own virtual deleting destructor. The result is still scoped to first-party task code and verified branches; arbitrary command tasks and exception behavior remain unknown.

See [Indexed Group Removal](indexed-group-removal.md), [Concrete Indexed Task Ownership](indexed-property-undo-task-ownership.md) and [Structural Commands](structural-command-undo.md).

## Clearing Undo and Redo history

Both `BEE_UndoContext::ClearUndoStack` and `ClearRedoStack` call the **same** private helper. It retrieves list items using `LIST_GetItem`, obtains the task pointer, calls a native deleting-destructor slot when non-null, then removes the corresponding list range with `LIST_RemoveRange`.

~~~text
BEE_UndoContext::ClearUndoStack
   └─ native TaskStack clear helper(UndoStack)
        ├─ LIST_GetItem
        ├─ if record.task nonnull:
        │    └─ task->virtualDestructor(deleteFlag=1)
        └─ LIST_RemoveRange

BEE_UndoContext::ClearRedoStack
   └─ same helper(RedoStack)
~~~

During the destructor `BEE_UndoContext::~BEE_UndoContext`, the very same TaskStack clear helper is called **twice**. F-VECTOR-103 independently establishes that the real `BEE_Project::~BEE_Project` calls this destructor directly on its project-associated context subobject; see [Project UndoContext Lifecycle](project-undo-context-lifecycle.md):
1. with the embedded Undo stack at `context+0x00`;
2. with the Redo stack at `context+0x28`.

This verifies the *shared teardown edge* connecting a native UndoContext's destruction to the deleting-destructor calls of both categories of history tasks. **F-VECTOR-103 now confirms that the BEE_Project destructor calls the UndoContext destructor directly**, after a separate holder-member cleanup and before freeing the holder allocation. The complete host shutdown ordering beyond the project destructor remains unverified.

### MSVC deleting-destructor detail

In the 2025 native helper, the callsite sets `edx=1` immediately before invoking `call qword ptr [rax]` through the task's vtable slot zero.

In AE2026, the same deletion flag is derived from `ebx=1`, copied into `edx`, and then passed into the same virtual slot. The difference is an instruction-generation detail, not a demonstrated API design change.

## Cross-version native code evidence

| Function / callsite | AE2025 BEE.dll RVA | AE2026 RVA |
| --- | --- | --- |
| UndoContext destructor | `0x67FBC0` | `0x69BF90` |
| First embedded stack cleanup in destructor | `0x67FC1F` | `0x69BFE4` |
| Second embedded stack cleanup | `0x67FC32` | `0x69BFF7` |
| Shared history clear helper | `0x67C110` | `0x698120` |
| `LIST_GetItem` during cleanup | `0x67C171` | `0x698179` |
| Task virtual deleting destructor | `0x67C1D9` | `0x6981D9` |
| `LIST_RemoveRange` during cleanup | `0x67C289` | `0x698298` |
| `BEE_Undo` | `0x67B440` | `0x697430` |
| `BEE_Redo` | `0x67ADA0` | `0x696E40` |
| Shared task replay helper | `0x67B9C0` | `0x6979C0` |
| Task vtable `+0x08` invocation | `0x67BBF3` | `0x697BEB` |
| New task pointer stored in output record `+0x20` | `0x67BBF6` | `0x697BEE` |
| Shared history requeue helper | `0x67CC20` | `0x698C90` |

All entries are **RVAs of the original installed binary**. They must not be interpreted as documented public function addresses.

## Requirements for a genuine new native type

A new type provider would need to handle not just registration and normal document ownership, but also its lifetime while **detached** or referenced by **history tasks**. Unregistering the type factory is insufficient proof that no derived C++ class object, task or callback can still be destroyed by the host. A provider DLL must not be unloaded while surviving TaskStack records could indirectly require code or destructors from that provider.

The concrete first-party indexed Add/Remove task pair and its guarded Stream destruction are **now verified statically** in F-VECTOR-102. To certify a *foreign* native type, however, it would be necessary to demonstrate an authorized factory/provider registration boundary and then qualify the native task ownership under actual Undo, Redo, Clear Undo, Clear Redo, project close/reopen and controlled module unload, including every error branch.

## Public SDK boundary and sources

Public `AEGP_DynamicStreamSuite4` Add/Delete/Duplicate/Reorder APIs operate on supported existing native properties and have documented Undo semantics. Public AEGP code cannot manufacture a BEE task object or add an independent Stream subclass merely by calling these APIs.

F-VECTOR-101 verifies the above machine-code paths with a standalone SHA-pinned script:

~~~powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_bee_undo_task_replay_and_destruction.py"
~~~

Evidence datasets: `datasets/ae-bee-undo-task-reciprocal-replay-destruction-2025-2026.json` (generic TaskStack) and `datasets/ae-bee-indexed-add-remove-reciprocal-stream-ownership-2025-2026.json` (concrete task Add/Remove, F-VECTOR-102). No private Adobe function was called, no AEP changed, and no foreign `CNL:` native Stream was registered. Related: [Native Stream Object Model](stream-object-model.md), [Factory Registration](factory-registration-lifetime.md) and [Verification Matrix](verification-and-version-matrix.md).
