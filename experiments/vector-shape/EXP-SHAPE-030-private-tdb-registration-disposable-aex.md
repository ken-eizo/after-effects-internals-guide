---
status: compiled-dangerous-NOT-host-tested
last_verified: 2026-10-12
evidence: E2-B + H, E2-X unobserved
versions: pinned AE2025/AE2026 TDB.dll hashes; MSVC x64
---

# EXP-SHAPE-030 — Staged disposable private TDB new-MatchName registration AEX

## Purpose

Investigate whether a completely Adobe-built TDB_ParamPathStream Creator can be installed by an external AEGP under a new CNL MatchName in a disposable AE process and explicitly unregistered immediately. No Mask/Shape Layer is generated, no custom TDB_StreamBase vtable fabricated, and there is no BEE VectorArt output.

## What was actually built

CNLPrivateTDBDisposable.aex compiled as a separate AEGP:
D:/Developer/ShapeLayerAE/build/native_tdb_registration_disposable/Release/CNLPrivateTDBDisposable.aex

Source: experiments/vector-shape/native-tdb-registration-disposable-lab. PiPL, EntryPointFunc and x64 binary statically checked. Source contains guarded real calls to private TDB_MatchName constructor, RegisterFactoryFunc, built-in TDB_ParamPathStream::Create callback and UnregisterFactoryFunc.

**Actual runtime call COUNT: ZERO. No host installed, no AE GUI interaction or Adobe host test.**

## Mandatory safety gate

- No private registry calls during startup.
- Only user manual Animation > CNL Private TDB: Disposable Type Registration (DANGER).
- Exact installed native TDB binary SHA256 fingerprint and exported symbol+getter opcode checks.
- No active AE layer, explicit environment opt-in string, separate one-shot disposable file opt-in, consumed before any private calls.
- Log flushed BEFORE every dangerous step under %TEMP%/CNL_PrivateTDB_Disposable_Test.tsv.
- If register returns true, explicitly attempt native unregister for same MatchName immediately; a successful return does not prove host cleanup safety.

## WARNINGS

Do not use in a production host, working project or before the safe AEX preflight completes. Native private API may crash AE, leave persistent in-memory state, corrupt caches or fail during canonical eager construction. No safe rollback has been proven, and even a successful unregister return is insufficient evidence of correctness. This is an isolated user-controlled research experiment, not a production feature.

## Evidence and next gate

Datasets/ae-private-tdb-disposable-build-receipt-20261012.json; F-VECTOR-033.
No runtime result. If user explicitly authorizes a disposable host run, record logs and clean shutdown. Even an accepted registry type does not demonstrate independent Contents owner, Pen editing, BEE evaluator or native VectorArt/RG output.
