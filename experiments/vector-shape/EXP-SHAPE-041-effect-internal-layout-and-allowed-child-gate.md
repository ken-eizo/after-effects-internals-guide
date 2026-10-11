---
status: pass-offline-two-pinned-native-builds
last_verified: 2026-10-12
evidence: E2-L
---

# EXP-SHAPE-041 — Effect-internal child match-name whitelist and dynamic UI append

The objective is to determine whether a custom native Path nested INSIDE an already existing effect must itself be an FLT_FCSeqSpec. Static x64 analysis proves that it does not have the same parent-type test as the outer Effect Parade.

For both installed versions, the FLT_FCSeqSpec secondary TDB_NamedStreamGroup virtual table's slot 56 resolves to an imported TDB_StreamGroup::CanStore. This predicate scans child MatchNames with exact TDB_MatchName::operator== and returns whether the proposed name belongs to the group's allowed child set. Consequently TDB Factory registration and a child's parent acceptance are separate barriers.

FLT_FCSeqSpec::FillInCanonicalUILayout in both versions is a one-instruction empty RET, whereas AddStreamToUILayout calls TDB_StreamGroup::GetUILayout. A direct-call search inside FLT.dll found zero calls to the AddStreamToUILayout entry; this does not exclude virtual or foreign-module calls. GetChildParamDef and GetParamTable exist but their precise dynamic parameter admission coupling remains unproven.

Standalone static crosschecks both PASS and evidence is in F-VECTOR-040 and datasets/ae-flt-* and ae-tdb-streamgroup-*; re-run mirrored scripts from experiments/vector-shape/probe-src/tools. This is an offline result, NOT a registered plugin-native effect-owned Contents tree, editor or renderer.

Future host-side observations may be gathered only with the new read-only EXP-SHAPE-039 AEGP (user installs), which compares existing built-in Effect and Shape/AV stream parents using the same candidate names. Do not run CNLPrivateTDBDisposable.
