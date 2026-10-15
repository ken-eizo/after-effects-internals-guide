---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E2-L + H
versions: Original installed Windows AE2025 / AE2026 native BEE and TXT DLL imports
---

# BEE_Project::AddMissingFont — Native Font Metadata Ownership and Cleanup

The real `BEE_Project` maintains a private array of `TXT_UsedFontData` records for **missing-font metadata**. The array is stored in the same indirectly allocated Project holder that contains its Undo/Redo command context. This is **Adobe internal C++ implementation**, not a supported After Effects SDK API or a public font-list format.

## Native responsibilities

| Function | Owner | Verified responsibility |
| --- | --- | --- |
| `BEE_Project::AddMissingFont` | `BEE.dll` | Copy a `TXT_UsedFontData` into a Project-associated growing vector |
| `TXT_UsedFontData` copy/move constructors | `TXT.dll` | Construct copied/moved records in normal and reallocation paths |
| Native vector growth helper | `BEE.dll` | Allocate, relocate records, destroy transferred originals, recycle storage |
| Project font-vector cleanup helper | `BEE.dll` | Call `TXT_UsedFontData` destructor for live records, release buffer and zero vector state |
| `BEE_UndoContext::~BEE_UndoContext` | `BEE.dll` | Destroy Undo/Redo history tasks **after** missing-font vector cleanup |

## Internal Project holder layout

```text
BEE_Project
  +0x368 [AE2025] / +0x370 [AE2026] → holder pointer
                                        holder size 0x130
                                        +0x10  native BEE_UndoContext
                                        +0x118 vector begin (TXT_UsedFontData*)
                                        +0x120 vector end
                                        +0x128 vector allocation end
```

Each native `TXT_UsedFontData` record occupies **`0x88` bytes (136 bytes)** in the examined host build, as verified from both append and cleanup loops.

The `TXT.dll` exports also contain getters named `GetFamily`, `GetFullName`, `GetID`, `GetPostScriptName`, and `GetStyle`. These export names indicate the record's font-related responsibilities, but we have **not** reconstructed its complete memory layout or a public serialization contract from them.

## Insertion and capacity growth

```text
BEE_Project::AddMissingFont(const TXT_UsedFontData& record)
  ├─ get holder from Project
  ├─ if end != capacity:
  │    ├─ TXT_UsedFontData copy-construct at end
  │    └─ increment end pointer by 0x88
  └─ else:
       └─ grow vector at holder+0x118
            ├─ MemoryRecycler Allocate
            ├─ TXT_UsedFontData copy and move constructors
            ├─ destroy old records
            └─ MemoryRecycler Recycle
```

The normal branch copies **one** record and advances the end pointer. The growth branch's machine code calls native copy/move constructors and releases the old allocation. Exception paths and missing-font uniqueness/deduplication policies have not been established.

## Project shutdown and Undo ordering

```text
BEE_Project::~BEE_Project
  ├─ cleanup(holder+0x118)
  │    ├─ TXT_UsedFontData destructor per element
  │    ├─ MemoryRecycler Recycle
  │    └─ reset vector start/end/capacity
  ├─ BEE_UndoContext destructor(holder+0x10)
  │    ├─ Undo TaskStack cleanup
  │    └─ Redo TaskStack cleanup
  ├─ release holder allocation (0x130 bytes)
  └─ continue Project members, including BEE_ExpressionEngine destructors
```

This ordering is statically confirmed in original AE2025 and AE2026 native code. It matters for object lifetime reasoning, **but it does not prove that any Undo task accesses destroyed font metadata or that a use-after-free occurs**.

## Versioned code locations

| Operation | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| `BEE_Project::AddMissingFont` | `0x4018F0` | `0x411D50` |
| Normal copy constructor call | `0x401910` | `0x411D70` |
| Vector growth helper | `0x3FAB60` | `0x40A9E0` |
| Project cleanup helper | `0x3FEFF0` | `0x40F260` |
| Cleanup `TXT_UsedFontData` destructor call | `0x3FF016` | `0x40F286` |
| Project calls font cleanup | `0x3FF441` | `0x40F681` |
| Project calls UndoContext destructor | `0x3FF44A` | `0x40F68A` |

All addresses are RVAs specific to pinned original builds, **not callable SDK addresses**.

## Related documentation and evidence

[Project UndoContext Lifetime](../state-model/native-property-system/project-undo-context-lifecycle.md) describes the neighboring UndoContext subobject and how real Layer/Item edit commands acquire it. [BEE Undo Task Lifecycle](../state-model/native-property-system/undo-task-lifecycle.md) and [Indexed Property Undo Task Ownership](../state-model/native-property-system/indexed-property-undo-task-ownership.md) trace the subsequent task/Stream destruction chain.

F-VECTOR-104 contains the full machine-code research receipt. Independently verify with `experiments/vector-shape/probe-src/tools/verify_bee_project_font_vector_pre_undo_teardown.py`; its dataset is `datasets/ae-bee-project-font-vector-pre-undo-shutdown-2025-2026.json`.

**Scope:** read-only static x64 analysis, no Adobe private runtime API call, no live project-close test, no third-party native Stream registered.
