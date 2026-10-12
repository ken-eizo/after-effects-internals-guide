---
status: implementation-frontier-reconstructed; host-external-ownership-unproven
last_verified: 2026-10-12
evidence: E2-L AE2025/26 exact installed BEE / TDB machine code
---

# Native Shape Contents: implementation boundary and CNL expansion route

This is a reconstruction of **the real internal Adobe Shape creation mechanism**, not a recipe for a conventional Effect or a claim of supported Adobe SDK extensibility. See [F-VECTOR-054](../../research/findings/F-VECTOR-054-native-shape-full-schema-and-183-creator-pipeline.md) and EXP-SHAPE-054.

## Authentic native creation path

```text
BEE native startup: BEE_VectorLayer::RegisterStreams
 │
 ├─ TDB_ScRegisterStreams::Register (55 + 47 + 19 + 62 static callsites)
 │   ├─ register typed Shape/Graphic/Filter stream creators
 │   ├─ register VectorStreamGroup + VectorsStreamGroup (2 MatchNames, 1 creator)
 │   ├─ register Transform/Materials groups
 │   └─ register BEE_VectorLayer::Create as a distinct TDB type
 ├─ TDB_StreamFactory::SetupCanonicalStream("ADBE Vector Group")
 │
 ├─ BEE_VectorLayer::FillInCanonicalUILayout (10 children in 2025, 11 in 2026)
 │   └─ ADBE Root Vectors Group
 │       └─ VectorStreamGroup::FillInCanonicalUILayout
 │           ├─ ADBE Vector Blend Mode
 │           ├─ ADBE Vectors Group
 │           │   └─ VectorsStreamGroup::FillInCanonicalUILayout
 │           │       ├─ ADBE Vector Group
 │           │       ├─ 4 native Path/Rect/Ellipse/Star types
 │           │       ├─ 4 native Fill/Stroke/Gradient types
 │           │       └─ 11 native vector filter types
 │           ├─ ADBE Vector Transform Group
 │           └─ ADBE Vector Materials Group
 │
 ├─ Separate BEE 20-key polymorphic evaluator registry
 │   └─ native BEE_VectorArt geometry/operators
 │
 └─ Native host Owner + Editor + RenderGraph
     ├─ BEE_VectorLayer and BEE_Layer dispatch
     ├─ native Timeline Contents and StreamIDPath
     ├─ Pen/Selection/Undo context
     └─ BEE_VectorLayer::Rasterize2DGraph → AGM/RG
```

The diagram is a **system boundary graph**: actual edges between registration and canonical functions are present; it does not assert the renderer or editor can consume an unknown externally registered class.

## Strict implementation completion gates

| Gate | Technical object | What constitutes actual success | Status |
| --- | --- | --- | --- |
| A: Independent CNL data core | CNL-owned strongly typed Group/Path/Bezier tree, clone/persistence | Tests and host AEX archive save/reopen | **Core and actual Effect archive confirmed**, but not Adobe-native Contents |
| B: Adobe-native registration | A real `TDB_StreamBase` subtype, named Creator callback, host canonical instance | Safe registration, verified no callbacks/vtables survive module unload; native type can be instantiated and serialized on a disposable AE host | **Not proven** |
| C: Host-owned root hierarchy | Owner that isn't an Adobe Mask or separate Shape Layer, with `ADBE Root Vectors Group`-equivalent editable indexed Contents | Native Timeline reveals CNL-authored child with persistent IDPath; save/reopen/Undo | **Not proven** |
| D: Native editor | `BEE_StreamSpec(BEE_Layer*, TDB_StreamIDPath)`, editable stream selection and Pen/drag routing | Real Adobe Pen moves CNL vertex and updates its host stream with Undo | **Not proven** |
| E: Host-native renderer | CNL polymorphic operator, valid BEE_VectorArt evaluator + producer owner, Rasterize2DGraph/RG | RenderGraph consumes CNL vector output, not PF_World/overlay/baked Shape | **Not proven** |
| F: CompNodeAE integration | Production product | **Explicit user design approval before entering Phase F** | **Prohibited until then** |

## Most important next binary research

1. Find an **owner-creation route that is not the closed `BEE_Layer::CreateLayerFromType` integer switch**. Its native cases are fixed for layer kinds 0–7 (F-VECTOR-037). Trace TDB-deserialization and `BEE_LayerSet` owners to see if plugin-controlled typed objects can legally become real selection/render owners without patching Adobe code.
2. For any candidate, prove from actual constructors the required `TDB_StreamGroup` canonical layout, mutable indexed-child state, stable `TDB_StreamIDPath` and serialization/Undo.
3. Prove whether **nonbuilt-in MatchName entries** can join both TDB typed creator and **BEE evaluator** registries safely with full cleanup. Merely changing prefix strings or calling `AEGP_CanAddStream` fails this test.
4. Trace Pen-selection conversion of the candidate's authored `BEE_StreamSpec` into native vertex hit-test/writeback, then RG graph evaluation.
5. Only after controlled, reversible, version-pinned preflight is proven, seek explicit user consent for an isolated host experiment. The old `CNLPrivateTDBDisposable.aex` is **not safe to run**.

**No standard Effect slider or raster geometry editor is a substitute for gates B–E.** The already user-verified CNL Owned Vector Document Effect is a useful safety control for archive and drawing only. `CompNodeAE` has not been edited.

## 2026-10-12 — A newly proven OWNER boundary, F-VECTOR-055

The TDB Creator callback `BEE_VectorLayer::Create` is not equivalent to AE's real layer factory: in AE2025/26 it allocates a BEE_VectorLayer and passes **null `BEE_CompItem*` (R9=0)** into the same concrete constructor that the normal `BEE_Layer::CreateLayerFromType(4, actual_CompItem*,...)` invokes with an actual CompItem pointer. Thus a registered TDB-native class is not automatically a selectable/renderable layer.

`BEE_Layer::SetParentComp` and `GetParentComp` are exported native methods, but a raw parent setter by itself is **not a validated host layer-insertion mechanism**: the native `BEE_CompItem` index, `BEE_LayerSet` ownership, Undo, cache, lifecycle, IDPath, editor and renderer pathways all remain to be proven. CNL must not invoke these private APIs from a user installation merely because their exports exist. The immediate highest priority is to locate the **complete comp layer-insertion transaction** and determine whether that transaction has any available custom creator path; the fixed built-in integer layer-kind switch is not one.

Evidence: F-VECTOR-055, EXP-SHAPE-055, offline verifier `verify_native_vector_detached_factory_vs_comp_owner.py`. CompNodeAE unchanged, Phase F prohibited.
