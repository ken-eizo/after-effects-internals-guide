---
date: 2026-10-13
status: PASS offline native compiled CNL hierarchy / public AE AEGP host probe; AE host probe not yet executed
evidence: E2-L exact Adobe SDK 25.6 public headers; 2/2 native CTest; PE AEX; previous EXP-SHAPE-005 real AE user trace
---
# F-VECTOR-061 — ChapeLayer: programmable Timeline-style hierarchy semantics and strict Adobe-native extension boundary

## Actual objective

This is NOT about reproducing a conventional Shape Layer or packing PF effect parameters in a GROUP. The ambition is a *new After Effects native Timeline object type* whose plug-in author defines its own:
1. MatchName-backed typed child families;
2. Indexed child insertion/admission/move/reparent and a nested named/indexed hierarchy;
3. ordering and rendering/evaluation semantics;
4. stable identity, serialization and Undo/Redo;
5. native Pen, selection, BEE VectorArt and RG integration.

**Do not treat the current compiled AEX as the completed native AE layer.** There is still no demonstrated external plug-in registration point for an independent BEE_Layer, a new TDB_StreamBase subtype and its evaluator/selection implementation.

## What public Adobe SDK *actually* provides (verified installed SDK 25.6)

The actual E:/ae25.6_61.64bit.AfterEffectsSDK/Examples/Headers/AE_GeneralPlug.h includes:
- AEGP_Menu_NEW: public registration point for an item under Layer > New. This is NOT a public registration point for a new layer class.
- AEGP_DynamicStreamSuite4: GetNewStreamRefForLayer, GetStreamGroupingType, GetNumStreamsInGroup, GetNewStreamRefByIndex/ByMatchname, GetMatchName, CanAddStream, AddStream, Duplicate/Delete/ReorderStream.
- AEGP_AddStream operates on an existing INDEXED_GROUP and matchName; it does not define a new C++ native stream type or attach a new evaluator.
- PF_Param_GROUP is an Effect UI parameter grouping structure, not arbitrary native Timeline Contents element constructors.
- Existing text animator and Shape hierarchies are host-owned: APIs may inspect and manipulate available built-in child types, **but no public BEE/TDB type factory registration interface has been proven**.

Key nuance: public DynamicStreamSuite *can change existing hierarchical stream instances*. The novel discovery target is not "making groups dynamic at all", but "**author-defined type+parent predicates+evaluator+native owner**" within the host's native Timeline.

## Big discovered separation of runtime contracts

The original BEE Shape 2025/2026 native implementation provides multiple necessary-but-not-sufficient layers:
- Native TDB type registrations: 55 + 47 + 19 + 62 = 183 callsites (conditional; not 183 guaranteed live registered types), 20 Contents subtype entries with real native Creator callbacks (F-VECTOR-054).
- Native Canonical Layout: Layer -> Root Vectors -> indexed Vectors Contents, a 20-type allowable child list. This is not the same as rendering semantics.
- Native CanStore: a predicate consistent with Shape/Graphic/Filter MatchName prefixes. Earlier real AE2026 EXP-SHAPE-005 recorded CanAddStream=TRUE for some unknown ADBE Vector Shape/Graphic/Filter-prefixed names; no AddStream was attempted, so **factory instantiability is still unproven**.
- BEE_VectorStream separate polymorphic evaluator registry of native VectorArt operators, not the TDB Factory and not plain SVG/PF_World.
- Host native owner CompItem insertion/creation: ShapeLayerTask<4> command -> Undo -> fixed LayerType 4 ctor -> AttachLayerToCompOnly, the static code path (F-VECTOR-058/059).
- Native editor/selection/Undo/TDB persistence, rendering and object lifespan are separate, not inferred from passing AddStream/CanStore or registering an AEGP menu.

This creates a *real research roadmap*: if safe registration of author-controlled types in each mandatory native subsystem could be proven, the same technology may support arbitrary new Timeline grammars (procedural geometry, text-selector-like groups, compositing pipelines, typed nested operators), not merely one new Shape Layer.

## ChapeLayer code delivered TODAY (actual ShapeLayerAE, not simply copied AEIG)

1. AEGP Layer > New menu entry "ChapeLayer (Native Type Pending)" using AEGP_Menu_NEW. Fail closed on click; does not make stock Shape or alter any project.
2. Animation menu read-only Host Contents Admission probe. Given selected stock Shape Layer with a nested Group, inspect Layer -> Root Vectors -> Contents -> nested Group Contents and record known operators, unknown ADOBE-prefix MatchNames and CNL-defined custom names via public CanAddStream; record actual indexed child order. No AddStream, no TDB/FLt/BEE calls.
3. A native C++ programmable type schema in ChapeHierarchyRules.h/.cpp: register independent CNL names and hierarchical group types, parent-specific child rules, reorder/reparent, cycle rejection, type schema update invariants, and per-group Forward/Reverse execution-trace rules.
4. The same TSV includes a second comparison branch containing the plugin-defined CNL control schema with editable type admission and a deterministic forward vs reverse hierarchy traversal trace. This is *not* an Adobe VectorArt renderer or display of a native new Layer.
5. 2/2 native compiled Release-safe CTest PASS and the AEX PE verifier PASS (PiPL, EntryPointFunc, no BEE/TDB/FLT imports).

The rules prototype is **not yet persisted with CNLVEC01's existing node archive** and does not yet drive the SVG renderer; it is a separately tested compositing grammar and scheduling model that can later be bound to persistent CNL Document node IDs. No claim of runtime Adobe rendering semantics is made.

## Why this is a new capability *if and only if* the host-native bridge is proven

A developer-defined grammar with independent owner and native renderer would allow group-local rules such as:
- only geometry inside a path-aggregation group;
- filters after aggregation but before isolated compositing;
- an explicit ordered stack, reverse stack or procedural operator execution order;
- typed transformations that choose their input/output data type and live inside the actual AE Timeline.
The actual BEE implementation must be audited for its own evaluation semantics. CNL's forward/reverse test is a proof of **CNL's** rules only; it is not a proof Adobe Shape content is rendered backward or forward universally.

## Next evidence gates in priority order

- Host test on a disposable selected existing Shape Layer: run the *updated* read-only "ChapeLayer: Inspect Native Contents Admission"; return TEMP/ChapeLayer_HostAdmission_ReadOnly.tsv.
- From this determine parent-specific admission and indexed ordering. **Do not** instantiate unknown-prefixed types yet.
- Prove the private TDB creator registration ABI in a fully mocked process, including cleanup and serialization/canonical initialization. No live registration without proven compatibility and user's explicit consent.
- Isolate a genuine owner registration route beyond fixed BEE_Layer::CreateLayerFromType. If none exists without host patching, record the hard impossibility of productizing this particular ABI on unmodified stock AE.
- Only then map Pen/Selection and VectorArt evaluator registry and native host Undo/replay.
- Phase F CompNodeAE integration remains prohibited until separate design review.

No existing AE project or CompNodeAE code modified. Only ShapeLayerAE files and AEIG research snapshot are authorized.
