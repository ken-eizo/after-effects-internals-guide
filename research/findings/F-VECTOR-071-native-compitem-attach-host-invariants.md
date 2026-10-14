---
date: 2026-10-14
status: PASS pinned AE2025/2026 native CompItem attachment contract; foreign layer admission UNPROVEN
evidence: E2-L exact installed Adobe BEE.dll PE instructions, SHA-256 gated offline verifier
---
# F-VECTOR-071 — Native CompItem layer attachment requires host-specific object and vtable contracts

## Why this matters

F-VECTOR-037 established that the stock `BEE_Layer::CreateLayerFromType` is a closed eight-kind constructor. F-VECTOR-067/068 located a distinct generic-looking path, `BEE_Layer::CloneAndAttach`: TDB native Clone, C++ RTTI cast to BEE_Layer, and eventual CompItem attachment. An externally constructed subclass, even if its RTTI were valid, would still need to survive the actual native `BEE_CompItem::AttachLayerToCompOnly` logic. That logic has now been independently disassembled for two pinned AE versions.

## Actual compiled method and byte-level evidence

| Feature | AE 2025 | AE 2026 |
| --- | --- | --- |
| Native BEE.dll SHA-256 | `98c682351e30f38cb7021eaa142f5ec473aea92885e14915d87c157cda971730` | `5fd8d318456228b9fd2a6733a5758f6b84206b7a8effcba5202957cd27ac680e` |
| `BEE_CompItem::AttachLayerToCompOnly` RVA | `0x392120` | `0x39D4D0` |
| Function extent from x64 unwind (.pdata) | `[0x392120,0x3922EB)` | `[0x39D4D0,0x39D684)` |
| Layer object's 32-bit field read | `mov ebp, dword ptr [rbx + 0x2d8]` | `mov ebp, dword ptr [rbx + 0x26c]` |
| Four identical-slot virtual dispatches | `call qword ptr [rax + 0x278]` | `call qword ptr [rax + 0x278]` |
| Another per-layer virtual dispatch | `call qword ptr [rax + 0x550]` | `call qword ptr [rax + 0x560]` |
| Conditional CompItem integer increment | `inc dword ptr [rsi + 0x3c8]` | `inc dword ptr [rsi + 0x420]` |

Here `rbx` is populated from the second Windows x64 argument (`rdx`, a `BEE_Layer*`) and `rsi` from the first (`rcx`, the `BEE_CompItem*`) in BOTH inspected functions. The Layer field is read and passed to subsequent native calls; its *exact semantic name* is NOT established by these instructions. The four calls through vtable slot +0x278 are preceded by distinct integer arguments 2, 1, 5 and 7, with conditional branching on return values. Their enum/capability meaning remains unresolved. The second virtual dispatch uses slot +0x550 or +0x560 after additional native calls. It is NOT yet identified as a particular named virtual method.

The function also performs null checks, invokes multiple other native host functions, conditionally updates CompItem state, and releases a temporary object using atomic counters and virtual dispatch. Thus the attachment cannot be safely modeled as merely appending a `BEE_Layer*` to a collection. The observed field offsets and one vtable index differ across the two real host versions. These new differences independently corroborate F-VECTOR-070's ABI-drift finding.

## Consequence and limits

A hypothetical foreign `BEE_Layer` would have to supply more than an MSVC RTTI-compatible inheritance path: it would also need correct version-specific object layout, virtual behavior, host references/state transitions, lifetime semantics, native serialization and unload safety. The evidence does NOT prove that an externally defined BEE subclass can ever be registered, constructed, attached or used in the unmodified Adobe host. Conversely, this bounded analysis does NOT prove that no alternative extension route exists.

In particular, direct generic-looking `CloneAndAttach` and internal `AttachLayerToCompOnly` are not public AEGP extension APIs. No private function may be called or injected into the user's running After Effects from this work. `CNLPrivateTDBDisposable.aex` remains prohibited for normal-host execution.

## Reproduction

Read-only Python tools and evidence in AEIG:
- `experiments/vector-shape/probe-src/tools/audit_compitem_native_attach_contract.py`
- `experiments/vector-shape/probe-src/tools/verify_compitem_native_attach_contract.py`
- `datasets/ae-bee-compitem-attach-owner-contract-2025-2026.json`

The original local work area is `D:/Developer/ShapeLayerAE/labs/native_owner_attach_audit/`. The offline verifier ran against both pinned installed Adobe BEE binaries, **2/2 PASS**. The audit does not execute AE, load Adobe DLLs, invoke private native APIs or change user projects.

## Highest-priority next research

1. Determine if any genuinely host-approved independent Layer subclass/owner registration or provider mechanism exists outside the closed eight-way constructor. Do not infer extensibility from exported C++ symbol visibility.
2. Identify the virtual methods at +0x278 and +0x550/+0x560 through actual version-specific RTTI/vtable evidence and their responsibility for attach-time state; document uncertainty.
3. Reconstruct actual object initialization, CompItem bookkeeping, teardown, save/reopen and TDB ownership before considering any host test.
4. Treat inability to discover a safe external registration route as a **bounded negative result**, not a claim of global impossibility.

CompNodeAE, other agents' AEIG files, Adobe binaries and the running AE GUI were not modified.
