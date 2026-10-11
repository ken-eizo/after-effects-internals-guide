---
status: compiled-NOT-runtime-tested-high-risk
last_verified: 2026-10-12
evidence: E2-B + E2-L + H
versions: exact AE2025/AE2026 TDB.dll source binary hashes; MSVC 2022
---

# F-VECTOR-033 — Gated private TDB type-registration AEX built, NOT validated in AE

## Actual goal, unproven

The true CompNodeAE objective is a new plugin-owned native editable Contents and VectorArt output. A smaller necessary preliminary test is: can an external AEGP register and then unregister a genuinely new MatchName in TDB_StreamFactory without using a Mask/Shape Layer or writing host executable memory?

For this test, Adobe's own completely constructed TDB_ParamPathStream::Create is chosen to isolate factory admissibility. This native parameter-path class is NOT a BEE vector Shape, plugin-controlled owner, editable Timeline Contents or native VectorArt object. **Even runtime success would not establish the larger goal.**

## What exists and what did NOT happen

A separate MSVC 2022 x64 AEGP binary was built successfully:

D:/Developer/ShapeLayerAE/build/native_tdb_registration_disposable/Release/CNLPrivateTDBDisposable.aex

It has a PiPL, a real AEGP EntryPointFunc, registered menu command and explicitly user-triggered private registration and immediate best-effort removal. The plugin includes no code path that registers types at AEGP startup or during render.

**It was NOT installed, NEVER invoked in AE, and has NO in-host result.** The PE static verifier confirms resource, exports, guarded source code and binary structure only. Source file:
experiments/vector-shape/native-tdb-registration-disposable-lab/CNLPrivateTDBDisposable.cpp

## Manual-only guard conditions, not a safety guarantee

- Exact SHA256 match for an inspected TDB.dll installed with AE2025/AE2026. Fail closed for any other binary.
- Existence of five precisely decorated private exports and the known getter instruction signature.
- No currently active AE layer.
- Explicit process env var CNL_TDB_DISPOSABLE_HOST_TEST=I_ACCEPT_PRIVATE_REGISTRY_CRASH_RISK.
- Correct one-time opt-in flag file in TEMP with an exact acknowledgment string. Flag is removed before private method calls and cannot be reused.
- Actual registration occurs only after all guards AND an explicit Animation menu click.
- Read-only preflight logs, flush after each dangerous stage; the new GUID MatchName is constructed using Adobe's private TDB_MatchName constructor.
- A real MSVC std::function creator forwards to TDB_ParamPathStream::Create; this uses Adobe's own allocator and complete class vtable rather than inventing an incomplete stream subclass.
- If native RegisterFactoryFunc returns true, attempt to call native UnregisterFactoryFunc for that same MatchName immediately.
- No Adobe BEE native registry, shape layer, mask object or project property is intentionally created.

**WARNING: guard conditions and unregister requests do not make private host ABI calls safe.** RegisterFactoryFunc may synchronously create a canonical object and call virtual methods that assert, corrupt memory, or leave stale entries before unregister can run; a successful unregister return may still leave native state. Do not execute in production AE or with a valuable project open. The proper next step is a separately authorized, isolated/disposable user experiment after the safe AEGP preflight succeeds; the user controls installation and AE UI. This research does not promise safety or successful registration.

## Evidence categories

- E2-L: F-VECTOR-026/027/030/031 verified registrar, eager CreateStream, native Stream factory and Guid-backed MatchName.
- E2-B: external MSVC ABI mock (EXP-SHAPE-029) passes cross-DLL/EXE callback retention and teardown; this is NOT proof of Adobe ABI.
- E2-B: gated risky AEX compiled and PE verified (dataset/ae-private-tdb-disposable-build-receipt-20261012.json).
- E2-X: **NOT TESTED**, no data or claim of actual Adobe type registration.

## Why this could be a large breakthrough, and why it still isn't one yet

If new external MatchName creation succeeds and cleans up correctly, it would show that Adobe's native type factory can accept external plugin-supplied registrations. That would be the first of many gates toward new plugin-authored native AE path/Contents and eventually CNL-defined procedural vector operators consumed by the standard vector renderer. It would not prove an independent native owner, native AE Pen/Selection binding, a BEE evaluator or RG renderer output.

Until a genuine in-host test and complete owner/editor/render integration: do not describe the experimental AEX as the new editable native vector plugin.
