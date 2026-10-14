---
date: 2026-10-14
status: PASS offline static multi-family BEE canonical stream grammar census AE2025/AE2026
evidence: E2-L SHA-pinned installed Windows BEE.dll, complete dumpbin exports, Capstone disassembled native instructions and exact imported TDB_GetCanonicalStream calls
---
# F-VECTOR-086 — Automatic AE native canonical property grammar census (Paint/Text/Shape/Layer)

## Goal

Scale F-VECTOR-084 from selected Paint and Text groups to **all exported `FillInCanonicalUILayout` methods** in installed Windows AE BEE.dll binaries. This is not a user-interface replacement and does not execute any private Adobe functions.

## Actual offline results

| Measure | AE2025 | AE2026 |
| --- | ---: | ---: |
| Exported `FillInCanonicalUILayout` methods enumerated | **102** | **104** |
| Direct `GetCanonicalStream` child references mapped to an exported BEE match-name symbol | **515** | **527** |
| Fill methods with zero identified named child reference | 42 | 42 |
| `GetCanonicalStream` calls not mapped to an exported name by the conservative lookback | 177 | 174 |
| Paint-named methods / recognized references | 7 / 44 | 7 / 44 |
| Text-named methods / recognized references | 13 / 168 | 13 / 169 |
| Vector-named methods / recognized references | 29 / 58 | 29 / 59 |
| Layer-named methods / recognized references | 23 / 93 | 24 / 98 |

The family headings overlap (e.g. Layer includes a VectorLayer); their counts must **not** be summed. Each reference is a discovered static callsite, **not a unique Stream type or a proven legal child in every live host context**. Some methods contain conditional branches, obsolete stream migration, optional features or inline names.

The 2026 export set adds two `FillInCanonicalUILayout` owners not found in 2025's audited set:
- `BEE_DisplacementOptionsStreamGroup`
- `BEE_LayerCredentialIDStream`

Count differences also include `BEE_AVLayer`, `BEE_VectorLayer`, `BEE_TextMoreOptionsStreamGroup` and several parametric mesh group methods. Changes in recognized calls alone do **not** prove UI-breaking schema changes without checking conditions/semantics.

## Proven mechanism and coverage boundaries

The extractor:
1. Enumerates full PE exports using `dumpbin /exports` (no truncated `pefile` export enumeration).
2. Locates 102/104 exported functions named `FillInCanonicalUILayout`.
3. Disassembles their unwind-defined function extents with Capstone.
4. Detects **actual call instructions** through the imported `TDB.dll!TDB_StreamBase::GetCanonicalStream`.
5. Associates each call with a nearby RIP-relative reference to an **exported** `BEE_StreamGroupName_*` or `BEE_StreamName_*` constant.
6. Records raw method names, RVAs, known child labels, exact instruction addresses, and unmatched-call counts for each AE version.

**Known limitations:** The lookback intentionally recognizes exported BEE globals only. Some Shape/Vector groups use internal or nonexported match names, so their calls are counted as unmatched (e.g. `VectorsStreamGroup@BEE_VectorStream` has 20 canonical lookups but none resolved to this export subset in AE2026). Therefore `527` is a **lower bound on directly recognized callsite relationships**, not a full exhaustive property schema.

For exact native parent admission, combine with F-VECTOR-084's vtable and `CanStore` evidence; not all parents use default TDB CanStore, and the parent may also implement prefix-based acceptance or explicit host conditions.

## Reproduction

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\census_all_bee_canonical_grammar.py"
```

Expected from installed AE2025 and AE2026: 102/104 exported methods, 515/527 recognized relationships. Source outputs JSON in the separate `D:/Developer/ShapeLayerAE/labs/paint_native_properties_audit` research lab; the pinned result is committed in:

`datasets/ae-bee-canonical-grammar-census-2025-2026.json`.

Cross-reference F-VECTOR-080 to 085 for Paint AEX, BEE/TDB registrar, Paint Suite, actual AE2026 Paint native hierarchy, two-gate native parent admission and v2 leaf inspector.

No host project mutation, no new native foreign Property registration and no unsupported calls occurred during this census.
