---
status: observed-static-only
last_verified: 2026-10-11
evidence: E2-L
versions: installed AE2025 / AE2026 BEE.dll
---
# EXP-SHAPE-016 — Concrete native Shape operators convert Bezier geometry and stamp source origin; Repeater adds synthetic identities

## Question

Do actual Shape/Rect/Ellipse/Fill/Repeater evaluator methods create independent native vector geometry **and** preserve the authored `TDB_StreamIDPath` as their origin? Is Repeater the producer of synthetic indices?

## Method

Starting from the exact concrete C++ RTTI vtables recovered in EXP-SHAPE-014/015, disassemble primary function slots 4–7 for Path Group, Rect, Ellipse, Fill, Trim and Repeater. Resolve direct BEE and TDB symbols through exported table/IAT for AE2025 and AE2026; preserve function boundary and CALL site in JSON. No private code was executed.

## Observation

- `ShapeOperator` uses `BEE_VectorArt::GetPathDataFromOM(OM_Shape,... CAIMBezierPath&)`, then `BEE_VectorArt::Path`, `OriginInfo(TDB_StreamIDPath)` and `SetOriginInfo`.
- `RectOperator` and `EllipseOperator` similarly call `GetRectPathData` and `GetEllipsePathData` to build `CAIMBezierPath`, then a native Path and origin metadata.
- `FillOperator` and generic `StreamBasedFilter` attach authored path origin information to evaluated objects.
- `RepeaterOperator` concrete algorithm directly calls `OriginInfo::AppendSyntheticIndex(unsigned)` twice within an operation that also constructs `Group`, `SymbolGroup`, changes `Group::SetAlpha`, and calls `SetOriginInfo`.
- Both installed host versions show the corresponding native call chains, with version-specific RVAs documented in F-VECTOR-016.

## Limits

Origin stamping is not itself selectable/hit-test proof. This does not establish a foreign effect-owned VectorArt origin, Pen edit support or independent persistent native Contents. An observer must not present this offline disassembly as an in-host third-party extension test.

## Reproduce

Run `tools/audit_vector_operator_art_provenance.py`. Dataset `ae-vector-operator-vectorart-provenance-calls-2025-2026.json` preserves CALL instructions, resolved exported names and per-operator function RVAs in both builds.

## Independent internal consistency gate

A separate source-only verifier (`experiments/vector-shape/probe-src/tools/verify_native_vector_operator_evidence.py`) validated the two-year evidence chain: all 20 unique MatchNames and concrete classes are aligned between data sets; both versions have 9/11 mode split and primary/secondary RTTI vtables; Path/Rectangle/Ellipse geometry-to-OriginInfo call sequences exist; Repeater's vtable slot5 has two or more direct `AppendSyntheticIndex` calls in each installed version. The command **passed** on the local evidence, with JSON receipt `datasets/ae-vector-operator-independent-crosscheck-2025-2026.json`. It verifies agreement among multiple static analyses, **not** an external AE plug-in integration or a live host behavior.
