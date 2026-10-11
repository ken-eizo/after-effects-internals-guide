---
status: research-active
last_verified: 2026-10-11
evidence: E2-L + E2-X (getter and CanAdd only) + H
versions: After Effects 2025/2026 installed binaries; SDK 25.6
---
# Native Vector Evaluator Registry — A Second Hidden Registration System

## Goal: native effect-owned vector output

The goal is for CompNodeAE to behave as a native editable vector producer **while remaining an effect**. Do not confuse that goal with creating an ordinary Shape Layer, copying paths into one, drawing in Custom UI, or emitting a raster `PF_World` from an effect. None of those satisfy independent Timeline Contents, native path tools and native renderer semantics.

Two distinct internal registries are now independently supported by evidence.

## Registry A — host-owned stream type factory

```text
TDB.dll!Get_AE_StreamFactory()
    └── TDB_StreamFactory
          └── TDB_ScRegisterStreams::Register(name, creator)
                └── RegisterFactoryFunc(name, std::function, bool)
                      ├── duplicate-key check and mutex
                      ├── CreateStream(name, ...) **during registration**
                      ├── canonical/initial instance
                      └── RegisterSeparatedDimensions, sometimes canonical registration
```

The external AEGP v3 read-only experiment **did invoke the no-argument getter and obtained a non-null pointer**. The pointer was never dereferenced and registration was never attempted. There is no public stream creator extension API here. Importantly, native registration *eagerly* creates a TDB stream, so it cannot safely be tested with a dummy callback or incomplete private object.

## Registry B — BEE's MatchName-keyed vector evaluator

Independent native binary analysis identifies a second global, initialized and owned by `BEE.dll`, holding a name-keyed ordered tree of polymorphic vector evaluator objects. Each BEE operator can be referenced through a MatchName and is called to materialize `BEE_VectorArt`.

```text
AE native VectorLayer owner
  └── TDB_StreamIDPath → FindStream → enumerate nested Vector Contents
        ├── IsActive / IsHidden / MatchName checks
        └── BEE evaluator registry::FindByMatchName
              ├── mode 0: PopulateVectorArt → operator vtable[+0x18]
              └── mode 1: StreamBasedFilter::DoFilter → vtable[+0x18]
                      ↓
               BEE_VectorArt::Group / Path / Graphics / Filters
                      ↓
               BEE_VectorLayer::Rasterize2DGraph → RG_RenderNode
```

Static evidence supports the two mode callsites; full class layouts, cache behavior, editor integration and external API stability **remain unresolved**. `BEE_VectorLayer` is the evaluator's owner and may be a non-substitutable class.

In AE2026, the BEE registrar exists at RVA `0x713120` (AE2025 `0x6eeb20`), and its registry singleton initialization at RVA `0x713550` (AE2025 `0x6eef40`). A native startup function performs TDB creator registration and BEE evaluator initialization. The evaluator registrar checks for duplicate names, installs reference-counted operator objects in its ordered tree, and the shutdown path releases them. This internal function is **not a publicly exported SDK method**.

## Exact 20 registered evaluators (AE2025 = AE2026)

| MatchName | Concrete MSVC RTTI type, namespace `BEE_VectorStream` |
| --- | --- |
| `ADBE Vector Filter - Trim` | `TrimOperator` |
| `ADBE Vector Filter - Offset` | `OffsetPathOperator` |
| `ADBE Vector Filter - PB` | `PuckerBloatOperator` |
| `ADBE Vector Filter - Repeater` | `RepeaterOperator` |
| `ADBE Vector Filter - Reveal` | `RevealOperator` |
| `ADBE Vector Filter - Merge` | `MergeOperator` |
| `ADBE Vector Filter - Roughen` | `RoughenOperator` |
| `ADBE Vector Filter - Wiggler` | `WigglerOperator` |
| `ADBE Vector Filter - Zigzag` | `ZigzagOperator` |
| `ADBE Vector Filter - RC` | `RoundCornerOperator` |
| `ADBE Vector Filter - Twist` | `TwistOperator` |
| `ADBE Vector Group` | `GroupOperator` |
| `ADBE Vector Shape - Group` | `ShapeOperator` |
| `ADBE Vector Shape - Rect` | `RectOperator` |
| `ADBE Vector Shape - Ellipse` | `EllipseOperator` |
| `ADBE Vector Shape - Star` | `PolyStarOperator` |
| `ADBE Vector Graphic - Fill` | `FillOperator` |
| `ADBE Vector Graphic - Stroke` | `StrokeOperator` |
| `ADBE Vector Graphic - G-Fill` | `GradientFillOperator` |
| `ADBE Vector Graphic - G-Stroke` | `GradientStrokeOperator` |

The correspondence is established for every entry from *literal text used in the static MatchName constructor* to the exact registrar callsite and *the MSVC RTTI of the C++ class constructed in that block*. Thus it is substantially stronger than guessing types from names. The same 20 names and classes were independently found in the two installed versions.

For path filter operators, intermediate RTTI includes `PathFilterOperatorT<TrimParams>`, `PathFilterOperatorT<OffsetPathParams>`, `PathFilterOperatorT<RoughenParams>`, etc. Most concrete operators have vtable RTTI metadata for subobject offsets 0 and 24 bytes: external subclasses must satisfy more than a single function pointer. No third-party operator has been constructed or called.

## What the experiments actually establish

| Contract | E2-X / E2-L result | Remaining obstacle |
| --- | --- | --- |
| External access to TDB global getter | **E2-X achieved**, getter returned non-null | Stable private method ABI and lifetime |
| Unknown Shape/Graphic/Filter names inside Contents | **E2-X achieved**, CanAdd=true | Object construction and persistence |
| TDB type creator registration | **E2-L**, Adobe native creator callbacks installed | Third-party reversible registration |
| BEE vector evaluator registration | **E2-L**, 20 concrete RTTI operators in its own registry | Third-party evaluators, cache and serializer |
| Editable Contents under an effect rather than Shape Layer | **Not shown** | Independent owner and Timeline identity |
| Native Pen/edit tools | **Not shown** | Host selection & editing binding |
| Native VectorArt->AGM/RG output from an effect | **Not shown** | Host vector-provider/output channel |

## Next research, kept separate by proof gate

First reconstruct TDB and BEE operator class ownership, vtable method semantics, registration timing, serialized descriptor creation and expected stream identity from static and read-only evidence. Next study native selection and Timeline owner acceptance. Only then may a **separate disposable AE session** be used for experimental native registration. Do not invoke an unknown-name `AddStream`, modify registry maps or inject callbacks into the working AE process.

The active ShapeLayerAE v3 remains the known read-only observatory; no v4 AEX/private registrar experiment was deployed by this research.

## Reproducibility

- `research/findings/F-VECTOR-013-tdb-eager-canonical-lifecycle.md`
- `research/findings/F-VECTOR-014-dual-native-vector-evaluator-registry.md`
- `research/hypotheses/H-SHAPE-006-dual-factory-evaluator-registration.md`
- `experiments/vector-shape/EXP-SHAPE-013-eager-factory-canonical.md`
- `experiments/vector-shape/EXP-SHAPE-014-vector-evaluator-registration.md`
- All static datasets and source-only `ShapeLayerAE/tools` copies are linked from the Findings. No Adobe DLL, SDK proprietary binary or private header has been redistributed.
