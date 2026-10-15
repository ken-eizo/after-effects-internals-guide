---
date: 2026-10-15
status: PASS two-version strict offline original BEE 2025/2026 PE command tables, concrete MSVC RTTI/vtables and conditional native Stream destruction
evidence: E2-L SHA-pinned original BEE.dll x64, COL RTTI TypeDescriptors, exact vtables, direct imports and bounded native instructions; no private AE runtime calls
---

# F-VECTOR-102 — Concrete BEE Indexed Add/Remove Undo tasks and the detached TDB Stream lifetime

## Major discovery

F-VECTOR-101 established a **generic** native Undo/Redo task replay system: the command history invokes the task's virtual slot **+0x08** to produce the next inverse task, and discarding a history record invokes the task's **virtual deleting destructor at slot 0**. In this finding, both endpoints are traced into **concrete Adobe first-party indexed-property command task classes**, not merely unnamed BEE helpers.

The original BEE.dll **32-byte native command registry** is decoded and independently cross-checked against MSVC RTTI Complete Object Locators and concrete virtual function pointers in **both AE2025 and AE2026**. Two registered task classes are:

- **BEE_DoAddToIndexedStreamGroupTask**
- **BEE_DoRemoveIndexedGroupTask**

Their virtual execution functions construct **each other's concrete C++ type** and return it as the newly generated inverse task:

~~~text
BEE_DoRemoveIndexedGroupTask::execute() [vtable+0x08]
  → run indexed native removal against authored BEE/TDB group
  → allocate and construct BEE_DoAddToIndexedStreamGroupTask
  → copy/reassign native StreamIDPath and removed child reference
  → set newly constructed Add task's ownership flag to 1
  → return Add task to generic Undo/Redo record manager

BEE_DoAddToIndexedStreamGroupTask::execute() [vtable+0x08]
  → perform native indexed insertion and host update steps
  → allocate and construct BEE_DoRemoveIndexedGroupTask
  → return Remove task to generic Undo/Redo record manager
~~~

**The inverse class identity is verified at exact native instructions**, where the creation function loads the other class's known vtable RVA and stores it into the newly allocated object's first 8 bytes. It does not merely infer this from string labels or the existence of similar names.

## The missing Stream lifetime connection is now proven, conditionally

The virtual deleting destructor of **BEE_DoAddToIndexedStreamGroupTask** has a conditional owned-child disposal branch in **both versions**:

~~~text
BEE_DoAddToIndexedStreamGroupTask::~... (deleteFlag)
  if task.ownsStream && task.stream != null:
    if NOT TDB_StreamBase::IsCanonical(task.stream):
       owner = TDB_StreamBase::GetParent(task.stream)
       if owner != null:
          success = owner->virtual RemoveChild(task.stream) [+0x1E0]
          if not success:
              host debug assertion/report path
       if task.stream != null:
          task.stream->virtual deleting destructor(deleteFlag=1)

  TDB_StreamIDPath::~TDB_StreamIDPath(task.path)
  BEE task base destructor
  if deleteFlag&1: deallocate this BEE task
~~~

This is a **direct code-level bridge** from the native Undo task lifecycle into the native **TDB_StreamBase derived object's virtual destructor**. The direct native import of `IsCanonical`, `GetParent` and `TDB_StreamIDPath` plus the precise machine-code transfer into a task-held Stream pointer make this significantly stronger than the earlier inference that Undo might retain a Stream.

It also establishes that the task's ownership flag and native `IsCanonical` gate are important: the code does **not** always delete every Stream pointer when a task is destroyed. When a native Stream still has a parent, the task first calls the parent group's **virtual slot +0x1E0**; the precise parent implementation and its failure semantics vary by the owner and are **not certified** for third-party types.

### Versioned C++ object layout

| Native private field / instruction | AE2025 | AE2026 |
| --- | --- | --- |
| Indexed Add task's Stream pointer | task `+0x40` | task `+0x40` |
| Indexed Add task ownership flag | task `+0x48` | task `+0x50` |
| Add task allocation size | `0x50` bytes | `0x58` bytes |
| Native Stream virtual deleting destructor | virtual vtable `+0x00`, `edx=1` | same |
| Native parent removal attempt | virtual `+0x1E0` | same |
| Add task native `TDB_StreamIDPath` field | task `+0x18` | task `+0x18` |

