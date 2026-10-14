---
date: 2026-10-14
status: PASS isolated private-registration AEX offline build and safety-preflight static inspection only; NO in-host native registration; experimental AEX MUST NOT BE INSTALLED without separate explicit opt-in
evidence: E2-L MSVC Release x64 build, PE/PiPL and private export/fingerprint verifier, controlled-source inspection
---
# F-VECTOR-090 — Experimental native TDB registrar AEX is compiled, but live Adobe registration is still unproven and unsafe

## Existing native-ABI prototype

The separate source lab `D:/Developer/ShapeLayerAE/labs/native_tdb_registration_disposable` is a PRIVATE native-ABI registrar prototype, *not* the production-safe `CNLNativeShapeLayer.aex` or a finished native property.

It is specifically designed to attempt registering a synthetic `CNL Experimental Native ParamPath Registration ...` MatchName against a **real Adobe-owned** `TDB_ParamPathStream::Create` callback via the private `TDB_StreamFactory::RegisterFactoryFunc`, then request `UnregisterFactoryFunc`. It does not instantiate a new foreign C++ Stream subclass, and even a successful registration/rollback would prove only that the internal registry accepted a new name in a disposable session — **not** an independent native group or AE Timeline property.

The C++ callback ABI `(TDB_MatchName const&, TDB_StreamFactory*, bool, unsigned int, bool)` was corrected after an earlier dangerous ABI mismatch. The factory eagerly constructs native prototypes and may call virtual methods during registration. The private Adobe code can assert/crash or leave global state contaminated. No static checks can certify safe rollback.

## 2026-10-14 revalidation

- `python D:/Developer/ShapeLayerAE/labs/native_tdb_registration_disposable/verify_no_host_load.py` → PASS PE checks, with explicit warning **ZERO real host test, UNKNOWN safety, rollback NOT PROVEN**.
- `cmake --build D:/Developer/ShapeLayerAE/build/native_tdb_registration_disposable --config Release` → MSVC x64 Release build PASS.
- Experimental `CNLPrivateTDBDisposable.aex` SHA-256 `c91ffce77be481a394c243c0de64568487d3f24e5864cbba9376eaf1500b5622` (37 KB).
- Search in the normal installed AE 2026 and common MediaCore plugin folders found **no installed copy** of this dangerous experimental AEX.
- The existing source explicitly requires a new unsaved empty project, no active layer, no RQ, correct TDB image SHA/exports/opcodes, a one-shot file and environment variable. Even if all gates are true, an actual private call may still crash the host. A normal live AE instance remains off limits.

## Two-phase approval model

1. Static read-only ABI/build tests (already PASS) do NOT authorize execution of private `RegisterFactoryFunc`.
2. A separate **user-chosen, truly disposable and isolated AE instance** with no valuable projects and explicit consent to possible crash/global state loss is required before any mutating native-ABI test. Prefer actual sandbox/VM isolation, rather than relying solely on an empty project in the daily Adobe process.
3. If the user expressly approves such a risky isolated test, use the existing fail-closed AEX and collect stage-flushed journals. A register result must be followed by a verified clean host exit and new start; private-register/unregister success alone is not sufficient.
4. New host-owned Property/Group in standard Timeline, native keyframes, Undo, AEP roundtrip and macOS support all remain independent unmet product gates.

The ordinary `CNLNativeShapeLayer.aex` is a stable **read-only observer / CNL engine**. Do NOT replace its completed state with this unsafe prototype automatically.

## Status relative to goal

`NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM`: no new independent group in the standard AE Timeline, no external native Stream provider accepted and persisted. The status is a measured engineering boundary, not proof a private workaround is physically impossible.

Code remains in D:/Developer/ShapeLayerAE as requested; no Adobe installation files were modified or private registry mutation performed during this investigation.
