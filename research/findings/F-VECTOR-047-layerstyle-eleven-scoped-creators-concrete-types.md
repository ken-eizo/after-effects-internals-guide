---
status: cross-version-static-verified
date: 2026-10-12
evidence: E2-L
versions: pinned installed AE2025/26 BEE.dll
---

# F-VECTOR-047 — Layer Style's eleven temporary TDB registrations are eight value streams and three groups

F-VECTOR-046 found eleven real `TDB_ScRegisterStreams::Register` calls during Adobe's Layer Style XML initialization. This experiment now follows the exact `LEA RAX` function-pointer captured into each `std::function` callback and disassembles its **actual native constructor calls**, rather than inferring types from MatchNames alone.

**Both pinned AE versions have the exact same category breakdown:** 8 registrations allocate and construct `TDB_Stream` value stream objects; 3 registrations call Adobe's concrete group constructors `BEE_LayerStyleStream::AdvancedBlendingStreamGroup`, `BlendingOptionsStreamGroup`, and `RootLayerStyleStreamGroup` (in this order among the three group entries, corresponding to index 6, 9 and 10 of the eleven). Separate `LayerStyleStreamGroupParser::CreateEffectGroup` constructs `IndLayerStyleStreamGroup` through the XML parser's virtual group-creation contract; it is **not** one of these eleven static registered callback identities.

This is positive architectural proof that Adobe builds a native Layer Style schema from both leaf and group factories before creating canonical instances and filling parent UILayout. It does **not** imply that `TDB_Stream` leaf values are custom vector geometry, that every registered canonical class can safely be created after `UnregisterAll`, or that third-party AEX code may register arbitrary groups through this private factory.

## Reproduction

`experiments/vector-shape/probe-src/tools/audit_layerstyle_registered_type_sources.py` records the exact two-version RIP-relative register callback sources; `audit_layerstyle_concrete_creator_classes.py` maps those targets to actual native constructor calls; `verify_layerstyle_scoped_creator_types.py` checks the category breakdown and three concrete group classes for both versions. Datasets:

- `datasets/ae-layerstyle-eleven-registration-sources-2025-2026.json`
- `datasets/ae-layerstyle-eleven-concrete-creator-types-2025-2026.json`
- `datasets/ae-layerstyle-eleven-creator-type-verification-2025-2026.json`

Native hosts not loaded or modified; no private runtime registration executed. F-VECTOR-045/046 provide related owner and lifetime contracts.
