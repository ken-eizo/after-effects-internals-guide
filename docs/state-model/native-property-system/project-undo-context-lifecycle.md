---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E2-L + H
versions: Original installed Windows AE2025/AE2026 BEE.dll
---

# BEE_Project and UndoContext — Ownership, Accessors and Destruction

Native After Effects Timeline property edits are enrolled in the BEE command system through a **project-associated UndoContext**. The underlying Undo/Redo histories are not independent per Layer or per Item; native `BEE_Layer` and `BEE_Item` accessors resolve the current **`BEE_Project` UndoContext**.

This page describes **Adobe's internal C++ implementation**. These classes, pointers and offsets are not public After Effects SDK extension points.

## Ownership and accessor hierarchy

```text
BEE_Layer::GetUndoContext()
  ├─ find the Layer's BEE_Item
  ├─ find that Item's parent BEE_Project
  └─ BEE_Project::GetUndoContext()

BEE_Item::GetUndoContext()
  └─ BEE_Project::GetUndoContext(Item.parentProject)

BEE_Project::GetUndoContext()
  └─ return *(Project + contextHolderOffset) + 0x10
```

For the Layer overload, the native implementation checks both the Item and Project pointer and takes a host error/verification path when either is null. It does **not** silently fall back to a separate Layer-owned UndoContext.

### Native object layout (version-specific)

| Observed member/access path | AE2025 | AE2026 |
| --- | --- | --- |
| `BEE_Item` parent Project pointer | `+0x38` | `+0x38` |
| `BEE_Layer` linked Item pointer | `+0x2B8` | `+0x260` |
| `BEE_Project` pointer to context-holder allocation | `+0x368` | `+0x370` |
| `BEE_UndoContext` subobject inside context holder | `+0x10` | `+0x10` |
| Missing-font vector start / end / capacity within holder | `+0x118 / +0x120 / +0x128` | `+0x118 / +0x120 / +0x128` |
| Context-holder allocated size released by Project destructor | `0x130` bytes | `0x130` bytes |

Only the named releases and exact original binaries are qualified. In particular, **the Layer-linked Item offset changes sharply between the two versions**, showing why a plugin must not hard-code this private layout.

## Project-level teardown and task destruction

The native `BEE_Project::~BEE_Project` destructor reads the context-holder pointer, checks it for null, **destroys the native missing-font `TXT_UsedFontData` vector at holder `+0x118`**, then explicitly calls **`BEE_UndoContext::~BEE_UndoContext(contextHolder+0x10)`**, and finally releases the containing `0x130`-byte allocation. The vector identity, its `0x88`-byte element stride and the matching writer `BEE_Project::AddMissingFont` were independently established in F-VECTOR-104.

```text
BEE_Project::~BEE_Project
  └─ context-holder exists?
       ├─ destroy each TXT_UsedFontData in holder vector [+0x118]
       ├─ recycle font-vector backing storage
       ├─ BEE_UndoContext::~BEE_UndoContext [+0x10]
       │    ├─ destroy Undo TaskStack entries
       │    └─ destroy Redo TaskStack entries
       └─ deallocate context holder [size 0x130]
```

The **exact UndoContext subobject** in the getter is the one passed to the destructor. This is confirmed in both compiled Adobe versions.

[Undo Task Lifecycle](undo-task-lifecycle.md) establishes that history cleanup invokes the **task object's virtual deleting destructor**, while [Indexed Add/Remove Task Ownership](indexed-property-undo-task-ownership.md) shows that the concrete inverse-Add task conditionally owns a native TDB Stream and can invoke the Stream's virtual deleting destructor.

Therefore, an actual **Project → UndoContext → history task → eligible native Stream** destruction path exists in the built-in host implementation. This is a **conditional static call chain**, not a guarantee that every Stream is destroyed this way or that every project-close runtime operation follows the same branch.

## Important entry-point locations

| Internal method/callsite | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| Project `GetUndoContext` | `0x407390` | `0x417630` |
| Item `GetUndoContext` | `0x3C9C70` | `0x3D7A00` |
| Layer `GetUndoContext` | `0x2EA2B0` | `0x2F2E60` |
| Project destructor | `0x3FF0C0` | `0x40F330` |
| Direct Project-to-UndoContext destructor callsite | `0x3FF44A` | `0x40F68A` |
| UndoContext destructor | `0x67FBC0` | `0x69BF90` |

These are **RVAs of original installed Windows files**, not portable addresses and not public SDK declarations.

## Implications for native type providers and module lifetime

A Creator registered in `TDB_StreamFactory` is not the only potential owner of a custom native object. Even after a property is deleted from its Timeline group, the Undo/Redo history associated with its Project can retain a task referencing the detached Stream. Project destruction is one of the host lifetime boundaries that may trigger the task's and the Stream's virtual destructor.

A hypothetical foreign native Stream-provider DLL therefore needs proof that **no live authored instance, canonical prototype, detached Stream or Undo/Redo task references code in the module** before it is unloaded. Merely calling a factory unregister method does not establish that invariant.

No supported public Adobe 25.6 SDK registration method for arbitrary new `TDB_StreamBase` subclasses has been found; this mechanism is **not a supported external implementation recipe**.

## Limits and proof

This chapter is based on read-only x64 disassembly of installed AE2025/AE2026 `BEE.dll` with SHA-pinned original images. It includes neither a live project-close experiment nor a foreign custom native Stream registration. F-VECTOR-104 **resolves** the helper at context holder `+0x118` as destruction of missing-font `TXT_UsedFontData` records before UndoContext teardown. Exception rollback, true cross-thread lifetime and macOS C++ ABI remain unknown.

To reproduce:

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_bee_project_undo_context_getter_delegation.py"
```

Evidence: F-VECTOR-103/104, `datasets/ae-bee-project-undo-context-getter-delegation-2025-2026.json` and `datasets/ae-bee-project-font-vector-pre-undo-shutdown-2025-2026.json`. See [Project Missing-Font Metadata Lifecycle](../../text-system/project-missing-font-data-lifecycle.md). Related feature pages: [Structural Commands and Undo](structural-command-undo.md), [Undo Task Lifecycle](undo-task-lifecycle.md), [Indexed Group Removal](indexed-group-removal.md), [Stream Object Model](stream-object-model.md), and [Startup to Shutdown](startup-to-shutdown.md).
