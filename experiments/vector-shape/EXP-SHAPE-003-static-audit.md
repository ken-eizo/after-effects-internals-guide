---
status: observed-static-only
last_verified: 2026-10-11
evidence: E2-L
versions: AE 2025 binary-index corpus
---
# EXP-SHAPE-003 — Static factory/vector boundary inventory

## Question

What architecture-relevant identifiers are present in the AE 2025 runtime symbol dataset? Do not interpret symbol occurrence as successful private API invocation, factory registration or full causal execution trace.

## Reproduction

1. Run `python D:\Developer\ShapeLayerAE\tools\audit_symbols.py`.
2. Inspect `D:\Developer\ShapeLayerAE\results\static_symbol_audit.json`.
3. Archive an exact copy to `experiments/vector-shape/runs/EXP-SHAPE-003/static_symbol_audit.json`.

Input: `datasets/ae-2025-vector-shape-symbols.csv`; SHA-256 `484cb6882928b52f34d27f5e2be5004508b52cf70270e10902708004543b70bb`. Records (excluding CSV header): **2517**.

Output: `runs/EXP-SHAPE-003/static_symbol_audit.json`; SHA-256 `04f10deeda3f0e068edff27c79022539eaccb1fa3000db6f51a95c40b1eae478`.

## Reproducible pattern hits

| Symbol substring | Rows | Evidence scope |
| --- | ---: | --- |
| `TDB_StreamFactory` | 79 | Constructor-like factory parameter references within `BEE.dll` |
| `TDB_MatchName` | 120 | Identifiers in BEE stream-related symbols |
| `BEE_GenericShapeStream` | 18 | BEE generic shape class symbols |
| `BEE_VectorStream` | 1452 | BEE vector stream classes/functions |
| `PopulateVectorArt` | 1 | Named stream-to-art evaluation symbol |
| `BEE_VectorArt` | 208 | Evaluated vector-art class symbols |
| `OriginInfo` | 24 | Provenance-like type symbols |
| `Rasterize2DGraph` | 3 | Vector layer raster graph function symbols |
| `C_AGMDLTranslatePort` | 9 | AGM/display-list translation symbols |
| `COR_NewAGMPort` | 2 | Bridge import/export symbol records |

Counts are **substring hits, not independent objects, calls, modules, or confirmations**. Categories overlap; source is one binary-index corpus, not multiple independent evidence paths.

## PE export/RVA and bounded disassembly cross-check

A second **read-only** tool, `D:\Developer\ShapeLayerAE\tools\audit_bee_disasm.py`, parsed the locally installed `BEE.dll` and correlated exact RVA addresses from the AEIG dumpbin corpus. The inspected binary SHA-256 is `98c682351e30f38cb7021eaa142f5ec473aea92885e14915d87c157cda971730` and its PE export table reports 13647 entries. Among the selected symbols were `BEE_GenericShapeStream` constructor variants at RVA `0x2ACC0` and `0x2ACF0`, `BEE_VectorStream::PopulateVectorArt` at `0x6ECB60`, and `BEE_VectorLayer::Rasterize2DGraph` at `0x6E3E90`. Six short entrypoint instruction windows were decoded with Capstone; this is **not** a control-flow graph or host execution trace.

The saved artifact is `runs/EXP-SHAPE-003/bee_private_surface_probe.json`, SHA-256 `21d9f8d8cc2017fb7e54350fbf44cf6e2d93902f6cdaaa3b6471530995b6677a`. Export names in the dumpbin inventory were used for RVA matching because the local `pefile` reader returned `None` for some longer decorated names. This difference is an instrumentation/parsing limitation, not evidence that the functions are missing.

## Interpretation

The runtime contains distinct named objects for factory-associated streams, evaluated vector art, and raster/display-list translation. This supports *investigating* the factory/evaluation/render boundaries and corroborates F-VECTOR-002 at the artifact level, but does not prove an externally extensible factory, any native Contents registration path, or injection of a plugin-created object into native tooling/rendering.

## Remaining work

Static call-site analysis, factory registration ownership, selection-tool target identity and real AE in-host stream inspection. No `E2-X` result exists in this experiment yet. Observable host results must be captured in a separate experiment before claiming native extensibility.
