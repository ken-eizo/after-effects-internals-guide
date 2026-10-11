---
status: research-active
last_verified: 2026-10-11
evidence: E0-G + E0-H + E0-S + E2-L + H; no E2-X host result for this project
versions: SDK 25.6; AE 2025 symbol corpus; current Adobe Guide (accessed 2026-10-11)
---

# Native Shape Extensibility: Authoring, Evaluation, Tools and Rendering

## Research objective and non-goals

Determine whether a third-party plug-in can independently **instantiate and register a native dynamic Contents hierarchy**, expose it in the regular AE Timeline, receive native Pen/Selection tool edits, and feed paths into AE's built-in vector evaluation/rasterizer **without creating or depending on an ordinary Shape Layer**. Ultimately test a CompNodeAE-owned native vector object. Reading or writing an existing Shape Path through AEGP/scripting is an observation/control baseline, **not** a success criterion.

This is a system reconstruction, not a promise that undocumented APIs are stable or extensible. Avoid calling private exports or modifying host process memory during the initial phase.

## Five distinct contracts (do not conflate)

| Boundary | What the visible feature requires | Current evidence | Still unproven |
| --- | --- | --- | --- |
| Creation/registration | Define a host-owned stream type/child-factory, attach to a host object | E2-L: `TDB_StreamFactory`, `TDB_MatchName`, `BEE_GenericShapeStream` symbols in AE 2025 `BEE.dll` | Whether external code can register new stream types; whether factory is open/closed |
| Hierarchy/Timeline | Indexed children, add/remove/reorder, persistence, undo, native tree UI | E0-G/H: `AEGP_DynamicStreamSuite` operates on **existing** indexed groups | Creating a new arbitrary indexed group inside an effect |
| Tool interaction | Host native pen/selection/vertex UI targets the new object | E0-G: Custom Comp UI and Drawbot can draw **plug-in** handles | Registering an object with AE's native path tool |
| Vector evaluation | TDB/BEE streams materialize geometry at time t | E2-L: `BEE_VectorStream::PopulateVectorArt`, `BEE_VectorArt::OriginInfo` | External geometry providers and dependency/identity contracts |
| Vector raster/output | AGM-facing vector commands, bounds and RG nodes materialize pixels | E2-L: `BEE_VectorLayer::Rasterize2DGraph`, `C_AGMDLTranslatePort` symbols | Public hook to submit a VectorArt object as an effect's output |

AEGP can **edit existing shape streams**, but that observation does not satisfy the objective. `PF_Param_GROUP_START/END` makes parameter topics, not an arbitrary mutable Timeline Contents object. Effect rendering normally returns pixels. `DRAWBOT_PathSuite` is UI drawing; it is not proof of using the production shape renderer. The public Artisan contract substitutes a renderer for composition 3D, not a generic 2D shape authoring/value-provider API; interactive Artisans have different final-output behavior. These are distinct negative scope statements about the *documented surfaces*, not proof that all private routes are impossible.

## Working internal path and evidence limits

```text
native Shape/Contents owning object
  -> TDB stream factory + match name + stream identity  [registration details unknown]
  -> BEE_VectorStream / TDB stream evaluation
  -> BEE_VectorArt::Group / Path / Graphic / Filter
  -> bounds analysis and AGM/AIM/display-list conversion
  -> BEE_VectorLayer::Rasterize2DGraph -> RG_RenderNode -> pixel materialization
```

AE 2025 `BEE.dll` export listings include constructor-like signatures referencing `TDB_StreamFactory*` and `TDB_MatchName*`; their existence establishes a **distributed implementation artifact**, not a stable call contract, a plug-in type registration path or a usable vtable layout. ABI may change by version. For the supporting findings, inspect repository files `research/findings/F-VECTOR-002-stream-vectorart-agm-render-boundary.md` and `research/findings/F-ABI-012-aegp-stream-coordinates-bridge-into-bee-tdb.md`. These live outside the MkDocs `docs_dir` and are evidence paths, not site page links.

## Research questions and discriminators

