---
status: pass-built-not-host-tested
last_verified: 2026-10-12
evidence: E2-B; E2-X pending
versions: MSVC VS2022 x64, AE SDK25.6
---

# EXP-SHAPE-028 — Actual CNL procedural cubic core compiled inside a new AEGP

## Output

Native CNLNativeVectorHostProbe.aex was built from original sources in native-vector-host-probe-lab. The AEGP includes real CNL NativeVectorCore document code and produces code-based cubic geometry in its user-invoked handler. It does NOT create or depend on native Shape or Mask, does not rasterize PF_World and does not mutate native registries.

Build local: D:/Developer/ShapeLayerAE/build/native_vector_host_probe/Release/CNLNativeVectorHostProbe.aex

Menu: Animation > CNL Native Vector: Host Preflight (Read Only).

Logs: %TEMP%/CNL_NativeVector_HostPreflight.tsv. Exact TDB.dll SHA256 fingerprint and native export readiness plus native CNL cubic geometry. The private getter is only invoked on an exact known binary hash and opcode; no private registration, creation or UI edit call occurs.

## Verified

- Windows x64 Release build and PiPL resource generated from official installed AE25.6 SDK.
- PE export EntryPointFunc and embedded CNL vector C API symbols verified.
- The AEX contains menu/report text and no Adobe TDB/BEE/AGM hard imports.
- Native standalone CNL Core CTest and external ctypes test previously passed.

Build receipt datasets/ae-native-vector-host-probe-build-receipt-20261012.json.
Static artifact verifier native-vector-host-probe-lab/verify_pe.py PASS.

## Still NOT verified

No user installed or ran it in AE. This is NOT evidence that AE adopts the path as native editable Contents. The host output contract, editor and renderer remain unproven. User owns installation and AE GUI test.
