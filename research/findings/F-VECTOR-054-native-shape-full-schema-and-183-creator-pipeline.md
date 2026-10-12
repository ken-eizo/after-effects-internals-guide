---
status: cross-version-verified-native-binary-reconstructed; third-party-registration-not-proven
date: 2026-10-12
evidence: E2-L pinned installed AE2025/AE2026 BEE.dll, TDB.dll exports
---

# F-VECTOR-054 — Complete BEE Shape Layer / Root Vectors / Contents schema, 183 typed registration sites, 20 evaluation types

## User requirement

The mission is **not** a plain Effect plug-in, custom Drawbot path editor, raster effect or copy into an Adobe Shape Layer. Discover and leverage Adobe's true native TDB/BEE Shape system so that independently authored CNL types could someday become new editable native Contents / owners / operators with AE's own Timeline hierarchy, selection, Pen, Undo and vector renderer.

The user's CNL Owned Vector Document **has rendered and survived a saved-project close/reopen in real AE2026**. This confirms an effect-owned PF Arbitrary value and raster rendering, but is *not* an independent AE native Shape/Contents type. Further ordinary Effect UX work was deprioritized to focus on this structural blocker.

## Breakthrough: typed BEE initialization consists of 183 direct TDB registration CALL sites

Following the **actual exported** `BEE_VectorLayer::RegisterStreams` x64 jump trampoline, its first initializer phase, three separate helper functions, and their imported `TDB_ScRegisterStreams::Register` references reveals these sites in **both installed AE2025 and AE2026 BEE.dll**:

| Initialization body | Native TDB typed Creator registration CALL sites | Primary examples |
| --- | ---: | --- |
| Base property registration | 55 | Vector Filter keys including Trim/Offset/Repeater |
| Vector property registration | 47 | Vector Fill/Stroke keys |
| Shape operator registration | 19 | Freeform path/Rect/Ellipse/Star and additional group entries |
| `BEE_VectorLayer::RegisterStreams` first phase | 62 | Shape's typed groups, `BEE_VectorLayer::Create`, 3D vector material attributes |
| **Total code sites** | **183** | **Not 183 guaranteed runtime registrations** |

The first and fourth stage have conditionals, so counts mean **statically present CALL instructions** not necessarily 183 calls under every host feature flag. The original 62-stage block includes `TDB_StreamFactory::SetupCanonicalStream`, and its distinct destructor/unload branch includes `TDB_ScRegisterStreams::UnregisterAll`. Neither method can safely be borrowed blindly by an external AEX. The subsequent initialization stage installs a **separate 20-key BEE polymorphic evaluator registry**.

These typed MatchName globals are **exactly reconcilable**: all 20 native evaluator keys can be found as explicit MatchName arguments to these four TDB-registration stages. They include 11 `ADBE Vector Filter - ...` keys, four `ADBE Vector Graphic - ...` keys, four `ADBE Vector Shape - ...` keys, and the `ADBE Vector Group` key. This establishes a code-level relationship between data constructors and native shape evaluators; it does **not** mean a new foreign type has been inserted.

## Recovered true three-level native Shape schema (both versions)

We parsed the **real C++ virtual** `FillInCanonicalUILayout` code and imported `TDB_StreamBase::GetCanonicalStream` calls of:

1. `BEE_VectorLayer::FillInCanonicalUILayout` — **10 children in AE2025, 11 in AE2026**.
2. `BEE_VectorStream::VectorStreamGroup::FillInCanonicalUILayout` — **four children in both**.
3. `BEE_VectorStream::VectorsStreamGroup::FillInCanonicalUILayout` — **20 children in both**.

We joined each literal pointer with the **native MatchName static initializer** in the exact PE image (not name guesses).

Real canonical hierarchy:

