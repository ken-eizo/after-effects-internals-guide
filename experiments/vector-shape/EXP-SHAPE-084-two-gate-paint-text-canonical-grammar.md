# EXP-SHAPE-084 — Two-gate native property type + parent canonical grammar

**Status: PASS offline static AE2025 and AE2026 BEE/TDB. External custom provider still NOT DEMONSTRATED.**

## Hypothesis

The `AEGP_CanAddStream` decision is not merely a test of stream type registration. For built-in Paint/Text, a parent group explicitly constructs a canonical layout of permitted children and the default TDB virtual `CanStore` checks that list.

## Direct evidence

- `BEE_PaintStrokesGroup` vtable slot #56 resolves through BEE import thunk to `TDB.dll!TDB_StreamGroup::CanStore` in BOTH versions.
- vtable slot #57 resolves to `BEE_StrokesGroupBase::FillInCanonicalUILayout`; it references `BEE_StreamGroupName_PAINT_ATOM` and imports `TDB_StreamBase::GetCanonicalStream`.
- `TDB_StreamGroup::SetupCanonicalLayout` invokes virtual slot #57 and calls `SetUILayout`.
- `TDB_StreamGroup::CanStore` iterates a stored list and compares candidate `TDB_MatchName` with equality function.
- Equivalent #56 / #57 structure checked for `BEE_TextAnimatorStreamGroup`, `BEE_TextSelectorsStreamGroup` and `BEE_TextAnimatorPropertiesStreamGroup`.
- Text Selector canonical children include four Adobe matchnames (Range, Wiggly, Levels and Expressible selector variants).
- `TDB_ScRegisterStreams::Register` calls `TDB_StreamFactory::RegisterFactoryFunc` as the **separate type registration gate**.
- Cross-check actual in-host Paint receipt F-VECTOR-083: `ADBE Paint Atom` TRUE, five other tested names FALSE.

## Reproduction

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_paint_two_gate_canonical_policy.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_paint_text_common_grammar.py"
```

Expected: 2/2 versions PASS in each script, four Paint/Text classes per version in the second verifier. Evidence is offline read-only and SHA-pinned. **No native foreign type created or registered.**

Details: `research/findings/F-VECTOR-084-tdb-native-two-gate-paint-text-canonical-policy.md`.
