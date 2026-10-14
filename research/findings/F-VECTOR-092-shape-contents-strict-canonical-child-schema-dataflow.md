---
date: 2026-10-14
status: PASS AE2025+AE2026 offline strict x64 native canonical-children dataflow proof; no third-party native stream registered
evidence: E2-L BEE.dll installed SHA pin, full dumpbin exports, Capstone, TDB_GetCanonicalStream IAT, RDX direct argument verification, independent replay
---
# F-VECTOR-092 — Shape Contents native canonical child grammar recovered; corrected strict x64 callsite census

## Purpose and relationship to F-VECTOR-086

F-VECTOR-086 scanned exported `FillInCanonicalUILayout` methods and counted 515 canonical child-name references in AE2025 and 527 in AE2026. It missed most Vector/Shape children because their exported native globals are **scoped under BEE_VectorStream** and named `?StreamName_...@BEE_VectorStream@@`, rather than the global `?BEE_StreamName_...` pattern.

The revised parser recognizes four symbol-name families: `?BEE_StreamGroupName_`, `?BEE_StreamName_`, `?StreamName_`, and `?StreamGroupName_`. It verifies each candidate against a *real* PE IAT call to `TDB.dll!TDB_StreamBase::GetCanonicalStream`.

An independent verifier then checks that the name is **loaded directly into RDX (Windows x64 second argument)** using a RIP-relative `LEA RDX,[RIP+...]`, that the caller targets the actual TDB import, and that no intervening instruction overwrites RDX or CALL invalidates the argument. This dataflow check identified seven ambiguous associations in the preliminary expanded census, which were rejected rather than silently counting them.

## Measured data (Windows)

| Measure | AE2025 | AE2026 |
| --- | ---: | ---: |
| Exported `FillInCanonicalUILayout` functions inspected | 102 | 104 |
| Actual `TDB_GetCanonicalStream` import CALL sites in these functions | 692 | 701 |
| **Direct RDX-proven native child MatchName references** | **685** | **694** |
| Unresolved CALL sites (not guessed) | **7** | **7** |
| Vector-named parent methods / proven child references | 29 / 222 | 29 / 223 |
| `BEE_VectorStream::VectorsStreamGroup` proven children | **20** | **20** |

**Count definition:** Each evidence item is one x64 CALL site to `TDB_StreamBase::GetCanonicalStream` that has a directly proven `RDX` argument referencing an exported native match-name object. It is NOT a count of distinct classes, not a count of UI nodes in a project, and not a guarantee that each such child may be independently added by the user. Calls may be conditional or specialized.

### 20 directly enumerated Shape Contents child kinds

AE2025 and AE2026 show the **same 20 symbol names in the same order** from `VectorsStreamGroup@BEE_VectorStream::FillInCanonicalUILayout`:

| Symbol suffix | Native Shape/Contents concept |
| --- | --- |
| VECTOR_GROUP | Group |
| SHAPE_GROUP | Bezier Path |
| POLY_STAR_GROUP | Polystar |
| RECT_GROUP | Rectangle |
| ELLIPSE_GROUP | Ellipse |
| FILL_GROUP | Fill |
| GRADIENT_FILL_GROUP | Gradient Fill |
| STROKE_GROUP | Stroke |
| GRADIENT_STROKE_GROUP | Gradient Stroke |
| TRIM_GROUP | Trim Paths |
| OFFSET_PATH_GROUP | Offset Paths |
| PUCKER_BLOAT_GROUP | Pucker & Bloat |
| REPEATER_GROUP | Repeater |
| REVEAL_PATH_GROUP | Reveal Paths |
| MERGE_PATH_GROUP | Merge Paths |
| ROUGHEN_GROUP | Roughen Paths |
| ZIGZAG_GROUP | Zig Zag |
| ROUND_CORNER_GROUP | Round Corners |
| TWIST_GROUP | Twist |
| WIGGLER_GROUP | Wiggle Paths |

This is a list of **native exported typed references passed to TDB's canonical getter**. The exact user-visible names and completeness of each nested group's schema require separate host UI evidence. See earlier F-VECTOR-063/065 for the `BEE_VectorStream::VectorsStreamGroup::CanStore` prefix-based admission semantics; it **does not** automatically accept a new foreign factory.

### Cross-release native schema differences in identified exported child references

Comparing the sets of direct RDX-proven native child references yields eight parent-class differences, all additions in the audited set:

| Native canonical parent | Additional AE2026 child |
| --- | --- |
| `BEE_ConeMeshOptionsStreamGroup` | `CONE_INVERT_SLICE` |
| `BEE_CylinderMeshOptionsStreamGroup` | `CYLINDER_INVERT_SLICE` |
| `BEE_DisplacementOptionsStreamGroup` (new parent) | `DISPLACEMENT_INTENSITY`, `SUBDIVISION_COUNT` |
| `BEE_MaterialOverrideLayer` | `DISPLACEMENT_OPTIONS` |
| `BEE_SphereMeshOptionsStreamGroup` | `SPHERE_INVERT_SLICE` |
| `BEE_TextMoreOptionsStreamGroup` | `TEXT_VARIABLE_FONT_SPACING` |
| `BEE_TorusMeshOptionsStreamGroup` | `TORUS_INVERT_SLICE` |
| `BEE_VectorLayer` | `LAYER_CREDENTIAL_ID` |

These deltas come from static named references, **not** a guarantee that every new child appears in every user-visible configuration. `BEE_LayerCredentialIDStream` and `BEE_DisplacementOptionsStreamGroup` also appeared in the list of newly exported canonical-layout owners identified by F-VECTOR-086.

## Impact on third-party host-native plugin design

- It is now possible to automatically recover almost all *export-named* canonical child references across Paint, Text and Shape; **Shape Contents has 20 traced native member classes in both releases**.
- The parent grammar is not the factory registry. `TDB_ScRegisterStreams::Register` and `TDB_StreamFactory::RegisterFactoryFunc` still need a compatible private creator; parent `CanStore` admission is a separate gate. A plugin-provided class cannot be inferred from BEE's own built-in child references.
- Extending an existing Shape parent's category with a new MatchName may pass prefix `CanStore`, but without a creator, editor, serializer and ownership path there is no new timeline object.
- Nothing in this experiment proves a supported external `TDB_StreamBase` provider, a true AE-owned foreign Named/Indexed Group, or save/reopen/render/Undo.
- No private Adobe API executed or installed Adobe binary modified; user requested pausing VM construction, and VirtualBox 5.2.20 remained unchanged.

## Reproducibility

Lab working copies: `D:/Developer/ShapeLayerAE/labs/paint_native_properties_audit`. AEIG contains copy-pinned scripts and datasets:

- `experiments/vector-shape/probe-src/tools/census_bee_canonical_grammar_strict_rdx.py`
- `experiments/vector-shape/probe-src/tools/verify_strict_canonical_dataflow.py`
- `experiments/vector-shape/probe-src/tools/diff_canonical_shape_2025_2026.py`
- `datasets/ae-bee-canonical-grammar-strict-rdx-2025-2026.json`
- `datasets/ae-bee-canonical-grammar-2025-2026-diff.json`

To reproduce on the installed original Windows AE2025/AE2026 binaries (requires `pefile`, `capstone`, Visual Studio `dumpbin`):

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\census_bee_canonical_grammar_strict_rdx.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_strict_canonical_dataflow.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\diff_canonical_shape_2025_2026.py"
```

Expected: 685/692, 694/701, strict dataflow check 100% of identified references, exactly 20 Shape Contents canonical children in each version.

Primary source is the installed original BEE.dll in each AE version, **not** any reconstructed Adobe source code.
