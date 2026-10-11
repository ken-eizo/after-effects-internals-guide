---
status: pass-static-no-registry-call
last_verified: 2026-10-12
evidence: E2-L
versions: pinned installed AE2025 / AE2026 TDB.dll
---

# EXP-SHAPE-027 — Native GUID MatchName and complete Adobe Path Creator static preflight

## Question

Can a known complete Adobe stream class allow a controlled new-unique-MatchName TDB factory admissibility test, avoiding an unsafe dummy plugin-supplied vtable? This static experiment prepares for the test but does NOT actually register a type.

## Read-only method and observations

Read two installed TDB DLLs via exact symbols + .pdata bounded Capstone disassembly. Source:
probe-src/tools/audit_tdb_builtin_creator_as_external_bootstrap.py and probe-src/tools/verify_tdb_matchname_guid_and_builtin_creator.py.

- TDB_MatchName(char*,bool) calls TDBp_MatchNamePool::GuidFromName and stores 16 bytes into the constructed object (both versions).
- TDB_ParamPathStream::Create allocates Adobe-native 0x468 bytes and calls TDB_DerivedStream<TDB_ParamPathStreamTraits> constructor.
- TDB_IndexedStreamGroup has its own native ctor and is NOT ParamPathStream.
- Factory RegisterFactoryFunc still performs eager CreateStream and native virtual checks, so real registration may assert/fail before returning.

Cross-validator PASS in both AE 2025 and 2026. Native project/registry untouched.

## Evidence and limitations

F-VECTOR-030/031.
datasets/ae-native-tdb-built-in-path-creator-registration-feasibility-2025-2026.json and ae-tdb-matchname-guid-and-built-in-path-creator-check-2025-2026.json.

External registration NOT PROVEN. True plugin-owned Contents/Pen editing/VectorArt NOT PROVEN. ParamPathStream is a parameter class, not a native vector provider.

## Next gate

Independent cross-module callback lifetime mock, compiled safe AEGP preflight, and only after explicit disposable-host authorization a manual-only version-pinned native test. Do not call private methods on user's currently running AE.
