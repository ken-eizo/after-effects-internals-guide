# EXP-SHAPE-092 — Strict native Shape/Contents canonical child-name census across AE2025/AE2026

**Status: PASS offline static x64 RDX dataflow, 2 installed AE versions. No AE private function executed.**

## Goal and change from EXP-SHAPE-086

Previous parser counted 515 (2025) and 527 (2026) calls to `GetCanonicalStream` with a nearby known global match-name symbol, but failed to recognize Shape's `BEE_VectorStream::StreamName_*` globals. A permissive expanded script found 687/699 candidates but an independent RDX-dataflow check detected 7 potentially **stale** matches across both versions. This experiment eliminates misassociation by requiring the actual `RDX` definition reaching the TDB call, without overwrites/intervening function calls.

## Proven results

| Host binary | `FillInCanonicalUILayout` methods | Direct imported `GetCanonicalStream` CALLs | **Proven `LEA RDX` match-name references** | unresolved |
| --- | ---: | ---: | ---: | ---: |
| AE 2025 BEE.dll | 102 | 692 | **685** | 7 |
| AE 2026 BEE.dll | 104 | 701 | **694** | 7 |

`BEE_VectorStream::VectorsStreamGroup` provides **20 native Shape Contents canonical child types** in each release, with the same symbol order. Their names and per-call RVAs are recorded verbatim. No additional semantics are assumed for parent policy or actual class construction.

Offline source files:

- `experiments/vector-shape/probe-src/tools/census_bee_canonical_grammar_strict_rdx.py`
- `experiments/vector-shape/probe-src/tools/verify_strict_canonical_dataflow.py`
- `experiments/vector-shape/probe-src/tools/diff_canonical_shape_2025_2026.py`

Datasets:

- `datasets/ae-bee-canonical-grammar-strict-rdx-2025-2026.json`
- `datasets/ae-bee-canonical-grammar-2025-2026-diff.json`

## Reproduction

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\census_bee_canonical_grammar_strict_rdx.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_strict_canonical_dataflow.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\diff_canonical_shape_2025_2026.py"
```

Expected: both script checks PASS. The verifier independently checks original BEE.dll SHA and Capstone instruction stream for every recorded edge, real TDB IAT target, RDX argument dataflow with no overwrite and no intervening calls. It explicitly FAILS for stale/guessed child names.

**Safety and result scope:** All tests are offline Windows PE reads only, no AEX installation or private ABI invocation. The user requested that VirtualBox upgrade and VM construction be paused in favor of research; neither was performed.

**Product acceptance unchanged:** `NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM`. A recovered Adobe canonical parent layout and its native children do **not** grant third-party AEX permission to register a custom property class or group in the AE Timeline.

Finding: `research/findings/F-VECTOR-092-shape-contents-strict-canonical-child-schema-dataflow.md`.
