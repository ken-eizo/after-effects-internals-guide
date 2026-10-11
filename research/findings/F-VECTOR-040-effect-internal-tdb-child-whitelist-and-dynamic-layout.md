---
status: cross-version-offline-verified-no-live-registration
last_verified: 2026-10-12
evidence: E2-L
versions: pinned AE2025/AE2026 FLT.dll and TDB.dll
---

# F-VECTOR-040 — Effect-internal Contents admission is TDB whitelist; UI layout has a dynamic append method

## Problem

F-VECTOR-039 proved `FLT_Parade::CanStore` requires a real `FLT_FCSeqSpec`-compatible **top-level effect child**. It does NOT determine what type of **path or group inside an existing effect** can be stored. We followed the `FLT_FCSeqSpec`'s actual secondary TDB subobject, rather than reusing the unrelated Effect Parade RTTI check.

## Exact ABI evidence — both installed versions

The exported `TDB_StreamGroup::CanStore(TDB_MatchName const&)` is in its native vtable at **slot 56**. In both AE2025 and AE2026, the native `FLT_FCSeqSpec` **TDB_NamedStreamGroup subobject** vtable slot 56 points to a local FLT.dll JMP thunk whose IAT target is `TDB.dll!?CanStore@TDB_StreamGroup@@UEBA_NAEBVTDB_MatchName@@@Z`. This establishes that effect-internal stream group admission uses the **generic TDB group predicate**, not `FLT_Parade::CanStore` and not a `FLT_FCSeqSpec` subtype requirement for each parameter.

Native `TDB_StreamGroup::CanStore` disassembly reveals an actual loop over a vector of candidate child match names. It copies a `TDB_MatchName` and calls `TDB_MatchName::operator==` against entries, advances 8 bytes per entry and returns a boolean depending on whether a match was found. Exact code crosscheck passed in 2025/2026. This makes type admissibility **parent-specific**, in addition to global TDB factory registration. The vector's acquisition is observed from native stream-group fields, but its complete mutation/ownership contract is not yet proven.

## Native effect layout creation boundary

The exported `FLT_FCSeqSpec::FillInCanonicalUILayout` in both versions is a tiny **no-op RET**, proven by examining the true entrypoint and stopping before the next independent function. Initial disassembly that continued into subsequent unrelated functions falsely attributed two `TDB_GetCanonicalStream` calls to this method; this mistake was detected and corrected in the reproducible script.

`FLT_FCSeqSpec::AddStreamToUILayout` is a separate native method. Its compiled body calls imported `TDB_StreamGroup::GetUILayout`, consistent with the group's UI-child list being extended through an independent native path. A bounded .text direct-CALL scan found zero direct calls to the exported AddStreamToUILayout entry within FLT.dll in both versions. This is only a scoped negative result: method calls may be virtual, indirect, or originate in a different module. There is **no demonstrated third-party API to modify this layout**.

`FLT_FCSeqSpec` additionally provides `GetChildParamDef` (calls `TDB_StreamBase::GetParamDef`) and `GetParamTable`. This suggests a relationship with PF effect parameter definitions but does not prove that arbitrary newly defined CNL streams can be inserted, serialized or edited by AE.

## Practical impact and next falsification

We have now separated two independent native contracts:

1. **Effect Parade accepting an entire effect**: FLT_FCSeqSpec canonical RTTI (F-VECTOR-039).
2. **An existing effect accepting its own child stream**: TDB_StreamGroup allowed-name vector + per-effect dynamic UI/parameter definitions (this finding).

A viable plugin-owned Contents implementation should first discover which supported effect parameter or nested group registration path, if any, can lawfully extend the existing effect's TDB child layout. Only after a child has a legal MatchName, canonical type, parent, Undo, save/reopen identity should we pursue the native Pen source callbacks and the separate BEE_VectorArt/RenderGraph delivery. Mask/Shape Layer carriers do not satisfy the goal.

Never infer that direct native vtable modification, hardcoded 0x210 offsets, or calling a private append method is safe. No AE native mutation, external TDB factory registration, Pen tool hook or vector render was achieved.

## Reproducibility

- `datasets/ae-flt-fcseqspec-nested-canstore-2025-2026.json`
- `datasets/ae-tdb-streamgroup-canstore-whitelist-2025-2026.json`
- `datasets/ae-flt-effect-canonical-layout-2025-2026.json`
- `datasets/ae-flt-effect-dynamic-layout-verification-2025-2026.json`
- `datasets/ae-flt-effect-addlayout-direct-calls-2025-2026.json`

Source read-only scripts mirrored in `experiments/vector-shape/probe-src/tools/`: verify_flt_fcseqspec_nested_canstore.py, verify_tdb_group_canstore_whitelist.py, audit_flt_effect_canonical_layout.py, verify_flt_effect_dynamic_ui_layout.py and trace_flt_addlayout_calls.py.