This shows a private ABI change even where the two task classes share the same semantic role: **the ownership flag is at a different offset in AE2026**. No copied AE2025 class layout or allocation can be used in AE2026.

### Exact important native sites

| Operation | AE2025 BEE.dll RVA | AE2026 BEE.dll RVA |
| --- | ---: | ---: |
| Command table data start | `0xFEC250` | `0x104C530` |
| Add task command table index | `70` | `71` |
| Remove task command table index | `72` | `73` |
| Add native C++ vtable | `0xF914B8` | `0xFF0860` |
| Remove native C++ vtable | `0xF914D8` | `0xFF0880` |
| Add deleting destructor (slot 0) | `0x549C90` | `0x568A30` |
| Remove deleting destructor (slot 0) | `0x549EE0` | `0x568CB0` |
| Add execute (slot `+0x08`) | `0x54C640` | `0x56B270` |
| Remove execute (slot `+0x08`) | `0x54CF00` | `0x56BC10` |
| Add execute loads **Remove** vtable for inverse | `0x54C978` | `0x56B5BD` |
| Remove execute loads **Add** vtable for inverse | `0x54D27D` | `0x56BFAB` |
| Remove execute sets new Add ownership flag=1 | `0x54D287` | `0x56BFB5` |
| Add destructor checks owned flag | `0x549CE3` | `0x568A83` |
| Add destructor checks `IsCanonical` | `0x549CFA` | `0x568A9A` |
| Add destructor checks `GetParent` | `0x549D0C` | `0x568AAC` |
| Add destructor attempts parent virtual remove | `0x549D2C` | `0x568AC5` |
| Add destructor calls Stream virtual deleting destructor | `0x549DE7` | `0x568B84` |

All RVAs refer to the exact pinned **original** Adobe files, not portable function pointers.

## How the full native ownership chain now fits

~~~text
First-party property Remove command
 → BEE_DoRemoveIndexedGroupTask
 → native group removes authored child
 → returns a BEE_DoAddToIndexedStreamGroupTask inverse
      ├─ stores removed native TDB Stream pointer
      └─ marks this inverse as owner of that Stream

If the inverse task stays on Undo or Redo history:
 → BEE_UndoContext owns task-history record
 → Undo/Redo may execute the inverse, yielding reciprocal Remove task

If the inverse Add task is discarded instead:
 → BEE_UndoContext ClearUndoStack / ClearRedoStack / destructor
 → common TaskStack clearer
 → virtual deleting destructor of BEE_DoAddToIndexedStreamGroupTask
 → when own-flag && non-null && noncanonical:
      ├─ attempt parent detachment if parent still exists
      └─ Stream's own virtual deleting destructor
~~~

This qualifies the **previously open last-owner question for this specific built-in Add/Remove Indexed task pair**. It does not establish that *every* BEE task owns Streams, that all exceptions are safe, or that code from an independently loaded plugin can register as a native task or owner.

## What is still NOT demonstrated

- User-authored foreign `CNL:` native TDB Stream registration in live AE: **NOT DELIVERED**.
- Exact BEE host command dispatch table authorization to introduce a new third-party task kind.
- Runtime failure behavior for malformed/unknown native Stream classes, reentrant callbacks and project unload.
- Safe foreign DLL unload while an Undo task references a foreign virtual class: **not qualified**.
- Runtime proof of all branch outcomes, all object destructor subclasses and an AEP saved/reopened with a foreign Stream.
- macOS ABI, vtable, memory allocator and TaskStack object layout.

This discovery is **first-party BEE internal implementation, not SDK support**.

## Strict reproducible verifier

~~~powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_bee_indexed_task_inverse_and_stream_lifetime.py"
~~~

The script SHA-pins original AE2025/26 BEE.dll, decodes command table names, native MSVC RTTI CompleteObjectLocator class names, actual class vtables, inverse vtable writes, native `IsCanonical` / `GetParent` imports and exact conditional deletion. Both versions PASS in static x64 mode; zero Adobe private API calls. Dataset: `datasets/ae-bee-indexed-add-remove-reciprocal-stream-ownership-2025-2026.json`.

Companion feature: `docs/state-model/native-property-system/indexed-property-undo-task-ownership.md`. Generic task lifecycle: F-VECTOR-101. Native `RemoveStream` detach: F-VECTOR-099.
