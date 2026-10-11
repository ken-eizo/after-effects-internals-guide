---
status: strong-offline-abi-verified
last_verified: 2026-10-12
evidence: E2-L + E2-B
versions: installed AE2025 and AE2026 TDB.dll; compiled MSVC 2022 x64
---

# F-VECTOR-034 — Corrected private TDB Creator callback signature and native MSVC type verification

## Why previous experimental AEX must NOT be used

A code review found an actual signature mismatch. The fifth parameter of the original CNL callback was unsigned int, but Adobe's private TDB_StreamFactory::RegisterFactoryFunc accepts a C++ std::function whose Creator signature is TDB_StreamBase*(TDB_MatchName const&, TDB_StreamFactory*, bool, unsigned int, bool).

The last parameter MUST be bool, not unsigned int. The previous source also used void* in the erased function signature where the native ABI specifies exact C++ pointer types. These are not innocuous cosmetic differences. Even if x64 register sizes appear compatible, they compromise type safety and should be corrected before any host experiment.

The corrected source now uses forward-declared TDB_StreamBase and TDB_StreamFactory, plus a version-pinned, 16-byte GUID-backed TDB_MatchName façade, exact bool/unsigned int/bool callback parameters, and a TDB_StreamBase* return pointer.

## Direct compiler-level symbol evidence (both AE builds)

Compile original NativeABISignatureProbe.cpp with MSVC2022 into COFF OBJ. Examine the exact C++ decorated symbol using dumpbin /symbols. The complete parameter-type suffix is compared against Adobe's RegisterFactoryFunc exported name found using dumpbin /exports on BOTH installed AE2025 and AE2026 TDB.dll binaries.

Exact common parameter suffix:
AEBVTDB_MatchName@@V?$function@$$A6APEAVTDB_StreamBase@@AEBVTDB_MatchName@@PEAVTDB_StreamFactory@@_NI2@Z@std@@_N@Z

undname confirms the native callback is TDB_StreamBase*(TDB_MatchName const&, TDB_StreamFactory*, bool, unsigned int, bool). The independent MSVC-compiled function's suffix matches both Adobe binaries byte-for-byte. This verifies the intended std::function TEMPLATE TYPE at the symbol level; it does NOT prove that Adobe accepts late third-party registrations, or that class ownership/allocator and host unload behavior is correct.

## Public-SDK project isolation guard

The previous unsafe AEX only checked that there was no selected layer. A project can contain many unselected footage files and compositions, so this was insufficient.

New shared NativeProjectSafety.h uses ONLY official AEGP suites. It requires:
- exactly one accessible project;
- ProjectIsDirty false;
- a resolvable project root;
- no active non-root item;
- zero non-root project items;
- zero Render Queue items;
- all SDK calls succeed (fail-closed).

It is called before consuming either of the two explicit test acknowledgements and before any private native registration. This is not a guarantee of sandbox isolation or global AE process safety.

The same public-SDK guard has been compiled into CNLNativeVectorHostProbe.aex v2. The safe preflight reports disposable_project_gate_pass and reason, item/queue counts and dirty state in TSV, and displays PASS/BLOCKED in its information dialog. The user's previous v1 safe preflight succeeded in AE2026 and is recorded as EXP-SHAPE-028-LIVE-001. The NEW v2 guard is only COMPILED and has not yet been exercised in AE.

## Additional improvements to dangerous, still untested AEX

- process-ID and timestamp in proposed new MatchName reduce collisions;
- native Creator invocation count recorded via a static atomic-friendly Interlocked counter, not an unsafe stack reference captured into a callback the host may retain;
- explicit private function registration still requires matching DLL SHA256, exact symbols, opcode fingerprint, new empty project, manual menu and two acknowledgments;
- best-effort explicit UnregisterFactoryFunc after success and flushed stage-by-stage TSV persist for diagnosis.

A successful private unregister return CANNOT certify all native/canonical objects and callbacks are released. The dangerous AEX has NOT been installed, run or certified safe. A host test is not justified on an ordinary production AE session.

## Artifacts

Original C++ and Python verifier:
experiments/vector-shape/tdb-callback-abi-mock/NativeABISignatureProbe.cpp
experiments/vector-shape/tdb-callback-abi-mock/verify_symbol_abi.py
experiments/vector-shape/host_abi_shared/NativeProjectSafety.h

Safe AEX source:
experiments/vector-shape/native-vector-host-probe-lab/

Gated HIGH RISK AEX source:
experiments/vector-shape/native-tdb-registration-disposable-lab/

Receipts:
datasets/ae-tdb-exact-msvc-callback-abi-receipt-20261012.json
datasets/ae-native-vector-host-probe-v2-build-receipt-20261012.json
datasets/ae-private-tdb-disposable-v2-build-receipt-20261012.json

Associated EXP-SHAPE-031/032. E2-L/E2-B only for the new changes; no new private host registration or plugin-owned native editable AE Contents is proven.
