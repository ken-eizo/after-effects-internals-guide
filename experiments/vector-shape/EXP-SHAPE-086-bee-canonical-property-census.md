# EXP-SHAPE-086 — Automatic BEE native canonical-property grammar census

**PASS offline:** installed AE2025 / AE2026 PE export + Capstone static analysis. No AE host private code executed.

`FillInCanonicalUILayout` functions: AE2025 **102**, AE2026 **104**. Recognized child references through imported `TDB_StreamBase::GetCanonicalStream` and nearby BEE-exported MatchName globals: **515** / **527**.

This is a **conservative subset** of all possible children. In AE2026, 174 `GetCanonicalStream` callsites are unmatched by the export-name lookback, including most Shape `VectorsStreamGroup` children. Only bounded direct instruction evidence is emitted, not an exhaustive UI grammar or a positive result for custom third-party registration.

## Reproduction
```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\census_all_bee_canonical_grammar.py"
```

Dataset: `datasets/ae-bee-canonical-grammar-census-2025-2026.json`. Detailed analysis: `research/findings/F-VECTOR-086-automatic-bee-canonical-property-grammar-census.md`.

No Adobe binaries patched, no project mutations, no direct call into private Adobe APIs; ChapeLayer host-native new-type registration still unresolved.
