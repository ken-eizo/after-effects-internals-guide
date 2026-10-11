---
status: compiled-not-yet-user-host-tested
last_verified: 2026-10-12
evidence: E2-B + E2-L
versions: MSVC VS2022 x64, AE25.6 SDK; AE host behavior untested
---

# F-VECTOR-032 — New independent native-vector AEGP compiles and performs gated host preflight

## Goal and precise outcome

Connect the genuinely plugin-owned CNLNativeVectorCore document/path model to a **real AEGP module**, without using native Mask, native Shape Layer, a PF_World rasterizer or any project mutations. The resulting built AEX demonstrates a code-generated double-precision cubic vector **inside a legitimate AE plugin binary** and prepares read-only host-native TDB ABI fingerprints.

Output built:
D:/Developer/ShapeLayerAE/build/native_vector_host_probe/Release/CNLNativeVectorHostProbe.aex

The AEX has not been installed or executed in AE. It is a **host-preflight probe**, not an independently editable native vector type and not the final plugin.

## Compiled code and menu

Source:
experiments/vector-shape/native-vector-host-probe-lab/CNLVectorHostBridge.cpp

PiPL:
experiments/vector-shape/native-vector-host-probe-lab/CNLVectorHostBridge_PiPL.r

Menu registered by AEGP EntryPointFunc:
Animation > CNL Native Vector: Host Preflight (Read Only).

Only when the user invokes that menu does it:
- Generate a CNL document with own Contents tree, procedural native ellipse, four double-precision Bezier cubics and handles. All geometry is in the AEX memory; no Mask/Shape/PF_World or comp modification.
- Compute SHA256 of actually loaded TDB.dll and compare against two pinned AE2025/AE2026 hashes.
- Use GetProcAddress to query private TDB factory getter, known complete ParamPathStream::Create, RegisterFactoryFunc, UnregisterFactoryFunc and GetCanonicalInstance exports, **without invoking the mutating functions**.
- On a pinned hash and known tiny machine-code fingerprint only, invoke the previously host-verified *no-argument read-only* TDB factory Getter. Pointer is checked only for nullptr and immediately discarded without dereference or retention.
- Write diagnostic data to %TEMP%/CNL_NativeVector_HostPreflight.tsv, including explicit native-registration=0, editor=0, renderer=0 indicators.
- Display a short info message via public AEGP UtilitySuite.

## Actual build verification

- Visual Studio 2022 Windows x64 Release AEX compiled successfully with Adobe SDK25.6 PiPLTool resources and CNLNativeVectorCore.cpp embedded.
- PE check confirms EntryPointFunc and native CNL function exports, x64 machine, PiPL resource, expected menu/report strings.
- BEE.dll, TDB.dll and AGM.dll are **not hard imports**. Private symbols are observed dynamically only.
- No new native stream type is registered or method attempted. No AE user project/GUI was operated by the researcher.
- Receipt: datasets/ae-native-vector-host-probe-build-receipt-20261012.json; local SHA256 in the receipt.
- This is E2-B compiled binary verification, **NOT E2-X host result**. No "AE successfully uses CNL vectors natively" claim can follow.

## User test and significance

Safe user test in an ordinary disposable project: install just the safe CNLNativeVectorHostProbe.aex, restart AE, select its Animation menu command, inspect %TEMP%/CNL_NativeVector_HostPreflight.tsv. This will confirm loaded native library fingerprints in a real AE process and CNL geometry inside AEGP, not native host editable Contents.

The next risky experimental AEX is **separate** and has not been installed. Never confuse these AEX files.

## Larger future vision

The durable CNL path-value core is now inside an actual AEGP, making an independent vector-source implementation available for later exact-ABI native adapter experiments. To become a real new native AE vector plugin, the host must still accept a new TDB type, legitimate Timeline owner, Pen editing, BEE operator and VectorArt render graph. This compiled AEX solves none of those host contracts by itself.
