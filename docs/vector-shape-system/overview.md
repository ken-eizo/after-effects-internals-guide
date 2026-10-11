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
