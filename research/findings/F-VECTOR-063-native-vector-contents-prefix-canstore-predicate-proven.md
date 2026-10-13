---
date: 2026-10-13
status: PASS cross-version executable code reconstruction / host 2026 corroborated
evidence: E2-L original installed BEE2025+BEE2026 code, RVA/literals and CRT import thunk + E2-X actual AE2026 public CanAddStream
---
# F-VECTOR-063 — The real native Shape Contents admission predicate is three prefix tests, independent of native creator and evaluator

## Previously unproven boundary now established with native code

F-VECTOR-009 had inferred but not proved prefix matching. The full native class predicate BEE_VectorStream::VectorsStreamGroup::CanStore(TDB_MatchName const&) has now been decoded in both installed AE2025 and AE2026 binaries and verified in machine-code form.

**It returns true for an initial special-case exact TDB_MatchName comparison OR any of the following prefixes:**

    ADBE Vector Shape -
    ADBE Vector Graphic -
    ADBE Vector Filter -

Both compiled implementations perform TDB_MatchName::GetName, pass the returned C string as the first argument and each literal as the second argument into the CRT function **strstr**. A direct comparison of the returned pointer to the original name buffer (CMP RAX,RBX) tests *prefix* equality. The initial exact-match special case is separate and its actual MatchName constant identity remains to be decoded. The code has no call to the TDB type factory and no call to the BEE evaluator registry.

- AE2025 CanStore RVA 0x700250; search thunk 0xCEACFE, bound to VCRUNTIME140.dll!strstr by native PE import mapping.
- AE2026 CanStore RVA 0x723C80; search thunk 0xD3BE2E, whose IAT target RVA 0xF19510 is the VCRUNTIME140.dll!strstr slot in the installed binary (also independently confirmed by dumpbin /imports).
- Three literal references each are recorded in the reproducible dataset. The exact native GetName -> strstr -> pointer comparison paths exist in both binaries.

The 2026 user's read-only TSV directly corroborates this:
- "ADBE Root Vectors Group" has grouping type INDEXED_GROUP and accepted unknown ADBE Vector Shape/Graphic/Filter-prefixed names (CanAdd=true, err=0).
- CNL:Forward, CNL:Reverse, CNL:Path all produced CanAdd=false, err=0.
- None of those unknown names was instantiated, so no independent CNL native Adobe Contents child was proven to exist.

**This is a structural discovery, not a stable extension contract**: the parental predicate is permissive on some future/unknown type IDs while the actual TDB factory and native BEE evaluator are independent and may not recognize those names at all. CanAdd true is therefore only an *admission* decision; it cannot validate creation, save/reopen, Undo, selection, or rendering. In particular, **do not call AEGP_AddStream on invented ADBE prefixes** in any irreplaceable AE project.

## Generalizable requirement for a new native Timeline grammar

Adobe's native Shape extension pipeline is split into at least:
1. Parent name/child-admission predicate (proven prefix-based in this owner).
2. Native per-MatchName TDB StreamType constructor and canonical child layout factory.
3. BEE_VectorStream per-MatchName geometry/graphic/filter evaluator registry.
4. BEE owner and editor (Pen, TDB_StreamIDPath, selection) and independently serializable layer type.
5. BEE_VectorArt→AGM/RG evaluation and lifetime.

A plug-in-defined grammar must implement all relevant contracts to be real, not a visual copy of Effects GROUP controls. The existence of 3 prefix namespaces is an **Adobe-internal classifier**, NOT a public plugin type-registration API.

## Reproduction

- experiments/vector-shape/probe-src/tools/verify_native_contents_prefix_canstore_full.py
- datasets/ae-vector-contents-canstore-full-predicate-2025-2026.json
- F-VECTOR-009 for earlier host CanAdd examples and unique-ID anomaly.
- EXP-SHAPE-063 full cross-binary result and exclusions.

All evidence was produced offline against installed BEE.dll; no private host call and no Adobe DLL patch. AEIG contains no copied Adobe DLL.
