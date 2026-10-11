---
status: research-active
last_verified: 2026-10-11
evidence: E2-L + E2-X + E0-H + H
versions: AE2025 and AE2026 native BEE/TDB runtime and AE2026 ShapeLayerAE v3
---

# Independent Native Vector Output — Ownership, Evaluation and Renderer Boundaries

## The central mismatch

CompNodeAE must create/emit editable geometry **as an effect without instantiating a separate ordinary Shape Layer**, and that geometry must appear in AE's regular native Timeline hierarchy, support Pen/Selection tools and render with the production Shape engine. Using AEGP to populate an existing Shape Layer, drawing a transient Comp UI overlay or returning pixel output does not count.

AE2026 v3 established:
1. An external AEGP can invoke the private **no-argument** `Get_AE_StreamFactory()` and receive a non-null pointer (no dereference). This is a narrow private-ABI proof.
2. `AEGP_CanAddStream` approves unknown `ADBE Vector Shape - ...`, `Graphic - ...`, and `Filter - ...` children under built-in Contents. This is admission, **not instantiation**.
3. AE's own 31 native Vector constructors are referenced in four bounded registration functions; these functions issue repeated `TDB_ScRegisterStreams::Register()` IAT calls. This is internal **type registration** evidence.
4. Native `BEE_VectorLayer::GetVectorArt` constructs a TDB path and `BEE_VectorArt::Group`, invokes `PopulateVectorArt` and `GetBounds`. This is the native intermediate geometry evaluation entry; a normal effect does not expose an equivalent output API.

## Four distinct contracts required for native CompNodeAE geometry

### A. Type registration is not parent ownership

`TDB_StreamFactory::RegisterFactoryFunc(matchName, std::function, bool)` gives an internal global creator registry. A valid callback could construct a TDB stream, but this does not place it in a host-owned Timeline tree. The parent `TDB_IndexedStreamGroup` may accept an element category by name independently of whether a concrete factory implementation exists.

`TDB_MatchName` objects passed to registration are references to static initialized runtime objects; corresponding image data can be zero-filled at rest. A creator callback also carries private C++ type, allocator, destructor and module-unload assumptions. A successfully generated native stream can still be uneditable or unserializable.

### B. Owner class vs general TDB stream

The native vector class families are separate:
- `BEE_VectorLayer` owns `BEE_VectorLayer::GetVectorArt` and `Rasterize2DGraph`.
- `BEE_VectorStream` evaluates authored Contents and operators into `BEE_VectorArt::Group`.
- `BEE_VectorArt::StreamBasedFilter(BEE_VectorLayer const&, TDB_StreamIDPath const&, T_Time const&)` explicitly binds a filter to **a native VectorLayer owner**, path identity and time.

No evidence yet supports substituting a normal **Effect** owner for `BEE_VectorLayer`. A BEE factory can create internal Shape-related TDB streams while still refusing them as children of `ADBE Effect Parade` (confirmed from real CanAdd outputs).

### C. Native Pen tool uses project selection identity

`BEE_GetSelectedShapePathsVec(BEE_Layer*, vector<TDB_StreamIDPath>*)` and `BEE_SelLayer::IsPathOrChildSelected(TDB_StreamIDPath const&)` belong to the host's selection subsystem, while `BEE_VectorArt::OriginInfo` includes authored/synthetic StreamID paths.

An evaluated path with the right geometric control points is not necessarily registered as a selectable, persistent editable host path. A custom Comp panel with draggable handles proves neither native Pen-tool interoperability nor Timeline selection identity.

### D. VectorArt is not an Effect SDK return type

The native evaluation sequence (direct CALL evidence in two runtime versions):

```text
BEE_VectorLayer::GetVectorArt(time, matrix, ...)
   |
   +--> BEE_VectorArt::Group constructed
   +--> TDB_StreamID / TDB_StreamIDPath constructed
   +--> BEE_VectorStream::PopulateVectorArt(...)
   +--> BEE_VectorArt::GetBounds(...)
      returns IntrusivePtr<BEE_VectorArt::Group>
```

The final Shape layer renderer uses `BEE_VectorLayer::Rasterize2DGraph(...)` returning `IntrusivePtr<RG_RenderNode>`. `BEE_VectorArt::Path` has constructors from `CAGMPath` and `CAIMBezierPath`. These are useful native vector intermediate types, but there is **no demonstrated public effect-output channel that returns a BEE_VectorArt object**. Creating such an object, even with correct internals, is different from making the host evaluate/cache/serialize/render it as an independent layer/effect.

## Strongest proof and next falsification gates

| Stage | Required direct evidence | Present state |
| --- | --- | --- |
| Factory existence | External AEGP can access host's factory accessor | **E2-X, read-only, achieved** |
| Parent grammar | Unknown Shape category passes existing native Contents admission | **E2-X, achieved** |
| Typed internal creators | Built-in Shape/Filter/Graphic Create references feed TDB register wrapper | **E2-L, strongly supported** |
| External *type registration* | Unique third-party match name registered and successfully unregistered, in disposable host | H, **not attempted** |
| Independent Effect-owned indexed Contents | No standard Shape Layer dependency, Timeline parent ID/child identity/Undo/save | H |
| AE native Pen/Selection | Native tool selects/edits custom geometry without custom overlay | H |
| AE production renderer | Custom BEE VectorArt consumed as native RG output before pixel materialization | H |
| Persistence/version | Reopen, undo/redo, cache correctness, AE2025 vs AE2026 binary compatibility | H |

Do not promote existence of an exported function, a Boolean capability check, a string-prefix rule or a successful private no-argument getter into later-stage claims. Conversely, the combination of discoveries justifies **further controlled investigation**, not premature dismissal of all private paths as impossible.

## Two practical branch hypotheses for CompNodeAE

**Branch 1 — Inject a native vector-producing stream:** uniquely register a stream class that evaluates to `BEE_VectorArt`. This requires a host vector-owner/evaluation dispatch contract and may be viable only under an existing Shape Layer, which would fail the stated independence goal.

**Branch 2 — Define a new native host owner:** create an independent BEE layer-like object with own native Contents and appropriate Tool/RG/Timeline interfaces. This could satisfy the goal but has substantially more ABI, project-serializer, ownership and UI dependencies, and no prototype yet.

Both branches should be researched in a **disposable AE environment** rather than installed into an active project's working plug-ins. The v3 plugin is strictly read-only, even when it invokes a private getter.

## Reproduction

- `F-VECTOR-010` — in-host private getter/CanAdd data
- `F-VECTOR-011` — built-in BEE stream creator registration callsites
- `F-VECTOR-012` — direct GetVectorArt->PopulateVectorArt->GetBounds path
- `experiments/vector-shape/EXP-SHAPE-009-010-v3-host-confirmation.md` — original 5 captures and SHA hashes
- `datasets/ae-vector-stream-creators-static-xrefs-2025-2026.json` and `datasets/ae-vector-creator-registration-bundles-2025-2026.json`
- `datasets/ae-vectorart-render-entry-calls-2025-2026.json`
