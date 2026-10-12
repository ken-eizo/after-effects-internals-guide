---
status: cross-version-native-binary-verified
date: 2026-10-12
evidence: E2-L pinned installed AE2025/AE2026 BEE.dll native C++ constructor code
---

# F-VECTOR-055 — Typed BEE_VectorLayer creator constructs with null Comp owner; stock Shape factory binds real BEE_CompItem

## Why this matters for a truly independent CNL vector owner

F-VECTOR-054 recovered the full Adobe native Shape hierarchy and `BEE_VectorLayer::Create` as one of 183 TDB Creator registration sites. **It would be wrong to conclude that registering that factory means a new custom vector layer can appear in the Timeline.** We now compared two different code paths that invoke the exact **same** `BEE_VectorLayer` constructor.

### Path A: TDB-owned typed stream creation, detached

- AE2025: `BEE_VectorLayer::Create` RVA **`0xB0970`**, allocates **`0x2820`** bytes, calls native `BEE_VectorLayer` ctor at RVA `0x6E1050`.
- AE2026: creator RVA **`0xB64E0`**, allocates **`0x2830`** bytes, calls ctor RVA `0x7058E0`.
- In *both* compiled Creator function bodies, the critical instruction immediately before the ctor call is **`xor r9d,r9d`**. The MSVC x64 constructor signature exposes the fourth argument as `BEE_CompItem*`. This passes a null owning CompItem; the factory function returns a `TDB_StreamBase*`.
- Another explicit stack argument is `mov byte ptr [rsp+0x20],1`. The boolean's full downstream semantics remain unanalyzed; do not infer attached/lifetime semantics from it.

**Consequence:** the registered TDB type Creator produces a `BEE_VectorLayer` object **without supplying the owning CompItem**. It may later be attached by a separate internal step; this code alone does not create a visible independently selectable Timeline layer.

### Path B: ordinary native layer creation, comp-bound

- AE2025: `BEE_Layer::CreateLayerFromType(int,BEE_CompItem*,unsigned char)` RVA `0x2E3E10`.
- AE2026: same method RVA `0x2ECD00`.
- In both, the native second parameter (`RDX`) is the `BEE_CompItem*`. The compiled entry preserves it as **RSI** (2025) or **RBX** (2026).
- For the fixed native Shape kind **4**, the function calls the **same concrete ctor** as the typed factory; immediately before the call it places the saved CompItem back into **R9** (`mov r9,rsi` or `mov r9,rbx`).
- The function first bounds-checks layer type against **7** and dispatches through the closed eight-way jump table (F-VECTOR-037), rather than dispatching custom user MatchNames to Layer Creators.

### Decisive architectural distinction

The native code provides **two different creation semantics** for the same concrete Shape class:

```text
TDB_StreamFactory typed callback:
  BEE_VectorLayer::Create(name, stream_factory, ...)
    → BEE_VectorLayer constructor(..., BEE_CompItem* = nullptr, ...)
    → returns a TDB_StreamBase* (not proof of comp admission)

Normal AE Shape Layer creation:
  BEE_Layer::CreateLayerFromType(4, BEE_CompItem*, flags)
    → BEE_VectorLayer constructor(..., BEE_CompItem* = actual comp, ...)
    → participates in built-in native layer creation path
```

**A new independent CNL layer requires the missing attachment/admission machinery.** `BEE_Layer::SetParentComp(BEE_CompItem*)` and `GetParentComp` are real exported native symbols in both builds, but their presence **does not prove** that calling the setter inserts a layer into the comp's layer list, creates an Undo transaction, assigns stable Layer IDs, installs editor selection handlers, or enables RG rendering. They are candidate research leads only.

The next real research gate is to discover the full **native CompItem/LayerSet insertion and teardown path**, and distinguish it from setting a raw parent pointer. Even safe and successful external TDB+evaluator registration would not bypass this owner gate.

## Real-world standing

- The user's normal **CNL Owned Vector Document (Research)** effect renders its Bezier path and survives project reopen in AE2026; this is a real effect archive/render proof, **not** this new native owner.
- True foreign `BEE_VectorLayer`, independent plugin Contents, native Pen editor, BEE_VectorArt RG output: **not yet implemented or host-tested**.
- No private BEE/TDB functions executed, no AE GUI install, no Adobe DLL modified, no `CompNodeAE` modification or Phase F integration.

## Reproduce

`experiments/vector-shape/probe-src/tools/audit_native_vector_owner_factory_vs_layer_dispatch.py` disassembles and symbolically resolves the three real native exported functions; `trace_native_vector_owner_stock_vs_tdb_creator.py` inspects the exact CompItem argument at the ctor call; `verify_native_vector_detached_factory_vs_comp_owner.py` asserts the null-vs-real CompItem distinction and matching ctor symbol for both pinned DLLs.

Receipts:
- `datasets/ae-bee-vector-owner-factory-vs-layer-dispatch-2025-2026.json`
- `datasets/ae-bee-vector-owner-stock-comp-ctor-2025-2026.json`
- `datasets/ae-bee-vector-factory-comp-owner-verification-2025-2026.json`

These are **static host-binary proofs**, not a demonstration that a third party can construct and attach any Adobe-native layer.
