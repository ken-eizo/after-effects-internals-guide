---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E2-L + H
versions: Windows AE2025 / AE2026 BEE.dll; macOS and foreign Stream ABI unverified
---

# Indexed Property Undo — Inverse Add/Remove Tasks and Stream Ownership

The actual native BEE indexed-property editor has concrete C++ task classes. Removing a built-in child property does not merely erase a value: it creates an inverse **Add** task and transfers a reference to the removed native Stream. That task may later reinsert the child during Undo, or **destroy the child when its history entry is discarded**.

**Scope:** original, SHA-pinned Adobe AE2025 and AE2026 Windows binaries. This is a reconstruction of *Adobe's own native mechanism*, **not a supported third-party AEX interface** and not a live demonstration of a foreign property class.

## Native registered command classes

| Concrete native BEE task | AE2025 command index | AE2026 index | Inverse |
| --- | ---: | ---: | --- |
| `BEE_DoAddToIndexedStreamGroupTask` | 70 | 71 | Remove |
| `BEE_DoRemoveIndexedGroupTask` | 72 | 73 | Add |
| `BEE_DoDuplicateIndexedGroupTask` | 71 | 72 | Not reconstructed here |
| `BEE_DoReorderIndexedGroupTask` | 73 | 74 | Not reconstructed here |

The native command table gives their names. **Independent MSVC RTTI and C++ vtable decoding** establish the concrete Add/Remove task identities.

## Verified inverse-operation relationship

```text
Remove task.execute()  [C++ vtable +0x08]
  → native Indexed Group removal
  → construct new Add task
  → copy StreamIDPath and detached native child reference
  → set Add task's Stream ownership flag
  → return Add task to Undo/Redo history machinery

Add task.execute()     [C++ vtable +0x08]
  → native Indexed Group insertion
  → construct new Remove task
  → return Remove task to Undo/Redo history machinery
```

The identity of each returned task is verified from the instruction that writes the **other task class's precise vtable address** into the newly constructed object; this is not a deduction from function names alone.

## Who deletes the detached Stream?

The Add task holds a native Stream pointer at **`task+0x40`** in both releases. A separate ownership flag moves between versions:

| Private member | AE2025 | AE2026 |
| --- | ---: | ---: |
| Native Stream pointer | `+0x40` | `+0x40` |
| Owns-Stream flag | `+0x48` | `+0x50` |
| Add task allocation size | `0x50` bytes | `0x58` bytes |

The Remove task's execute path sets the returned Add task's ownership flag to **1**. That Add task's **virtual deleting destructor** checks the flag and pointer, checks `TDB_StreamBase::IsCanonical`, and **only for the eligible noncanonical Stream**:

```text
AddTask.deletingDestructor(deleteFlag)
  if ownsStream && Stream != null:
    if !Stream.IsCanonical():
      parent = Stream.GetParent()
      if parent != null:
        parent.virtualRemoveChild(Stream)  [parent vtable +0x1E0]
        // host assertion/error path if removal fails
      Stream.virtualDeletingDestructor(1) [Stream vtable +0x00]

  destruct embedded TDB_StreamIDPath
  destruct BEE base members
  if requested: free native Add task allocation
```

This is the missing connection between the **BEE Undo task destructor** and the **actual TDB Stream virtual destructor**. The code also contains branches that do not delete the Stream, and host assertion paths; neither every branch nor all failure recovery is qualified.

## From document edit to history clearance

```text
BEE indexed-property command
    → BEE_DoRemoveIndexedGroupTask
    → inverse BEE_DoAddToIndexedStreamGroupTask
         └─ owns detached native Stream when flagged
    → BEE Undo/Redo TaskStack
    → BEE_UndoContext ClearUndo/ClearRedo/destructor
    → history task virtual deleting destructor
    → eligible owned Add task's Stream virtual deleting destructor
```

**Important:** clearing a generic BEE task destroys the task, but the underlying Stream is destroyed only when the *concrete Add task's* ownership and canonical guards allow it. This distinction is essential for safe unloading of any hypothetical Stream-provider DLL.

## Versioned machine-code anchors

| Verified native item | AE2025 BEE RVA | AE2026 RVA |
| --- | --- | --- |
| Add task C++ vtable | `0xF914B8` | `0xFF0860` |
| Remove task C++ vtable | `0xF914D8` | `0xFF0880` |
| Add task execute | `0x54C640` | `0x56B270` |
| Remove task execute | `0x54CF00` | `0x56BC10` |
| Add task deleting destructor | `0x549C90` | `0x568A30` |
| Remove task deleting destructor | `0x549EE0` | `0x568CB0` |
| Add writes inverse Remove task vtable | `0x54C978` | `0x56B5BD` |
| Remove writes inverse Add task vtable | `0x54D27D` | `0x56BFAB` |
| Remove sets returned Add task owner flag | `0x54D287` | `0x56BFB5` |
| Add destructor invokes eligible Stream virtual delete | `0x549DE7` | `0x568B84` |

These are **not portable ABI declarations**. Every address and conditional branch is verified by original PE disassembly and cross-checked against the binary SHA.

## Remaining native extension gates

This does **not** prove a foreign `CNL:` Stream can be registered, admitted to Adobe's canonical parent grammar, edited natively, serialized, rendered, or safely unloaded. The discovered task system demonstrates precisely *why* factory unregister alone cannot imply no remaining callbacks into a foreign Stream implementation. macOS native BEE/TDB ownership remains unverified.

To reproduce, run `experiments/vector-shape/probe-src/tools/verify_bee_indexed_task_inverse_and_stream_lifetime.py` on the authorized installed Windows binaries. The strict verifier produced **PASS for AE2025 and AE2026**, with no Adobe code loaded or invoked.

Evidence: [Undo Task Lifecycle](undo-task-lifecycle.md), [Structural Command Submission](structural-command-undo.md), [Indexed Removal](indexed-group-removal.md), [Factory Lifetime](factory-registration-lifetime.md), F-VECTOR-099/101/102 and `datasets/ae-bee-indexed-add-remove-reciprocal-stream-ownership-2025-2026.json`.
