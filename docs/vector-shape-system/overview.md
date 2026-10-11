---
status: active
last_verified: 2026-09-15
---
# Vector and Shape System

Shape layers combine a persistent vector object model, hierarchical transforms/modifiers and a renderer-facing tessellation/rasterization path.

## Questions
- What is the exact stream hierarchy for groups, paths, fills, strokes, repeaters and operators?
- Which operators change geometry versus only appearance/bounds?
- How are vector bounds cached and invalidated (`AE.VectorBoundsCache` is a local diagnostic clue, not semantic proof)?
- At what stage are shape paths tessellated, sampled and handed to CPU/GPU rendering?
- How does continuously rasterize/collapse behavior intersect with vector evaluation?
- How does direct Illustrator/SVG paste introduced in 26.3 map SVG concepts into native AE streams?

## Evidence surfaces
Scripting/AEGP streams; AEP differential corpus; local diagnostic keys; render-node traces; path suites; SVG/Illustrator paste experiments; one-pixel/bounds probes.

This domain should cross-link to animation, ROI/bounds, sampling, render graph, GPU and persistence rather than becoming an isolated feature chapter.

## AGM execution layer
AE 2024 Beta resources expose MultithreadedAGMShapeRendering, explicitly describing vector-shape rendering across multiple threads. Local installs retain AGM.dll from CS6 through 2025; AE 2025 also ships AdobeSVGAGM.dll and drawbotagm.dll. Media Encoder ships AGM-family modules as well, so AGM should be treated as an Adobe graphics substrate rather than an AE-only class name.

The current working model is: AE owns the editable Shape/Property/animation graph; an AGM-facing layer consumes evaluated vector geometry/appearance commands; the resulting vector rasterization/materialization rejoins AE's composition/render graph. The exact command boundary and whether tessellation or raster work is performed inside AGM remain open.

MultithreadedAGMShapeRendering is important because it separates vector-domain parallelism from frame-level MFR. Benchmarking should hold frame concurrency constant while varying single-frame shape complexity to isolate AGM's own threading.

## Adjacent 2024 internal features
The same Beta-feature corpus contains GroupAlphaForAIConvertToShapes, exposing a conversion-specific semantic issue: Illustrator group opacity needs preservation when converted into native shape fills. This is evidence that AI→Shape conversion is not merely path copying; group-level compositing semantics must be lowered into AE's shape/property model.

## Verified native host experiment and identity frontier (2026-10-11)

The fixed read-only ShapeLayerAE AEGP probe was executed in AE 2026. Its archived raw capture shows 180 public stream nodes with zero reported per-node API errors, including `ADBE Root Vectors Group` as an indexed Contents group and Rectangle/Fill as named child groups. This E2-X result proves real host traversal **only**, not plug-in-owned Contents creation. See repository report `experiments/vector-shape/EXP-SHAPE-001-host-success.md`.

A follow-up read-only probe was **executed in AE2026**: it measured session-specific stream IDs, dynamic flags and leaf types, and successfully ran a non-mutating `CanAddStream` matrix. The AE2026 v3 host evidence is archived separately from static native DLL research. See [Native Vector Editability and Provenance](native-edit-and-provenance-bridge.md) for the distinct TDB/VectorArt selection identities, renderer handoff, and strict criteria for full native parity.

## Native stream factory registration breakthrough (2026-10-11)

Offline BEE/TDB PE/IAT analysis found the host-internal `TDB.dll` and confirmed **BEE_Layer::RegisterStreams -> Get_AE_StreamFactory -> TDB_ScRegisterStreams::Register -> TDB_StreamFactory::RegisterFactoryFunc**, with canonical stream creation and guarded unregister. The native `VectorsStreamGroup::CanStore` references built-in `ADBE Vector Shape -`, `ADBE Vector Graphic -`, and `ADBE Vector Filter -` prefixes. See [Native Stream Factory and Shape Schema](native-stream-factory-and-schema.md) for evidence, safety boundaries and *unverified* third-party factory integration.

## 2026-10-11 — External read-only private factory accessor, typed registration and native VectorArt evaluation

