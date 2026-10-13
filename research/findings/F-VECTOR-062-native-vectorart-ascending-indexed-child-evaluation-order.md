---
date: 2026-10-13
status: PASS native x64 executable order in AE2025 and AE2026
evidence: E2-L actual installed BEE.dll, Capstone disassembly of recursive PopulateVectorArt helper
---
# F-VECTOR-062 — BEE VectorArt traverses indexed Contents in ascending child order; final draw order is a separate contract

The actual native recursive BEE_VectorStream::PopulateVectorArt helper was disassembled on two installed version-pinned AE builds.

AE2025 helper RVA 0x6EC3C0–0x6EC63E; AE2026 RVA 0x710790–0x7109EA.

Both native implementations use equivalent logic:

    xor esi, esi                    ; child index = 0
    loop:
      call qword ptr [rax + 0x168]  ; native virtual child count
      cmp esi, eax                 ; compare child index with count
      jae exit
      mov edx, esi                 ; child index argument
      mov r8d, 1
      call qword ptr [rax + 0x190]  ; retrieve indexed child
      ... append child to TDB_StreamIDPath, apply predicate/dispatch ...
      ... evaluate child or recursively descend into child group ...
      inc esi                      ; next child index

The code visits native children in authored index order 0,1,2,... subject to active/hidden/group predicates. This is independently verified static executable instruction order, not an inference from the Shape UI.

| Machine-code site | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| initialize index=0 | 0x6EC48A | 0x71084E |
| group virtual count, slot 0x168 | 0x6EC496 | 0x710856 |
| index < count comparison | 0x6EC49C | 0x71085C |
| index argument in RDX | 0x6EC4AD | 0x71086D |
| indexed child virtual fetch, slot 0x190 | 0x6EC4B2 | 0x710872 |
| increment index | 0x6EC5D6 | 0x710982 |

## Separation that matters for custom ChapeLayer operator groups

The native stream tree walker order is NOT the same claim as final fill/stroke display order. Earlier F-VECTOR-014 shows a separate BEE MatchName-to-polymorphic-operator registry with two dispatch modes (normal populate mode0 and StreamBasedFilter::DoFilter mode1). F-VECTOR-002 and 012 show a separate BEE_VectorArt::Group/Path/Graphic/Filter object graph and subsequent AGM/RG render materialization.

A genuinely plugin-defined native hierarchy therefore requires four separate extensible contracts:
1. Author-defined typed child grammar and insertion policy.
2. Indexed stream traversal and scoped recursive group semantics.
3. Per-operator state reducer: geometry, graphic, filter, scope/isolation, evaluation-mode dispatch.
4. Actual native vector output compositor / RenderGraph.

The newly compiled ChapeHierarchyRules supports #1 and a CNL-only configurable forward/reverse *evaluation trace*. It does NOT prove #3/#4 or host-native CNL stream registration. Do not extrapolate that Adobe universally paints its SVG/AGM final pixels in ascending index order.

## Reproducibility

Verifier: experiments/vector-shape/probe-src/tools/verify_vectorart_recursive_traversal_order.py
Machine-readable dataset: datasets/ae-bee-vectorart-indexed-native-child-traversal-2025-2026.json
Private working script: D:/Developer/ShapeLayerAE/tools/disassemble_vectorart_recursive_order.py
No private API execution or AE host mutation.

## Next discriminating host experiment

On a disposable selected stock Shape Layer, insert two native paths, Fill, Stroke, one modifier and a nested Group; use the updated public read-only ChapeLayer admission probe to capture child order, then compare visually before/after moving the graphic or modifier in a user-controlled fixture. It will distinguish actual BEE rendering operator behavior from source traversal. No attempt to AEGP_AddStream unknown custom MatchNames.
