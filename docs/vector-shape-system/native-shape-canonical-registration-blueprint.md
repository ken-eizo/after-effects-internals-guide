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

## 2026-10-12 — Native Shape command transaction and exact fixed-size command table (F-VECTOR-056)

Following the TDB factory / parent owner split of F-VECTOR-055, the actual `BEE_CmdNewVectorLayer` binary code was traced to `BEE_StartGroup → BEE_DoCommand → BEE_EndGroup` in AE2025 and AE2026. The native type-4 Shape creation helper separately contains both `BEE_Layer::CreateLayerFromType(4, comp)` and `BEE_CompItem::AttachLayerToCompOnly(layer, position, flags)` in the SAME bounded function; `AttachLayerToCompOnly` has rich native bookkeeping far beyond `SetParentComp`.

`BEE_DoCommand`'s common executor uses a **32-byte native command table**, 2025 RVA `0xFEC250` (155 entries, 149 with two nonnull callback pointers) and 2026 RVA `0x104C530` (160 entries, 155 with both). It checks two fields `+8` and `+0x10` and invokes a pointer at `+8` indirectly. No direct references from table items or their immediate handlers to `BEE_CmdNewVectorLayer` were detected; the **final command dispatcher → type-4 creation helper edge is STILL OPEN** and must not be claimed. This table is an internal implementation detail, **not** a supported or proven custom-command registration API.

Architectural consequence for an independent CNL owner: must satisfy ALL of (1) typed native TDB creator, (2) permitted native Contents hierarchy and Canonical parent-child relations, (3) legitimate native BEE CompItem/LayerSet insertion with ID and state, (4) Undo command integration, (5) native editor/BEE VectorArt. Avoid private registry or command-table writes in AE. Source and evidence: F-VECTOR-056 / EXP-SHAPE-056. `CompNodeAE` unchanged and Phase F still paused.

## 2026-10-12 — Exact BEE New Shape command identifier and dispatcher (F-VECTOR-057)

The former uncertainty about the **native command integer ID** has been resolved by reading the actual `BEE_CmdNewVectorLayer` machine-code wrapper: AE2025 passes `0x65` (101), AE2026 passes `0x6A` (106), each with resource `0x306`, into the shared Undo command worker. At stride 32 this maps exactly onto the actual native command table record `0xFECEF0` (2025) or `0x104D270` (2026). The real `+0x10` execution callbacks are `0x646C30 / 0x660C70`, which invoke `0x544470 / 0x563290` respectively.

The final indirect handler-to-comp-owned `CreateLayerFromType(4) → AttachLayerToCompOnly` edge remains **not yet shown** by a six-level native direct-call graph, so host command registration is **not** demonstrated as an external CNL extension point. Exact receipts in EXP-SHAPE-057. Do not patch table entries or install risky private registrar; `CompNodeAE` and Phase F untouched.

## 2026-10-12 — True native New Shape task dispatch path RESOLVED (F-VECTOR-058)

The once-open `BEE_DoCommand` → native type-4 Shape owner creation edge is now cross-version proven **in static BEE code**, after reconstructing the **MSVC RTTI-backed C++ task class** `BEE_NewLayerTask<4>` (`.?AV?$BEE_NewLayerTask@$03@@`). The 32-byte command record's `+0x08` callback explicitly supplies `mov r8d,4` while constructing a 0x30-byte polymorphic task. Both `+8` and `+16` callback variants assign its SAME native vtable. Its virtual slot1 calls the built-in new-layer worker, which calls `BEE_Layer::CreateLayerFromType` and then reaches `BEE_CompItem::AttachLayerToCompOnly` via native helper calls.

Full 2026 direct CompItem attach route: `0x31E800 → 0x314820 → 0x39D4A0 → 0x39D4D0`. Full 2025: `0x3151D0 → 0x30B650 → 0x3920F0 → 0x392120`. The task also contains TDB StreamIDPath and Undo command state/serialization logic. This is the **original Adobe native Shape command implementation**, not an authorized third-party extension ABI. A custom CNL layer class cannot be inferred from the fixed type-4 task or the `BEE_Layer::CreateLayerFromType` closed switch. Exact source+receipts: F-VECTOR-058 / EXP-SHAPE-058. No private host invocation, CompNodeAE edit or Phase F.
