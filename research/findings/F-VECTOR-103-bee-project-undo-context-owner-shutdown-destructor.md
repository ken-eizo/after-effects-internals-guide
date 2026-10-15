---
date: 2026-10-15
status: PASS original Windows AE2025 and AE2026 BEE.dll strict SHA-pinned native Project/Item/Layer UndoContext accessor plus Project destructor static proof
evidence: E2-L original x64 exported methods, bounded disassembly, direct cross-class callsites, exact object offsets; no Adobe private runtime calls
---

# F-VECTOR-103 — Project-level UndoContext acquisition and destruction closes the native Stream lifetime chain

## Main finding

Real first-party `BEE_Layer`, `BEE_Item` and `BEE_Project` do not maintain three separate unrelated Undo histories. The original Windows AE2025/AE2026 binary getters converge on a **Project-accessible `BEE_UndoContext`**.

More importantly, the real **`BEE_Project::~BEE_Project` calls `BEE_UndoContext::~BEE_UndoContext` directly** for the same native context subobject returned from the Project getter, and only afterward releases the containing `0x130`-byte allocation. This gives a verified project-destruction boundary for the generic history cleanup discovered in F-VECTOR-101 and the conditional native Stream deleting-destructor discovered in F-VECTOR-102.

### Real getters

```text
BEE_Item::GetUndoContext()
  ├─ project = *(BEE_Item + 0x38)
  └─ tailcall BEE_Project::GetUndoContext(project)

BEE_Layer::GetUndoContext()
  ├─ item = *(BEE_Layer + version-dependent offset)
  ├─ if null: native verification/error branch
  ├─ BEE_Item::GetParentProject(item)
  ├─ if null: native verification/error branch
  └─ tailcall BEE_Project::GetUndoContext(project)

BEE_Project::GetUndoContext()
  ├─ containing_context = *(BEE_Project + version-dependent offset)
  └─ return containing_context + 0x10
```

Mutable/const overloads were independently inspected and route to the same project context. In these two builds, the const Layer getter also tailcalls the *mutable* Project getter. This is a compiled implementation observation, not a recommendation to use non-const private interfaces.

### Actual Project destructor

```text
BEE_Project::~BEE_Project()
  ├─ ... earlier native project cleanup ...
  ├─ context_owner = *(project + 0x368 [2025] / 0x370 [2026])
  ├─ if context_owner != null:
  │    ├─ call separate helper on context_owner + 0x118 [semantics not established]
  │    ├─ call BEE_UndoContext::~BEE_UndoContext(context_owner + 0x10)
  │    │    ├─ clear Undo TaskStack and delete task objects [F-VECTOR-101]
  │    │    └─ clear Redo TaskStack and delete task objects [F-VECTOR-101]
  │    └─ release context_owner allocation, size 0x130
  └─ ... subsequent native Project members cleanup ...
```

The **exact +0x10 subobject offset** is identical in the Project accessor and destructor; the destructor's direct call target is the exported `BEE_UndoContext::~BEE_UndoContext` method. This is materially stronger than inferring ownership from a method name.

## The scoped project-to-Stream destruction chain

```text
BEE_Project native destructor
 → embedded/indirectly allocated BEE_UndoContext destructor
 → native Undo/Redo TaskStack cleanup
 → history task vtable[0] deleting destructor (for non-null task entries)
 → BEE_DoAddToIndexedStreamGroupTask deleting destructor (when that task owns entry)
 → if owns native noncanonical Stream:
      → optionally detach from parent
      → native Stream's own vtable[0] deleting destructor
```

The **individual calls are statically verified** in the two installed Adobe binaries and the verified generic/concrete helpers. This does **not** mean every Project contains an owning inverse-Add task, or that every task's full lifetime follows one success branch. No user AEP was closed under a debugger, and failure/exception/unload behavior remains unverified.

## Exact private offsets and native code anchors

| Internal implementation evidence | AE2025 BEE.dll | AE2026 BEE.dll |
| --- | --- | --- |
| `BEE_Project::GetUndoContext` | RVA `0x407390` | `0x417630` |
| Project context-holder pointer | Project `+0x368` | `+0x370` |
| `BEE_UndoContext` within holder | holder `+0x10` | `+0x10` |
| `BEE_Item::GetUndoContext` | RVA `0x3C9C70` | `0x3D7A00` |
| Item parent Project field | Item `+0x38` | `+0x38` |
| `BEE_Layer::GetUndoContext` | RVA `0x2EA2B0` | `0x2F2E60` |
| Layer's Item link field | Layer `+0x2B8` | `+0x260` |
| `BEE_Item::GetParentProject` | RVA `0x3C9860` | `0x3D76A0` |
| `BEE_Project::~BEE_Project` | RVA `0x3FF0C0` | `0x40F330` |
| Project destructor loads context-holder | `0x3FF42E` | `0x40F66E` |
| Direct Project → UndoContext destructor call | `0x3FF44A` | `0x40F68A` |
| `BEE_UndoContext::~BEE_UndoContext` | RVA `0x67FBC0` | `0x69BF90` |
| Context-holder allocation size on release | `0x130` | `0x130` |

Object offsets and RVAs are valid **only for the exact observed private implementations**. In particular, note that the Layer's Item pointer moves significantly between builds.

## What this does and does not establish

**Proven (E2-L):** Project-accessed UndoContext for Layers and Items, real Project destructor's direct UndoContext destructor call, UndoContext's two history-stack cleanup calls (F-VECTOR-101) and eligible concrete Add-task-to-Stream destruction (F-VECTOR-102).

**Not proven:** that a third-party C++ Stream class may be registered in Adobe's native factory; arbitrary class compatibility with BEE undo tasks; correct failure unwind; plugin module unload ordering relative to surviving Stream vtables; a real malformed AEP or foreign AEP save/reopen; macOS native ABI; behavior of the other project-context helper at `+0x118`.

This is **not** a public SDK registration interface, and the native `BEE_Project` is not a replacement for an `AEGP_ProjectH`.

## Reproducible experiment

Execute the SHA-pinned cross-version verifier:

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_bee_project_undo_context_getter_delegation.py"
```

Machine-readable receipt: `datasets/ae-bee-project-undo-context-getter-delegation-2025-2026.json`.

**Subsequent refinement (F-VECTOR-104, 2026-10-15):** The previously unidentified Project context-holder `+0x118` helper is now independently verified as `TXT_UsedFontData` missing-font vector destruction. `BEE_Project::AddMissingFont` writes to that same vector, and the Project destructor disposes it before `BEE_UndoContext`. The original F-VECTOR-103 scope was correct but its `+0x118` helper's semantics are no longer unknown.

Related first-party internal proof: F-VECTOR-099 (native detach and command entry), F-VECTOR-101 (task replay and TaskStack destruction), F-VECTOR-102 (concrete Add/Remove inverse task Stream ownership), F-VECTOR-104 (font metadata lifecycle). Feature page: `docs/state-model/native-property-system/project-undo-context-lifecycle.md`.
