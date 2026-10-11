---
status: strongly-supported-static
last_verified: 2026-10-11
evidence: E2-L, with separate E2-X TDB getter and CanAdd support
versions: installed AE2025/AE2026 BEE.dll/TDB.dll
---
# F-VECTOR-014 — Separate BEE MatchName-keyed vector evaluator registration and 20 concrete native operator classes

## The unexpected second registration substrate

Adobe's built-in TDB type factory and BEE's geometry operator registry are **two distinct native registries**. Their registration and evaluation call paths are separable by direct 2025/2026 disassembly:

```text
BEE initialization
   ├── BEE_VectorLayer/VectorStream typed creators -> TDB_ScRegisterStreams::Register
   └── BEE-owned native geometry evaluator registry
           -> MatchName -> reference-counted operator object
           -> virtual evaluation method
BEE_VectorLayer::GetVectorArt -> PopulateVectorArt -> recursive stream traversal
    -> find per-MatchName evaluator -> evaluator virtual table +0x18, mode 0
BEE_VectorArt::StreamBasedFilter::DoFilter
    -> same registry lookup -> same vtable +0x18, mode 1
```

The BEE evaluator lookup is a name-keyed tree; the native registrar performs a duplicate check, allocates a tree node (0x38 bytes AE2026) and stores the operator instance in the node. Singleton setup allocates a registry object (0x18 bytes) and tree head, and shutdown traverses and releases objects. Calls into this registrar are direct BEE internal calls, **not exported public ABI**.

| Evidence | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| Evaluator registry constructor | `0x6eef40` | `0x713550` |
| Evaluator registrar | `0x6eeb20` | `0x713120` |
| Evaluator MatchName lookup | `0x6f9020` | `0x71cc00` |
| Lookup from vector evaluation | `0x6ecd81` | `0x711081` |
| Lookup from vector filter | `0x6cc9a0` | `0x6f15f0` |
| Native evaluator initial registration CALLs | 20 | 20 |

These specific sites are code-location receipts, not stable version-independent API addresses.

## All 20 registered evaluator names and concrete RTTI classes

Recovered from **static text literals -> TDB_MatchName initializer -> registry callsite -> same callsite's MSVC vtable RTTI** in each installed version:

| MatchName | Concrete BEE_VectorStream C++ evaluator |
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

Filter subtypes also expose intermediate RTTI `PathFilterOperatorT<TrimParams>`, `PathFilterOperatorT<OffsetPathParams>`, `PathFilterOperatorT<PuckerBloatParams>`, `PathFilterOperatorT<RoughenParams>`, `PathFilterOperatorT<ZigzagParams>`, `PathFilterOperatorT<RoundCornerParams>`, and `PathFilterOperatorT<TwistParams>`.

Most derived operators have MSVC RTTI vftables at offsets **0 and +24 bytes** within the object, indicating multiple polymorphic subobject views. This is observed ABI metadata and must not be treated as an externally supported class definition. Names, offsets and callsite linkages were reproduced for **both AE2025 and AE2026**.

## Boundary conditions

1. `AEGP_CanAddStream` accepting unknown prefixed names only proves **parent admissibility**, not a factory producer and certainly not a renderer evaluator.
2. TDB type creation alone cannot be assumed to generate VectorArt: a second BEE operator registry is used on the native evaluation path.
3. Both lookups pass the owner/context `BEE_VectorLayer`, not a general Effect SDK geometry socket.
4. No independent CompNodeAE-owned vector tree, standard Pen tool support, plugin-created evaluated VectorArt or renderer handoff has been demonstrated.
5. Registry insertion may not be thread-safe for third-party insertions, may depend on early bootstrap, and non-exported C++ ABI can change; do not attempt on an active AE project.

## Evidence corpus

`datasets/ae-native-vector-evaluator-registration-records-2025-2026.json`
`datasets/ae-vector-evaluator-matchname-identities-2025-2026.json`
`datasets/ae-native-vector-evaluator-vtable-rtti-2025-2026.json`
`datasets/ae-native-vector-evaluator-registry-lifecycle-2025-2026.json`
`datasets/ae-native-vector-populate-recursive-helpers-2025-2026.json`
`datasets/ae-vector-evaluator-registry-xrefs-2025-2026.json`
`datasets/ae-vector-evaluator-matchname-xrefs-2025.json` and `...2026.json`.
