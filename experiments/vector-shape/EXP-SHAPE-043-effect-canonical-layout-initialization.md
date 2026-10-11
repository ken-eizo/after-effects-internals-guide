---
status: pass-static-cross-version-NOT-host
last_verified: 2026-10-12
evidence: E2-L
---

# EXP-SHAPE-043 — Native Effect Canonical UILayout setup and derived class population

## Question

A registered new `TDB_StreamBase` MatchName cannot become a top-level `FLT_Parade` child unless its canonical object is an `FLT_FCSeqSpec` (F-VECTOR-039). What is the DIFFERENT child-admission condition for native parameters *inside* an already existing `FLT_FCSeqSpec` effect?

## Method

Read exact installed AE2025/2026 FLT.dll and TDB.dll as static PE images. Resolve the `TDB_NamedStreamGroup` vtable and its native `TDB_StreamGroup::CanStore` slot, then locate the corresponding `FLT_FCSeqSpec` TDB subobject slot. Decode the FLT `FF25` thunk and its IAT import name (do not infer from source class hierarchy). Independently disassemble `TDB_StreamGroup::CanStore`, `TDB_StreamGroup::SetupCanonicalLayout`, `FLT_FCSeqSpec::FillInCanonicalUILayout`, `FLT_EffectBuiltInParams::FillInCanonicalUILayout`, `FLT_CompoundEffect::FillInCanonicalUILayout`, `TDB_NamedStreamGroup::FillInStreamsFromCanonicalLayout` and relevant native Creator functions.

## Exact results

PASS both pinned versions:

- Native `FLT_FCSeqSpec` TDB-side vtable index **56** resolves through an actual FLT import jump to `TDB_StreamGroup::CanStore`.
- Canonical-child membership is checked through the shared collection fields at `TDB_StreamGroup+0x210/+0x218`, using `TDB_MatchName::operator==`.
- Native `TDB_StreamGroup::SetupCanonicalLayout` invokes class-specific `FillInCanonicalUILayout` at vtable offset `+0x1c8`, then separated-dimensions setup and `SetUILayout`.
- Bare `FLT_FCSeqSpec::FillInCanonicalUILayout` is a 1-instruction return; `FLT_EffectBuiltInParams` has 3 (2025) / 4 (2026) direct canonical-stream getter calls, and `FLT_CompoundEffect` has 2 in each version.
- No host calls, code patches, plugin installation, stream registration, foreign callbacks or runtime mutations occurred.

## Remaining blocker and next experiment

Identify where ordinary third-party Effect `PF_ParamDef` schemas are materialized as `TDB_StreamBase` canonical children, and whether AE provides any legal dynamic group-child interface under that owner. Do NOT assume global TDB creator registration updates the owner's allowed child list. A candidate native path still must have editable IDPath/selection and a genuine BEE VectorArt renderer, which are separate unfulfilled gates.

Source-only verifier: `verify_flt_nested_contents_admission.py`. Full PE disassembly and vtable evidence: three JSON datasets cited in F-VECTOR-042. No private mutation is recommended; run the separate public-only `CNLNativeOwnerAdmission.aex` manually if host evidence is required.