1. **Type registration**: Are built-in vector types registered through a centralized, extensible `TDB_StreamFactory`, or a sealed host initialization table? Locate construction/registration call sites, owner lifecycle, and allowed caller modules by *static* analysis. Distinguish constructor symbols from registration semantics.
2. **Ownership**: Is `ADBE Root Vectors Group` allocated only as part of `BEE_VectorLayer`, or can another owner legitimately contain a similar TDB indexed group? Compare Shape Layer, ordinary layer Effect Parade, mask parade and plug-in parameter groups using public AEGP traversal and persistence diffs. Merely observing an indexed Effect Parade is not sufficient.
3. **Timeline**: Does timeline topology derive from a generic TDB stream descriptor or special-case vector-stream owners? Track one add/reorder operation against identities; avoid assertions based solely on visible UI.
4. **Native tools**: Which identity maps a Pen-tool selection to a vector/path stream? Determine whether that mapping is discoverable and registerable externally; compare native pen behavior vs Custom Comp UI.
5. **Geometry output**: Can an effect communicate geometry *before* pixel materialization? Inspect public Effect/AEGP/Artisan output contracts, runtime vector functions and the dependency/cache graph. Require a true vector intermediate, not a Drawbot overlay or transient `PF_World`.
6. **Durability**: An apparent native extension must survive save/reopen, undo, expression/animation, renderer invalidation and AE version restart. Failure here disproves full equivalence.

## Controlled research sequence

- EXP-SHAPE-001: read-only AEGP recursive stream tree from an active native Shape Layer vs an effect on a normal layer. Log grouping kind, match name, depth, child order and errors without host mutation.
- EXP-SHAPE-002: compare identical native vector objects assembled by Scripting vs UI, across save/AEPX and undo; inspect ownership evidence, *not* claim success from path editing.
- EXP-SHAPE-003: static export/import graph for `TDB_StreamFactory`, `BEE_VectorStream`, `PopulateVectorArt`, `Rasterize2DGraph`, AGM bridges, annotated with module/version/provenance. This is not an executable private hook.
- EXP-SHAPE-004: native-tool path selection and transform behavior vs custom overlay; use observable selection/stream ID surfaces before invasive tracing.
- EXP-SHAPE-005: test whether any supported geometry-producing host API returns a vector output consumable by the native shape renderer. Keep negative-search scope explicit.
- EXP-SHAPE-006 (gated): attempt a custom host-owned Contents group and native render integration only after an independently supported, safe registration path has been demonstrated.

## Falsification and promotion rules

**Claim A**: public SDK has no *documented general-purpose* custom indexed-group/type registration API. Falsified by a reproducible SDK declaration/Adobe sample supporting registration of a new native stream *type*, not merely adding a known stream to an existing group.

**Claim B**: native vector evaluation and final rasterization are separate stages. Supported by AE 2025 BEE exports; determine exact causal call chain with independent runtime capture before promoting.

**Claim C**: native editor, Timeline, and renderer all use an identical object identity. **Hypothesis**, not proven. Falsified by captured distinct binding identities or one subsystem operating without a direct identity bridge.

A host experiment is `observed` only with a captured host version, runnable probe, raw result, digest, and interpretation. Unsupported/negative results remain recorded. See [Evidence Model](../foundations/evidence-model.md) and repository path `experiments/observatory/README.md`.

For the cross-version history and concrete private symbol counterevidence (including the possibility that `RegisterStreams` installs stream command handlers rather than new types), see [Native Shape Historical / Private API Forensics](historical-native-extension-forensics.md). A user-observed `GetNumStreamsInGroup` leaf-precondition violation is recorded at repository path `experiments/vector-shape/EXP-SHAPE-001-host-failure.md`, distinct from proven shape plugin extensibility.

## Sources and provenance

- **E0-G** Adobe, [AEGP Suites](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/) (DynamicStreamSuite; accessed 2026-10-11).
- **E0-G** Adobe, [Custom UI & Drawbot](https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/) (UI-only drawing contract).
- **E0-G** Adobe, [Artisans](https://ae-plugins.docsforadobe.dev/artisans/artisans/) and [Artisan Data Types](https://ae-plugins.docsforadobe.dev/artisans/artisan-data-types/).
- **E0-H / E0-S** locally distributed SDK 25.6 at `E:\ae25.6_61.64bit.AfterEffectsSDK\Examples`; AEGP headers and Adobe samples `AEGP/Streamie` / `AEGP/ProjDumper`, evaluated as contracts/working patterns only.
- **E2-L** `datasets/ae-2025-vector-shape-symbols.csv` (AE 2025 installed runtime symbols; 2518 entries + header).
- **H** External registration, native-tool targeting and direct vector output: open hypotheses, not confirmed.
