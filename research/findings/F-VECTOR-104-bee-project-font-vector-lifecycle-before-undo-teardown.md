---
date: 2026-10-15
status: PASS SHA-pinned AE2025 / AE2026 BEE.dll static original Win64 native AddMissingFont and Project teardown
evidence: E2-L cross-DLL TXT.dll constructor/destructor IAT, original C++ project methods, explicit object and subobject offsets, machine-code call order
---

# F-VECTOR-104 — Project missing-font vector lifecycle and teardown order relative to UndoContext

## What changed

F-VECTOR-103 established that a native `BEE_Project` owns an indirect `BEE_UndoContext`, and that the Project destructor calls `BEE_UndoContext::~BEE_UndoContext` before releasing its containing allocation. However, **a native helper called on the same holder at `+0x118`, immediately before the UndoContext destructor, was still unidentified**.

Original installed AE2025 and AE2026 `BEE.dll` code now establishes **both ends of the member's lifecycle**:

1. `BEE_Project::AddMissingFont(const TXT_UsedFontData&)` **appends a native `TXT_UsedFontData` value** into a vector-like three-pointer structure at **the same Project context holder `+0x118`**.
2. If the buffer is full, it tail-jumps to a vector growth helper; the helper invokes native memory allocation, `TXT_UsedFontData` copy and move constructors, destructors for old elements, and backing-memory recycling.
3. At Project destruction, the previously anonymous helper called on holder `+0x118` iterates the live entries, invokes **`TXT.dll!TXT_UsedFontData::~TXT_UsedFontData`**, recycles the backing allocation, and zeros vector start/end/capacity.
4. The Project destructor **then** invokes `BEE_UndoContext::~BEE_UndoContext` on the holder's distinct `+0x10` subobject, and only then frees the `0x130`-byte holder allocation.
5. `BEE_ExpressionEngine` destruction follows that holder release in the examined Project destructor.

This identifies the helper as **missing-font metadata vector cleanup**, not another UndoContext, callback table or second Undo-history system. It also establishes a versioned native teardown order among different Project-owned subsystems.

## Object layout — identical semantics across both versions

```text
BEE_Project
   └─ pointer at Project +0x368 [AE2025] or +0x370 [AE2026]
       └─ Project context holder (0x130 bytes)
           ├─ +0x10 : BEE_UndoContext native subobject
           └─ +0x118: TXT_UsedFontData vector state
                        +0x118 : begin
                        +0x120 : end
                        +0x128 : capacity
```

`TXT_UsedFontData` vector stride is `0x88` bytes (**136 bytes**). The precise private structure is established from *both* AddMissingFont and cleanup machine instructions. It is not a public SDK ABI.

### Normal append versus growth

```text
BEE_Project::AddMissingFont(const TXT_UsedFontData& value)
  ├─ holder = *(Project + holderOffset)
  ├─ end = *(holder +0x120)
  ├─ if end != *(holder +0x128):
  │     ├─ TXT_UsedFontData::TXT_UsedFontData(end, value) [copy constructor]
  │     └─ end += 0x88
  └─ otherwise:
        └─ vector growth helper(holder+0x118, value)
             ├─ MemoryRecycler::Allocate(new capacity)
             ├─ TXT_UsedFontData copy and move constructors
             ├─ TXT_UsedFontData destructors for transferred originals
             └─ MemoryRecycler::Recycle(old allocation)
```

The growth helper's complete exception and allocator error behavior remains unverified; the listed successful call order is machine-code-supported.

### Project teardown

```text
BEE_Project::~BEE_Project
  ├─ earlier native Project members and lock cleanup
  ├─ if context holder exists:
  │    ├─ destroy each native TXT_UsedFontData at holder+0x118
  │    ├─ recycle missing-font vector allocation
  │    ├─ reset vector begin/end/capacity
  │    ├─ BEE_UndoContext::~BEE_UndoContext(holder+0x10)
  │    │    ├─ clear Undo TaskStack
  │    │    └─ clear Redo TaskStack
  │    └─ release holder's 0x130-byte allocation
  └─ destroy BEE_ExpressionEngine subobjects later in this destructor
```

The TaskStack-to-owned-native-Stream virtual destructor chain is **conditional** and separately evidenced in F-VECTOR-101/102. This finding does not establish whether any specific Undo task calls back into TXT font data after the vector has been destroyed, nor does it assert that such a callback occurs.

## Original code anchors

| Internal operation | AE2025 RVA | AE2026 RVA |
| --- | ---: | ---: |
| `BEE_Project::AddMissingFont` | `0x4018F0` | `0x411D50` |
| In-place `TXT_UsedFontData` copy ctor | `0x401910` | `0x411D70` |
| In-place vector end advances `+0x88` | `0x401916` | `0x411D76` |
| Vector growth fallback | `0x3FAB60` | `0x40A9E0` |
| Growth calls native Allocate | `0x3FAC32` | `0x40AAB9` |
| Growth calls native TXT copy ctor | `0x3FAC64` | `0x40AAF2` |
| Growth calls native TXT move ctor | `0x3FAC96` | `0x40AB26` |
| Growth recycles old allocation | `0x3FAD71` | `0x40AC01` |
| Project `TXT_UsedFontData` vector cleanup helper | `0x3FEFF0` | `0x40F260` |
| Cleanup calls native TXT destructor | `0x3FF016` | `0x40F286` |
| Cleanup recycles vector allocation | `0x3FF054` | `0x40F2C4` |
| Project calls font-vector cleanup | `0x3FF441` | `0x40F681` |
| Project calls UndoContext destructor | `0x3FF44A` | `0x40F68A` |

Both DLL hashes, complete callsite probes and exact vector member fields are recorded in the independent verifier receipt.

## What this means for native Stream extension research

The real Project UndoContext is not a standalone reference-counted object unconnected to other Project members. It exists **inside the same allocation as the native missing-font metadata vector** and the Project destructor explicitly sequences their teardown. Therefore, any future hypothesis about a foreign native Stream callback during Project shutdown must account for **cross-subsystem destruction order** rather than assuming the environment remains fully alive while Undo-owned Streams are deleted.

**Not proven:** complete Project destruction order for every member; whether any Undo task touches TXT fonts; thread-safety; successful foreign native type registration; safe external DLL unload; a live foreign AEP save/reopen; macOS ABI. These are private first-party implementation details.

## Reproduction and incorporation

Run `experiments/vector-shape/probe-src/tools/verify_bee_project_font_vector_pre_undo_teardown.py`; it pins each original Windows AE2025/AE2026 `BEE.dll` SHA and validates the writer, vector grow, imported TXT constructors, cleanup, Undo destructor, and expression engine ordering. No Adobe library function is executed.

Receipt: `datasets/ae-bee-project-font-vector-pre-undo-shutdown-2025-2026.json`.

Feature pages: `docs/text-system/project-missing-font-data-lifecycle.md` and `docs/state-model/native-property-system/project-undo-context-lifecycle.md`. Earlier evidence: F-VECTOR-101, F-VECTOR-102 and F-VECTOR-103.
