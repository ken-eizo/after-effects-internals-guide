---
date: 2026-10-13
status: PASS cross-version binary traversal structure; final compositor order still open
evidence: E2-L actual installed BEE2025/BEE2026 machine instructions
---
# EXP-SHAPE-062 — Prove BEE VectorArt indexed-child traversal order

Two exact installed native binaries were disassembled at the BEE recursive VectorArt source walker:
- 2025 0x6EC3C0–0x6EC63E
- 2026 0x710790–0x7109EA.

Both perform xor esi,esi -> get group count through virtual +0x168 -> cmp esi,eax -> pass esi as indexed child in RDX to virtual +0x190 -> recurse/dispatch -> inc esi. This proves ascending native child stream visitation before/during VectorArt materialization.

Distinct from a final visible stacking rule: native Graphic/Filter evaluators may act on accumulated geometry, and RG/AGM rendering is another stage. F-VECTOR-014 established normal vs StreamBasedFilter evaluator dispatch as independent modes.

Offline verifier PASS for both versions. Not a native CNL layer or proof of CNL evaluator registration. No Adobe process run, no project mutation. Code and structured evidence archived in AEIG.
