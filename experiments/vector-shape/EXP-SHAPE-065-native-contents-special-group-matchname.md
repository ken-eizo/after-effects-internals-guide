---
date: 2026-10-13
status: PASS special builtin Group MatchName proven in both installed native BEE binaries
evidence: E2-L x64 native global MatchName ctor + CanStore equality reference
---
# EXP-SHAPE-065 — Resolve initial special CanStore MatchName object

The native Shape child-admission predicate had one unexplained exact TDB_MatchName equality in addition to three prefix checks. Following the RIP-relative reference to the same global object from both CanStore and the native TDB_MatchName initializer gives:

2025 initializer RVA 0x1C030, special global 0x15EF420, CanStore ref 0x700263, native literal "ADBE Vector Group".
2026 initializer RVA 0x1B760, special global 0x169FDF0, CanStore ref 0x723C89, native literal "ADBE Vector Group".

Thus native built-in VectorsStreamGroup::CanStore has a full four-clause naming rule: exact "ADBE Vector Group", startswith("ADBE Vector Shape -"), startswith("ADBE Vector Graphic -"), startswith("ADBE Vector Filter -"). Three prefix checks were established in EXP-SHAPE-063; this resolves special group identity. This is name admission, not a TDB creator or BEE evaluator factory; custom native classes are not yet supported.

Verifier PASS AE2025 and AE2026. No Adobe host operation or binary edit. Full F-VECTOR-065.
