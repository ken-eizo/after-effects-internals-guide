---
status: strongly-supported-static
last_verified: 2026-10-11
evidence: E2-L
versions: installed AE2025 and AE2026 BEE.dll
---
# F-VECTOR-016 — Native Path, Shape, Fill and Repeater operators stamp evaluated VectorArt with origin stream paths

## Source-to-evaluated-art trace, no longer just symbol-name correlation

From each evaluated BEE operator's concrete vtable methods, direct CALL targets in both installed versions reconstruct this path:

```text
TDB authored Shape / Rect / Ellipse Contents at evaluated time
    -> GetPathDataFromOM(OM_Shape&, CAIMBezierPath&)
       OR GetRectPathData(NamedStreamGroup,..., CAIMBezierPath&)
       OR GetEllipsePathData(...)
    -> BEE_VectorArt::Path(CAIMBezierPath, Usage)
    -> BEE_VectorArt::OriginInfo(TDB_StreamIDPath)
    -> BEE_VectorArt::BaseObject::SetOriginInfo(...)
    -> attach to BEE_VectorArt::BaseContainer children
```

Additionally, native Fill operator and native StreamBasedFilter wrappers construct and attach `OriginInfo(TDB_StreamIDPath)`. This is verified **inside concrete operator render/evaluation methods**, rather than inferring origin association from existence of the `OriginInfo` type.

### Repeater's synthetic paths are now tied to its actual algorithm

Previously hypothesis-only, `BEE_VectorArt::OriginInfo::AppendSyntheticIndex(unsigned)` is directly called at least **twice** inside the concrete `RepeaterOperator` geometry/filter implementation in each installed host version:

- AE2025 `RepeaterOperator` vtable primary slot5 RVA `0x6f12c0`, callsites to `AppendSyntheticIndex` RVA `0x6f13ea` and `0x6f1449`.
- AE2026 `RepeaterOperator` vtable primary slot5 RVA `0x7156d0`, callsites RVA `0x7157f2` and `0x71581b`.

Other direct calls in the same path construct `BEE_VectorArt::Group`, `BEE_VectorArt::SymbolGroup` and `OriginInfo(TDB_StreamIDPath)`, and call `SetOriginInfo` and `Group::SetAlpha`. This strongly supports the conclusion that **native repeated evaluated objects carry synthetic identifiers relative to their authored origin**, without creating independent authored Timeline streams for each copy.

### Important negative boundary

These facts demonstrate origin *stamping during art generation*, not yet proof that AE's Pen tool can select/edit a plugin-owned native shape. `BEE_SelLayer` and `BEE_Selection` use native `TDB_StreamIDPath`, but the exact editor hit-test -> selected authored stream mapping still requires an independent runtime or deeper static trace. Effects' PF_World raster output is not a native vector object output.

### Raw evidence and reproducer

- `datasets/ae-vector-operator-vectorart-provenance-calls-2025-2026.json`
- `experiments/vector-shape/probe-src/tools/audit_vector_operator_art_provenance.py`
- Baselines `research/findings/F-VECTOR-005-origin-identity-and-native-selection.md` / `F-VECTOR-006-native-selection-origin-synthetic-callsite.md` (historical descriptions should be read alongside this promoted finding).

## Independent internal consistency gate

A separate source-only verifier (`experiments/vector-shape/probe-src/tools/verify_native_vector_operator_evidence.py`) validated the two-year evidence chain: all 20 unique MatchNames and concrete classes are aligned between data sets; both versions have 9/11 mode split and primary/secondary RTTI vtables; Path/Rectangle/Ellipse geometry-to-OriginInfo call sequences exist; Repeater's vtable slot5 has two or more direct `AppendSyntheticIndex` calls in each installed version. The command **passed** on the local evidence, with JSON receipt `datasets/ae-vector-operator-independent-crosscheck-2025-2026.json`. It verifies agreement among multiple static analyses, **not** an external AE plug-in integration or a live host behavior.
