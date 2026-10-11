---
status: active
last_verified: 2026-09-15
---
# Vector / Shape Runtime Architecture

The installed AE 2025 runtime exposes a useful separation between editable streams, evaluated vector art, bounds analysis and raster materialization.

```text
Shape layer Property/Stream tree
        |
        v
BEE_VectorStream / TDB streams
(Rect, Ellipse, Fill, Stroke, Repeater, Trim, Merge Path, ...)
        |
        | PopulateVectorArt(layer, stream path, time, ...)
        v
BEE_VectorArt object tree
(Group / Path / Graphic / Filter / StrokeData / OriginInfo)
        |
        +--> GetBounds(... RenderExtentMode)
        |
        +--> AGM/AIM paths and display-list translation
        |
        v
BEE_VectorLayer::Rasterize2DGraph(...)
        |
        v
RG_RenderNode -> PF_World / render graph materialization
```
## 2026-10-11 — Native path provenance and edit selection investigation

The AE2026 host-executed ShapeLayerAE traversal is archived in `experiments/vector-shape/EXP-SHAPE-001-host-success.md`. A 2025/2026 static audit established `BEE_VectorArt::OriginInfo` direct and synthetic `TDB_StreamIDPath` accessors, plus a host-side selected-shape-path enumeration function `BEE_GetSelectedShapePathsVec`. Bounded disassembly confirms the latter invokes `BEE_SelIterate`, and the VectorLayer constructor initializes its vector art cache. These E2-L observations do **not** prove a Pen-tool binding, supported independent Contents registration, or a plugin geometry output API. For explicit tests and raw evidence see [Native Vector Editability and Provenance](native-edit-and-provenance-bridge.md).

## Important boundaries
`BEE_VectorArt::OriginInfo` stores a `TDB_StreamIDPath`, so evaluated vector objects retain a route back to stream identity. This is consistent with selective invalidation and with operator-specific provenance surviving after stream evaluation.

Bounds are not merely inferred from the final raster. `BEE_VectorArt::GetBounds` accepts a `RenderExtentMode`, and `BEE_VectorLayer` has dedicated source-rect helpers before `Rasterize2DGraph` constructs the render node. AEIG should therefore treat vector bounds as an explicit intermediate computation.

The AGM boundary is also not limited to UI Drawbot. BEE imports helpers that create an AGM raster port from `PF_World`, combine/play AGM paths, and construct vector-art objects from `CAGMPath`. `C_AGMDLTranslatePort` bridges an AGM display-list style interface to an AE pixel world/shape target.

## SVG is a related but distinct path
`BEE_SVGToAGMDisplayListConverter` exposes Open/Close, `GetDisplayListPort`, document bounds and view-box accessors. This supports a separate SVG -> AGM display-list ingestion path. It should not yet be assumed identical to the native Shape Layer `VectorStream -> VectorArt` path; the useful research question is where the two converge.

## Open questions
- Which shape operators materialize new geometry versus attach a filter object to existing art?
- Is `PopulateCacheVariant` a geometry/appearance cache mode, a bounds-only mode, or something broader?
- Which VectorArt objects survive across time samples and which are rebuilt every evaluation?
- Where does multithreaded AGM shape rendering begin relative to BEE VectorArt materialization?
- At what boundary do CPU/GPU paths diverge for shape rasterization?

Primary local evidence: `datasets/ae-2025-vector-shape-symbols.csv` and Finding `F-VECTOR-002`.

## Current SVG/native-shape ingestion
AE 26.5 exposes two meaningfully different SVG import outcomes. Importing as footage preserves a footage-style source boundary, while composition/native editable shape workflows materialize SVG structure into AE shape-layer Contents with Path/Fill/Transform-style properties. Clipboard SVG can also become native editable shape layers.

This is useful architectural evidence that "SVG support" is not one renderer path. At minimum distinguish external-source ingestion, declarative vector structure, native stream/property materialization, evaluated VectorArt and final rasterization.

A practical model is:
`SVG/file/clipboard source -> parser/import representation -> optional native Shape stream tree -> time-specific VectorArt -> bounds/operator evaluation -> AGM/display-list materialization -> RG/PF pixels`.

## Shape operators are evaluated structure, not layer duplication
Path operators such as Merge/Offset/Trim/Round/Repeater should be modeled as operations over shape content, not as project-layer copies. Repeater-style copies can multiply rendered instances without creating equivalent Timeline layer objects. Therefore object count in the project graph and rendered vector instance count are different quantities.

This distinction matters for identity, invalidation and performance: one authored operator can generate many materialized paths/graphics while retaining one property-stream owner.

## Threading and cache boundaries
`MultithreadedAGMShapeRendering` evidence shows vector-domain parallelism can be controlled independently of general MFR. A single frame may therefore contain composition-level scheduling plus internal vector-raster work decomposition.

Cache experiments should distinguish stored stream values, materialized VectorArt, bounds calculations, AGM display lists and final pixel residency. A change that alters only fill/stroke appearance may have a narrower reusable geometry domain than one that changes path topology.

## Failure classes
- stale vector cache after operator/property mutation;
- incorrect bounds causing clipping despite correct geometry;
- different SVG parser/native-shape semantics after import mode change;
- font/text-to-shape conversion changing editability/identity;
- large Repeater/operator graphs creating vector-domain CPU pressure even when MFR is unchanged;
- CPU/GPU/display-list path divergence producing pixel or antialiasing differences.

## Discriminating experiments
Import one SVG as footage and as native shape structure, then compare persistent property trees, AEP/AEPX diffs, bounds, trace/module activity and output hashes. Independently animate Path, Fill, Stroke, Trim, Merge and Repeater properties and measure which intermediate/runtime surfaces invalidate.

Hold frame concurrency constant while scaling path count and Repeater copies to isolate AGM/vector parallelism from MFR. Compare native-created geometry with imported equivalent SVG geometry to identify the convergence point.

## Version and unknown boundary
26.3/26.5 expanded direct SVG/Illustrator editable-shape workflows; do not back-project those import semantics to older releases. Still unknown: exact cache key for VectorArt/materialized geometry, whether every native-shape render reaches the same AGM path, and where modern GPU acceleration begins relative to AGM/RG.

Related: `F-VECTOR-001-multithreaded-agm-shape-rendering.md`, `F-VECTOR-002-stream-vectorart-agm-render-boundary.md`, `docs/render-graph/render-nodes.md`, `docs/state-model/streams-properties.md`.