An explicitly invoked AE2026 ShapeLayerAE v3 AEGP returned a non-null pointer from the pinned private `TDB.dll!Get_AE_StreamFactory()` accessor. The same user-run AEGP demonstrated unknown Shape/Graphic/Filter-prefixed match names are admitted by native Contents `CanAddStream`, without instantiating them. Cross-version bounded binary disassembly confirmed that the native Shape creators feed `TDB_ScRegisterStreams::Register`, and `BEE_VectorLayer::GetVectorArt` directly calls `PopulateVectorArt` and `GetBounds`. **No independent plugin-owned editable native Contents or geometry output is yet demonstrated.** Details: [Native Stream Factory](native-stream-factory-and-schema.md), [Independent Native Vector Output](native-vector-output-ownership.md) and original raw experiment `EXP-SHAPE-009-010-v3-host-confirmation.md`.

## 2026-10-11 — Second internal vector evaluator registry and 20 concrete native operator types

A cross-version static audit recovered a **separate BEE MatchName-keyed evaluator registry** beyond `TDB_StreamFactory`. The native initializer installs exactly 20 built-in Shape/Graphic/Filter/Group evaluation objects. Each MatchName was recovered from its static constructor literal, paired with its actual registration callsite and concrete MSVC RTTI operator class; the full set matches between AE2025 and AE2026. `PopulateVectorArt` and `StreamBasedFilter::DoFilter` both query the registry and invoke the same evaluator virtual slot (different mode arguments). TDB factory registration also eagerly invokes a creator and canonicalization. None of this demonstrates externally creatable effect-owned vector output. See [Native Vector Evaluator Registry](native-vector-evaluator-registry.md), Findings F-VECTOR-013/014.

## 2026-10-11 — Native evaluator vtable and concrete Path/Repeater provenance

The two installed versions now agree on all 20 concrete operator vtables, reference-counted MSVC RTTI inheritance and the native evaluation mode split: **9 Shape/Graphic/Group operators dispatch for mode 0; 11 vector Filters dispatch for mode 1** via the primary vtable at +0x18. Path, Rectangle and Ellipse concrete generators directly build `CAIMBezierPath` / `BEE_VectorArt::Path` and stamp the native `TDB_StreamIDPath` origin. The Repeater algorithm **directly invokes `OriginInfo::AppendSyntheticIndex`** in 2025/2026, promoting the older hypothetical association to supported static evidence. The Pen-tool selection contract and effect-owned native output remain unproven. See [Native Vector Operator ABI and Origin](native-vector-operator-abi-and-origin.md) and Findings F-VECTOR-015/016.

## Runtime model status
The runtime-side reconstruction is now tracked in `runtime-architecture.md`. AE 2025 exposes a concrete `BEE_VectorStream -> BEE_VectorArt -> AGM-facing translation -> RG_RenderNode` chain, with explicit vector bounds computation before rasterization. This upgrades the domain from surface mapping to a working internal model while leaving cache variants, operator-level reuse and the exact AGM/GPU execution boundary open.

Reproducible local inventory: `datasets/ae-2025-vector-shape-symbols.csv`; core finding: `F-VECTOR-002-stream-vectorart-agm-render-boundary.md`.

## Native shape extension research (2026-10-11)

[Native Shape Extensibility: Authoring, Evaluation, Tools and Rendering](native-extensibility-boundaries.md) and [Historical Native Shape Forensics](historical-native-extension-forensics.md) investigate a stricter goal than editing existing paths: independently registering a mutable native Contents hierarchy, participating in native Pen/Selection tools, and supplying geometry to AE's production vector renderer without creating a Shape Layer. This is presently a **research objective**, not an achieved host capability. See `research/hypotheses/H-SHAPE-001-native-stream-registration.md`, `H-SHAPE-002-native-vector-output.md`, and `experiments/observatory/manifests/EXP-SHAPE-001.json` / `EXP-SHAPE-003.json`.


## 2026-10-12 — The indexed Contents and mask/vector editor boundary is shared; importer bootstrap is not

Exact executable-instruction audits across AE2025/2026 show BEE_CmdAddToIndexedStreamGroup is **a generic BEE_Layer stream-child/Undo command**, with 13 real callers in mask, layer-set, material and other native subsystems; the specialized Vector property command is distinct. The Shape stream-path identity predicates compare end-of-path MatchNames for **both Masks and Vector Shapes**. Native mask vertex and feather selection routines actually call these shared predicates. This is a host-internal path/selection abstraction broader than a concrete VectorLayer class. See [Research-to-Product Vector Frontier](research-to-product-frontier.md) and Finding F-VECTOR-021.

