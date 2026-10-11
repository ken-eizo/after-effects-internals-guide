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

A follow-up read-only probe is available as a **compiled but not host-tested** experiment to measure session-specific stream IDs, dynamic flags, leaf types, and a non-mutating `CanAddStream` matrix. See [Native Vector Editability and Provenance](native-edit-and-provenance-bridge.md) for the distinct TDB/VectorArt selection identities, renderer handoff, and strict criteria for full native parity.

## Native stream factory registration breakthrough (2026-10-11)

Offline BEE/TDB PE/IAT analysis found the host-internal `TDB.dll` and confirmed **BEE_Layer::RegisterStreams -> Get_AE_StreamFactory -> TDB_ScRegisterStreams::Register -> TDB_StreamFactory::RegisterFactoryFunc**, with canonical stream creation and guarded unregister. The native `VectorsStreamGroup::CanStore` references built-in `ADBE Vector Shape -`, `ADBE Vector Graphic -`, and `ADBE Vector Filter -` prefixes. See [Native Stream Factory and Shape Schema](native-stream-factory-and-schema.md) for evidence, safety boundaries and *unverified* third-party factory integration.

## Runtime model status
The runtime-side reconstruction is now tracked in `runtime-architecture.md`. AE 2025 exposes a concrete `BEE_VectorStream -> BEE_VectorArt -> AGM-facing translation -> RG_RenderNode` chain, with explicit vector bounds computation before rasterization. This upgrades the domain from surface mapping to a working internal model while leaving cache variants, operator-level reuse and the exact AGM/GPU execution boundary open.

Reproducible local inventory: `datasets/ae-2025-vector-shape-symbols.csv`; core finding: `F-VECTOR-002-stream-vectorart-agm-render-boundary.md`.

## Native shape extension research (2026-10-11)

[Native Shape Extensibility: Authoring, Evaluation, Tools and Rendering](native-extensibility-boundaries.md) and [Historical Native Shape Forensics](historical-native-extension-forensics.md) investigate a stricter goal than editing existing paths: independently registering a mutable native Contents hierarchy, participating in native Pen/Selection tools, and supplying geometry to AE's production vector renderer without creating a Shape Layer. This is presently a **research objective**, not an achieved host capability. See `research/hypotheses/H-SHAPE-001-native-stream-registration.md`, `H-SHAPE-002-native-vector-output.md`, and `experiments/observatory/manifests/EXP-SHAPE-001.json` / `EXP-SHAPE-003.json`.
