---
date: 2026-10-15
status: PASS strict installed Windows AE2025/AE2026 BEE.dll x64 static task replay and UndoContext destructor
evidence: E2-L SHA-pinned original Adobe BEE PE, vtable offsets and LIST imports; no private calls or live AE document changes
---

# F-VECTOR-101 — Native BEE Undo/Redo task replay and two-stack destruction

## What is new

F-VECTOR-099 established that first-party BEE Add/Remove/Duplicate/Reorder indexed-property commands submit changes using BEE Undo groups. This finding traces what happens **after submission**, at a deeper and independent boundary: generic native Undo/Redo task records and their deterministic teardown in the native BEE command system.

In installed AE2025 and AE2026 Windows builds, both `BEE_Undo(BEE_UndoContext&)` and `BEE_Redo(BEE_UndoContext&)`:
1. **pop a history record** using `LIST.dll!LIST_Remove`;
2. call the **same private task replay helper**;
3. pass the newly produced task record to the **same history enqueue helper**, using the other stack's native `GetRedoStack` or `GetUndoStack` accessor;
4. dispose a consumed transient task pointer through a virtual deleting destructor on a branch.

The shared task replay helper takes a source native history record containing a task pointer at **offset +0x20**, invokes that task object's **virtual slot +0x08**, and stores the returned task pointer into **offset +0x20 of an output history record**.

The observed code strongly supports a **reciprocal task/inverse-command pattern**: applying an Undo task produces a task for the corresponding Redo history, and vice versa. It does **not** prove the exact object layout or behaviour of a specific Add/Remove native Stream task, nor does it prove that an inverse always succeeds.

~~~text
BEE_Undo / BEE_Redo
  ├─ pick UndoStack or RedoStack from BEE_UndoContext
  ├─ LIST_Remove(history stack, final record)
  ├─ common task replay executor
  │    ├─ source record.task [+0x20]
  │    ├─ task vtable[+0x08](source record, context, status)
  │    └─ output record.task [+0x20] = returned task pointer
  ├─ enqueue output record into opposite history stack
  └─ conditionally destroy consumed/transient task via vtable[0]
~~~

## Native stack destruction — separately verified

The **real `BEE_UndoContext::~BEE_UndoContext` destructor** calls the **same internal history-clear helper twice**, first with its Undo stack and second with the embedded Redo stack at **context +0x28**. Public `ClearUndoStack` and `ClearRedoStack` methods also route through that same internal helper.

~~~text
BEE_UndoContext::~BEE_UndoContext
  ├─ shared TaskStack clear helper(context, UndoStack)
  │    ├─ LIST_GetItem(record)
  │    ├─ retrieve record.task [+0x20]
  │    ├─ if nonnull: vtable[0](task, deletingDestructorFlag=1)
  │    └─ LIST_RemoveRange(...)
  └─ shared TaskStack clear helper(context, RedoStack = context+0x28)
       └─ same per-task conditional destructor and list removal
~~~

The exact native call uses an MSVC deleting-destructor convention: **virtual slot 0, deletion flag 1**. The 2025 build places 1 directly in `edx`, whereas the 2026 build stores constant 1 in `ebx` and forwards it to `edx`. These variants were independently checked, rather than assuming identical instruction patterns.

**Critical distinction:** the pointer destroyed here is the **BEE history task object**, not necessarily the native `TDB_StreamBase` that was detached from a property group. A task may contain pointers, smart pointers or clones that have their own destructors, but that relationship has not yet been recovered for a concrete Indexed Group removal task.

## Cross-version machine-code markers

| Native operation | AE2025 BEE.dll RVA | AE2026 BEE.dll RVA |
| --- | ---: | ---: |
| `BEE_UndoContext::~BEE_UndoContext` | `0x67FBC0` | `0x69BF90` |
| Common TaskStack clear helper | `0x67C110` | `0x698120` |
| Clear helper `LIST_GetItem` | `0x67C171` | `0x698179` |
| Clear helper virtual deleting destructor | `0x67C1D9` | `0x6981D9` |
| Clear helper `LIST_RemoveRange` | `0x67C289` | `0x698298` |
| `BEE_Undo` | `0x67B440` | `0x697430` |
| `BEE_Redo` | `0x67ADA0` | `0x696E40` |
| Common task replay helper | `0x67B9C0` | `0x6979C0` |
| Output/requeue helper | `0x67CC20` | `0x698C90` |

The exact instruction sites for pop/replay/callback/output pointer/requeue, the two destructor calls and each public clear wrapper are preserved in `datasets/ae-bee-undo-task-reciprocal-replay-destruction-2025-2026.json`.

### Consequences for native Stream extensions

- Correctly implementing `TDB_StreamFactory::CreateStream`, `CanStore` and `InsertStream` does **not** automatically implement Undo and Redo.
- A custom native Stream would have to survive both **document ownership** and **Undo task references**, potentially after it was detached from its group.
- Clearing history and destroying an UndoContext can invoke virtual destructors in independently owned tasks, so a foreign C++ provider cannot safely assume that no callback remains after a property is deleted or after its factory is unregistered.
- The true last safe unload point requires identifying whether a concrete task owns a `TDB_StreamBase`, retains its foreign virtual methods, and destroys it when the task's deleting destructor runs.
- The exact concrete task ownership, Undo exception rollback, history compression, module lifetime and complete project-close behavior remain **unverified**.

## Strict reproducibility

~~~powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_bee_undo_task_replay_and_destruction.py"
~~~

The verifier pins the exact original BEE.dll hashes in both installed releases, resolves named exports, bounded function bodies, direct references and `LIST.dll` imports and checks the conditional deletion and reciprocal-record write. It does **not load or call any private Adobe symbol**, and no AEP was opened or changed.

Data: `datasets/ae-bee-undo-task-reciprocal-replay-destruction-2025-2026.json`. Feature chapter: `docs/state-model/native-property-system/undo-task-lifecycle.md`. Product remains `NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM`.