However, the AE2026 SVG Paste command callback now proves it calls TDB_StreamGroup::FindStream on **ROOT_VECTORS_GROUP** and exits the conversion branch if that stream is absent; a generic BEE_Layer* argument does not make the importer a way to install a missing native Contents root on an arbitrary effect. See F-VECTOR-022 and EXP-SHAPE-020. All native BEE/TDB work is **static binary research**, not user-installed runtime private calls.

## 2026-10-12 — Tested procedural PICA vector output and user-facing product prototype

The user installed and re-tested the corrected native VectorBridge Consumer AEX in AE2026; the screenshot showed PICA suite: connected and four native cubic segments, with installed hash identical to the corrected binary. Independently, a new compiled C++ consumer VectorBridgeToSVG dynamically loads the actual AEGP, receives the four cubic segments at rational time, applies path-level affine instancing and writes an **SVG with 28 distinct path objects / 112 cubic Beziers**. A two-timepoint validation passed and confirmed zero raster image nodes. It is a practical code-to-vector artifact, though native Shape import fidelity is not yet tested. See [Research-to-Product Vector Frontier](research-to-product-frontier.md), Findings F-VECTOR-020/023, and EXP-SHAPE-021.

The high-risk flagship goal is unchanged: ordinary CompNodeAE Effect SDK plug-in owns native Timeline Contents, native Pen/Selection, and a BEE_VectorArt renderer input **without creating a separate Shape Layer**. The PICA geometry bus and generated SVG are real intermediate product capabilities, **not** proof of this native parity.


## 2026-10-12: native Mask Path experiment on ordinary AV layers (compiled, awaiting user AE host test)

A third AEGP prototype is now compiled from original C++ source and the distributed Adobe SDK 25.6 (Finding F-VECTOR-024, Experiment EXP-SHAPE-022). It connects the independently host-confirmed PICA Bezier producer to **AE native host-owned Mask Path streams**, using CreateNewMask, CreateVertex, SetMaskOutlineVertexInfo and SetStreamValue on a selected ordinary AV Layer. One explicit command sets Mask Mode NONE for interactive native Pen handles without changing original pixels; another sets Mask Mode ADD to let AE's built-in native Mask compositor clip the source. A read-only menu command records the native root stream MatchNames to compare ordinary AV, Mask and Shape ownership in the same host.

**No actual AE host action has been tested for the new plugin; compiled-PiPL/PE and SDK signatures only are confirmed.** The user will install and test it separately. No Shape Layer is created in the intended workflow, but the resulting Mask belongs to the ordinary BEE AV Layer — NOT the CompNodeAE effect's own Contents. This does NOT prove direct BEE_VectorArt, native custom BEE operator registration, native Shape Layer renderer interception or Pen editing of effect-owned procedural vertices. A native Mask is a real AE editing and mask-rendering route, but was publicly accessible before this project; the novel local connection is PICA procedural geometry entering that host-owned stream without raster intermediate.

If native mask test passes: next implement live path-input/expression-free sync from the edited native Mask to CompNodeAE nodes, while continuing the independent private-ABI stream/renderer owner research. See F-VECTOR-021 for BEE's shared Mask/Shape path selection identity substrate.


## 2026-10-12 — Reconfirming the actual flagship: no Mask/Shape shortcuts

The user's actual goal is direct control of **the native path object, its editable Timeline hierarchy, Pen tool binding, vector evaluation and native AE render output** from a plugin-owned new type. Creating a Mask, writing to standard Shape Contents, rendering PF_World or exporting SVG cannot be promoted to that achievement.

New two-version vftable and native command work proves that AE's AV Layer and Vector Layer put their distinct Rasterize2DGraph implementations into **the same virtual Layer slot** (2025 index235, 2026 index238), with distinct GetLayerType and factory-created native C++ class identities. This means renderer participation is an **owner/layer class contract**, not merely Bezier geometry or a BEE operator MatchName registration. Separate TDB and BEE evaluator registries must be connected to a legitimate native owner, editor/selection model and render-graph dispatch.

See [Independent Native Vector Objects: Type, Owner, Editor and Renderer](independent-native-vector-owner-research.md), F-VECTOR-025 and EXP-SHAPE-023. The older Mask PICA bridge is retained for historical completeness but no longer treated as a step meeting the main independent native Contents objective.


## 2026-10-12 — TDB Creator lifecycle ABI landmark

