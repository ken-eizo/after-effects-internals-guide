---
status: pass-compiled-and-static-verified-NOT-host
last_verified: 2026-10-12
evidence: E2-B + E2-L
---

# EXP-SHAPE-033 — Live-code export fingerprint and unsaved-project-only safety gates (offline)

## Research question

Can a disposable AE native-TDB registration prototype refuse both saved, clean projects and patched/incompatible in-memory private entrypoints, while preventing another private attempt during the same loaded plugin instance? Can these requirements be tested offline without executing Adobe's private registrar?

## Procedure

1. Inspect SDK25.6 AEGP ProjSuite6::AEGP_GetProjectPath and MemorySuite1's lock/unlock/free contract. Update shared NativeProjectSafety.h to reject missing/failed results and nonempty UTF-16 project paths.
2. Extract exact exports and first 16 bytes from the pinned installed TDB.dll PE images using `ShapeLayerAE/tools/audit_tdb_native_entry_fingerprints.py`. No DLL is loaded or called.
3. Insert fail-closed live-memory code fingerprint comparison for getter/constructor/path creator/register/unregister in the isolated experiment AEX, in addition to existing full-file hash, export-presence and getter opcode checks.
4. After one-shot explicit acknowledgment, repeat public SDK project test; atomically record one private ABI attempt per loaded plugin instance.
5. Retain native `std::function` callback signature and unregistration attempt; add post-attempt read-only public gate and an explicit `private_registry_rollback_proven=0` result.
6. Compile both dependent AEX targets (safe host preflight and dangerous disposable experiment) with VS2022 x64 Release. Run `verify_no_host_load.py`, MSVC exact decorated callback symbol test `verify_symbol_abi.py`, and native ABI model CTest. Do **not** install, launch AE UI or invoke Adobe private registry methods.

## Result

- Compiled v3 `CNLPrivateTDBDisposable.aex` and rebuilt read-only `CNLNativeVectorHostProbe.aex` successfully.
- `verify_no_host_load.py` passed, including exact 5-entrypoint x 2-version PE-byte crosscheck against hardcoded live memory checks. SHA-256 of v3 mutating AEX is recorded in `datasets/ae-private-tdb-disposable-v3-build-receipt-20261012.json`.
- Cross-module mock CTest passed (1/1), and independently compiled MSVC `std::function` decorated type still matches actual AE2025/2026 TDB private RegisterFactoryFunc exports.
- Runtime host tests of **these updated binaries did not occur**; the previous successful v1 safe getter/Bezier test must not be presented as v3 validation.

## Failure gates still unresolved

- Cannot prove private maps, cache, canonical stream and retained callbacks completely cleared after unregister. A true rollback condition is unknown.
- Cannot assume actual AE runtime uses unmodified entry code; only a future read-only in-host preflight could confirm loaded fingerprints. The compiled verification proves expected comparisons, NOT live equality.
- A private registrar call can crash even if every guard passes. Do not authorize dangerous AEX based on these static results alone.
- No independent Contents owner, AE native Pen editor or BEE VectorArt renderer has been connected.

## Evidence and reproducibility

- `experiments/vector-shape/native-tdb-registration-disposable-lab/CNLPrivateTDBDisposable.cpp`
- `experiments/vector-shape/native-tdb-registration-disposable-lab/verify_no_host_load.py`
- `experiments/vector-shape/host_abi_shared/NativeProjectSafety.h`
- `experiments/vector-shape/probe-src/tools/audit_tdb_native_entry_fingerprints.py`
- `research/findings/F-VECTOR-035-private-tdb-runtime-fingerprint-and-unsaved-project-gates.md`

This experiment is a risk-reduction measurement, **not** a safety certification. The plugin must remain off production AE installations.
