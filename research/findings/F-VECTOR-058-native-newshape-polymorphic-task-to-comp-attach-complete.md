---
status: PASS-both-installed-BEE-native-dispatch-to-comp-attach-full-static-chain
date: 2026-10-12
evidence: E2-L on-disk AE2025/AE2026 exact PE, actual native x64 instruction and MSVC RTTI/vtable
---

# F-VECTOR-058 — New Shape Layer native command-to-Comp attachment full C++ virtual dispatch bridge

## The previously missing architectural edge is resolved

F-VECTOR-057 established the exact `BEE_CmdNewVectorLayer` command number (2025 ID 101, 2026 ID 106), its occupied 32-byte `BEE_DoCommand` dispatch-table row, and both callbacks, but direct-call traversal from those entry callbacks **could not** find the true `BEE_Layer::CreateLayerFromType` owner creation path. This is because native code constructs a **polymorphic command TASK**, whose creation path resides in its **virtual methods**, not in a direct call from the table callback.

We now extracted the actual class from both installed Adobe BEE DLLs via MSVC RTTI Complete Object Locator, TypeDescriptor and code-verified VTable:

```text
RTTI TypeDescriptor:  .?AV?$BEE_NewLayerTask@$03@@
Native C++ concept:    BEE_NewLayerTask<4>
Virtual slots:          0 destructor; 1 new layer task handler; 2 task state serialization
```

The specializable fourth layer kind is not a guess: both command-table `+0x08` native callbacks explicitly contain `mov r8d, 4` immediately before calling the 0x30-byte task constructor. Both `+0x08` and `+0x10` constructors assign **the same exact RTTI-backed vtable address**.

| Native endpoint | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| `BEE_CmdNewVectorLayer` | `0x65CDD0` | `0x6783E0` |
| BEE command ID | 101 (`0x65`) | 106 (`0x6A`) |
| Command table record | `0xFECEF0` | `0x104D270` |
| Table +8 task constructor | `0x646BD0` | `0x660C10` |
| Table +16 alternate task constructor | `0x646C30` | `0x660C70` |
| `BEE_NewLayerTask<4>` vtable | `0xFEE6E0` | `0x104EB28` |
| Virtual slot 1 code | `0x54E920` | `0x56D660` |
| Slot 1's direct worker | `0x3151D0` | `0x31E800` |
| Worker direct `BEE_Layer::CreateLayerFromType` CALL | `0x3152B2` | `0x31E8F0` |
| Stock constructor function target | `0x2E3E10` | `0x2ECD00` |
| Worker to Comp attachment helper | `0x31530C → 0x30B650` | `0x31E95B → 0x314820` |
| Comp attach intermediate thunk | `0x3920F0` | `0x39D4A0` |
| Actual `BEE_CompItem::AttachLayerToCompOnly` | `0x392120` | `0x39D4D0` |

**Verified native code graph:**

```text
BEE_CmdNewVectorLayer(command id 101/106)
  → Shared worker BEE_StartGroup / BEE_DoCommand / BEE_EndGroup
  → BEE_DoCommand fixed 32-byte registry: index = cmd_id << 5
  → table[cmd_id] +8 callback
    → allocate 0x30-byte task
    → assign initial layer kind 4 via mov r8d, 4
    → construct RTTI-backed BEE_NewLayerTask<4>
  → virtual slot1:
    → full native BEE new-layer worker
       → BEE_Layer::CreateLayerFromType(kind 4, CompItem*, ...)
       → placement, time, undo/state processing
       → native helper → helper thunk
       → BEE_CompItem::AttachLayerToCompOnly
       → includes TDB_StreamIDPath and optional BEE_CmdSeparateStreamDimensions
```

The 2025 attach path is `0x3151D0 → 0x30B650 → 0x3920F0 → 0x392120`; 2026 is `0x31E800 → 0x314820 → 0x39D4A0 → 0x39D4D0`. All are machine-decoded direct native calls/jumps, not inferred from symbol names. The actual stock constructor call is present in both task workers. A conditional code branch may change the type to 5 when the source is a 3D model; therefore *not* every worker invocation necessarily constructs a Shape type4. **The NewShape callback's normal initial layer kind is 4** and that conditional is explicitly documented.

Virtual slot 2 calls `dvacore::serialization::AddToObject` multiple times and contains additional virtual calls; it is a concrete clue for the Undo command's serialization state. Further analysis is necessary to prove native undo of **foreign CNL types**.

## Scope and safety constraints

This is a **major discovery of Adobe's built-in native implementation**, not a delivered CNL native Shape plugin. The table is internally fixed, the class is an Adobe-compiled template specialization, and `BEE_Layer::CreateLayerFromType` still has a closed built-in type switch (F-VECTOR-037). It provides a complete *architectural execution map*, **not** a stable third-party ABI or an invitation to patch the command table.

The native code has been analyzed purely offline. No `BEE_DoCommand`, `BEE_CompItem`, private factory registration, private TDB stream code, AE GUI or Adobe binary modification occurred. The user's previously verified ordinary CNL Owned Vector Document effect renders and reopens, but native CNL Shape Owner/Contents/Pen/BEE_VectorArt integration is **still not present**. Do not conflate either capability with the native path above. `CompNodeAE` and Phase F untouched.

## Reproduction

`experiments/vector-shape/probe-src/tools/` has independent extraction/check scripts:

- `decode_newshape_command_object_rtti_vtable.py`
- `trace_bee_newshape_task4_virtual_methods.py`
- `disassemble_bee_newlayer_task4_factory_worker.py`
- `inspect_bee_newlayer_task4_create_factory_args.py`
- `trace_newlayer_task4_virtual_owner_creation_graph.py` — intentionally negative direct-graph probe before adding missing CompItem edge
- `find_newlayer_task4_to_comp_attach_path.py`
- `verify_bee_new_shape_complete_owner_chain.py` — PASS for both installed version-pinned DLLs.

Datasets `datasets/ae-bee-newshape-task4-*.json`; no Adobe vendor binaries are published.

## Remaining actual implementation gates

1. **Outside the built-in layer class switch**: locate/validate a true host owner registration path for a CNL-native `BEE_Layer` or CNL-owned indexed Contents tree. The documented AE plug-in SDK doesn't expose this extension contract.
2. **Native TDB lifecycle**: exact C++ `TDB_StreamBase` subclass ABI, registration and canonical ownership/teardown; private `RegisterFactoryFunc` cannot be executed until proven safe in an isolated disposable host.
3. **Native evaluation**: install/validate CNL BEE evaluator/VectorArt provider (separate 20-key polymorphic registry) and its render graph path, without a PF_World or baked Shape workaround.
4. **Native editor**: real `BEE_StreamSpec`/IDPath selection, Pen interaction, mutating coordinate streams and undo after save/reopen.
5. **Release safety**: plugin unload lifetime, AE2025/26 binary build specificity, project corruption defense and refusal on nonmatching binaries.

The next research should **seek a separately host-admitted foreign type** rather than reimplementing the old `BEE_NewLayerTask<4>` itself as an effect.