```text
BEE_VectorLayer (actual native owner; AE layer type 4)
├── ADBE Marker
├── ADBE Root Vectors Group                ← canonical native root for VectorStreamGroup
│   ├── ADBE Vector Blend Mode
│   ├── ADBE Vectors Group                  ← canonical native Contents group
│   │   ├── ADBE Vector Group
│   │   ├── ADBE Vector Shape - Group        (freeform Path)
│   │   ├── ADBE Vector Shape - Star
│   │   ├── ADBE Vector Shape - Rect
│   │   ├── ADBE Vector Shape - Ellipse
│   │   ├── ADBE Vector Graphic - Fill / G-Fill / Stroke / G-Stroke
│   │   └── ADBE Vector Filter - Trim / Offset / PB / Repeater /
│   │       Reveal / Merge / Roughen / Zigzag / RC / Twist / Wiggler
│   ├── ADBE Vector Transform Group
│   └── ADBE Vector Materials Group
├── ADBE Mask Parade
├── ADBE Effect Parade
├── ADBE Transform Group
├── ADBE Layer Styles
├── ADBE Extrsn Options Group
├── ADBE Material Options Group
├── ADBE Audio Group
├── ADBE Layer Sets
└── ADBE Layer Credential ID               ← present in AE2026 only
```

The full list, canonical native ordering, source instruction RVA, raw MatchName object RVA, source native DLL SHA256 and host version appear in the linked datasets. **The 20 Contents types and four Root Vectors children have identical order in AE2025 and AE2026.** The layer's one extra AE2026 canonical child is precisely `ADBE Layer Credential ID`.

Native linkage from the typed Creator table:

- Native `ADBE Root Vectors Group` is one of the two typed MatchNames accepted by `BEE_VectorStream::VectorsStreamGroup::Create` (the other is `ADBE Vectors Group`); **both share the same C++ factory callback pointer**. This is native C++ object construction, not an AEGP stream enumeration trick.
- `ADBE Vector Group` is constructed by `BEE_VectorStream::VectorStreamGroup::Create`; the exact same MatchName is passed to `TDB_StreamFactory::SetupCanonicalStream`.
- `ADBE Vector Transform Group` and `ADBE Vector Materials Group` have separate native Creator callbacks in the same native 62-entry registration table.
- Native owner root `BEE_VectorLayer` has its own `Create` callback and typed `BEE_StreamGroupName_VECTOR_LAYER`, proving the Shape owner is a distinct created class.

These class names are similarly spelled but semantically distinct (`VectorStreamGroup` versus `VectorsStreamGroup`). The precise native child relationships are a major prerequisite to attaching a genuinely foreign type.

## What breaks a simplistic independent plug-in attempt

1. **Owner factory**: `BEE_Layer::CreateLayerFromType` is a closed native eight-case switch in both versions (F-VECTOR-037). Registering a new MatchName doesn't cause a new layer class to be instantiated. A new CNL-native owner route must be identified beyond this dispatcher.
2. **Contents admissibility**: `VectorsStreamGroup::CanStore` has native Shape/Graphic/Filter prefix logic (F-VECTOR-009). But passing `CanAddStream` is not proof that a constructor exists.
3. **Typed factory**: `TDB_StreamFactory::RegisterFactoryFunc` eagerly calls creator paths / canonical construction; external CNL registration must satisfy exact private C++ ABI, class layout, serializer, cleanup and safe owner lifetime. The disposable private probe is **not approved for in-host execution**.
4. **Evaluator**: BEE holds an additional, independent 20-key polymorphic `BEE_VectorStream` evaluator registry. A TDB stream alone does not produce VectorArt.
5. **Selection/Undo/RG**: The Pen tool operates on real `BEE_StreamSpec(BEE_Layer*,TDB_StreamIDPath)`; RG/AGM needs host-owned `BEE_VectorLayer::Rasterize2DGraph` or an independently valid renderer route. Neither a Shape Layer carrier nor a custom Effect CPU renderer suffices.

This is **verified native-internal architecture, not a finished external plug-in**. No original Adobe runtime functions were called, no AE binaries modified and no experimental registry mutation or GUI installation performed. `CompNodeAE` and Phase F remain untouched.

## Reproduce

Pure offline static extractors in `experiments/vector-shape/probe-src/tools/`:

- `audit_vector_layer_bootstrap_three_phases.py`
- `resolve_native_vector_62_tdb_creators.py`
- `recover_native_vector_183_tdb_registrars.py`
- `recover_native_shape_contents_canonical_schema.py`
- `recover_native_vector_canonical_matchname_literals.py`
- `verify_vector_layer_native_schema_bootstrap.py`
- `verify_native_vector_three_level_canonical_schema.py`
- `verify_native_shape_canonical_hierarchy_named.py`

Machine-readable evidence in `datasets/ae-bee-native-*.json` described by EXP-SHAPE-054. No vendor DLL is distributed.