The first native type registration requirement is more constrained than callback installation: RegisterFactoryFunc clones an erased MSVC std::function then eagerly creates a real native TDB_StreamBase instance and invokes virtual IsLeaf/GetAsLeaf/SetupCanonicalLayout and separated-dimensions checks. These virtual methods were identified directly in AE2025 and AE2026 exported TDB vftables. Registering with an invalid/dummy subclass is unsafe even before placing a stream in the Timeline.

TDB_ScRegisterStreams::UnregisterAll walks registrations in reverse, while its destructor does NOT automatically unregister. This is critical for any future plugin unload / host state lifecycle test. See F-VECTOR-026 and EXP-SHAPE-024; the independent-Contents product milestone remains unachieved until host creation, editor and renderer integration work end-to-end.


## 2026-10-12 — First compiled plugin-owned vector geometry core; host-native interface is still open

The independent native path/Contents project now has a real source implementation separate from AE standard Masks/Shapes: CNLNativeVectorCore.dll with typed tree, true cubic Bezier handles, procedural geometry, deterministic archive, cloning and 20-function C ABI; actual compiled DLL and CTest/ctypes cross-language tests passed (F-VECTOR-029, EXP-SHAPE-026). This is NOT an AE AEX and does NOT yet satisfy native TDB/Timeline/Pen/VectorArt renderer integration.

Static AE2025/2026 work (F-VECTOR-027/028) separately established native Group Read/Write stream IDs and canonical layout, CloneStream/SetParent behavior and BEE's native operator registry's polymorphic lifetime. That clarifies next host integration requirements; no private registrar was invoked, no AE UI action was performed. Retain these as separately falsifiable gates, not as successful host-native third-party output.


## 2026-10-12 — Compiled host AEGP and separate native registration acceptance experiment

The independent CNL vector-core is now compiled into an actual AEGP as CNLNativeVectorHostProbe.aex. This AEX has a user-invoked Animation menu to create true independent CNL cubic geometry and report the loaded TDB.dll's SHA256 and exported private factory methods. It calls NO private mutating native functions; even the read-only getter is invoked only when the installed TDB module hash and opcode pattern match the pinned AE2025/2026 builds. The build is complete, **AE in-host execution is not yet tested**. F-VECTOR-032, EXP-SHAPE-028.

A different, explicitly HIGH RISK disposable native type registration AEX has also been compiled but **NEVER installed or run**. It is version-pinned, menu-triggered, double-acknowledged and contains an immediate best-effort unregister attempt. It forwards a new CNL MatchName to Adobe's own complete TDB_ParamPathStream native Creator. The target is ONLY to test private TDB factory acceptance of a brand-new MatchName, not native Contents/Pen/VectorArt. It may crash or corrupt AE; no safety or rollback is proven. F-VECTOR-030/031/033 and EXP-SHAPE-027..030.

Offline x64 DLL/EXE lifetime simulation with MSVC std::function pass-by-value passed, but this is not actual Adobe ABI. See EXP-SHAPE-029.

**Next success gate:** the user tests the safe AEX preflight and supplies its report. Only after that and explicit user acceptance of disposable-host risk should the separate mutating AEX ever be considered. An actual external new TDB type registration is still UNPROVEN. Further owner/editor/evaluator/render contracts remain after that.


## 2026-10-12 — Critical native callback ABI correction and project-state gate

A later code audit discovered that the earlier HIGH-RISK native type registrar AEX had the wrong fifth Creator callback parameter: unsigned int instead of bool. This is NOT a harmless cosmetic difference. F-VECTOR-034 and EXP-SHAPE-031 show the corrected MSVC function object uses native C++ TDB classes and bool/unsigned int/bool, and an independently compiled C++ COFF decorated signature matches Adobe's actual RegisterFactoryFunc exported parameter-type suffix in AE2025 and AE2026. No private registration was called.

The previous gate of 'no active selected AE layer' was also inadequate. The rebuilt dangerous AEX and the read-only safe AEX v2 now share a public-SDK-only project guard which blocks non-empty or dirty projects, non-root active items, nonempty Render Queue and unavailable host state. This is risk reduction, NOT a guarantee of safe Adobe private ABI mutation. Both new AEX binaries compile and pass source/PE checks, but new gate v2 is NOT yet tested inside AE. The user's earlier safe v1 probe DID pass inside AE2026 (EXP-SHAPE-028-LIVE-001).

Old dangerous AEX builds must NOT be run. There is still no AE-native registered plugin type, independent Contents, native Pen editor, BEE VectorArt or AE RG renderer.
