---
status: host-confirmed-original; corrected-build-pending-host-retest
last_verified: 2026-10-11
evidence: E2-X + compiled-PE + isolated-mock-pass
versions: AE2026, AE SDK25.6, x64
---

# EXP-SHAPE-019 — AEGP PICA geometry producer to ordinary Effect SDK consumer, actual AE host success and PiPL repair

## Question

Can a separately compiled AEGP provide four independent cubic Bezier segments to a normally installed AE effect via a public PICA suite without rasterizing the geometry? If so, what parts of the implementation remain host metadata/MFR concerns?

## Observed in AE2026

The user installed `VectorBridgeAEGP.aex` and `VectorBridgeConsumer.aex` and applied `Vector Bridge Consumer (Research)` to a black solid. Four screenshot dialogs were provided in the conversation. The Effect About dialog reported:

```text
CompNodeAE Vector Geometry Bridge
PICA suite: connected
Native Bezier segments: 4; first X: 100.00
This is NOT a host Shape Layer or native AE vector renderer.
```

Thus the public PICA interface exchanged numeric 4-cubic geometry across plugin DLLs **in the real host** (E2-X). It did not produce native host VectorArt/Shape Contents. Initial AEX loaded with these *separate* diagnostics:

- Code version 1.0 vs PiPL version 0.2; code packed hex 0x80001; PiPL had 65536
- Code out_flags hex 0x400 vs PiPL 0x0 (consumer had incorrectly claimed PIX_INDEPENDENT on a pixel passthrough)
- MFR performance notice (not a hard error)

## Repair and actual build receipt

Source `labs/vector_bridge/VectorBridgeConsumer.cpp`: remains `PF_VERSION(1,0,0,PF_Stage_DEVELOP,1)`; changed `out_flags` to `PF_OutFlag_NONE`; sets `out_flags2` to `PF_OutFlag2_SUPPORTS_THREADED_RENDERING` because render code has no shared mutable state and uses caller-local snapshots.

Source `VectorBridgeConsumer_PiPL.r`: changed `AE_Effect_Version` to 524289, `AE_Effect_Global_OutFlags` to 0 and `AE_Effect_Global_OutFlags_2` to 0x08000000.

SDK `PF_VERSION` bit shifts were verified (major 1<<19 + build1). The **compiled Consumer AEX** PiPL resource, not only the source file, was decoded with pefile:

| Serialized PiPL key | Parsed integer |
| --- | ---: |
| `REVe` | 524289 |
| `OLGe` | 0 |
| `2LGe` | 134217728 |

`verify_pipl_metadata.py` asserts these properties and checks that C++ flags match.

New Consumer SHA256 `4271c8b7b1c710df12681c57cfda6eb9e148eff59114ffdd1477e31e5d4d411f`; unchanged Provider SHA256 `85f189f8e3bfa22ba9858ee1b5b95ae21b5462cf271f9f23f889708d306e5802`.

## Separate executable cross-DLL mock test

Built `VectorBridgeHostMock.exe` loads both actual compiled AEXs. The initial mock process crashed on `PF_Cmd_ABOUT` because the **mock** supplied a `PF_InData` structure with `utils == nullptr`; SDK macro `PF_SPRINTF` dereferences `in_data->utils->ansi.sprintf`. The real AE host supplies this callback; the screenshot already demonstrated that. Adding a mock sprintf callback corrected the test harness.

Final test **PASS**:

```text
suite_registered=1 native_cubics=4
time0_radius=100.000 time05_radius=115.130
consumer_suite_acquires=1
consumer_about= ... PICA suite: connected ...
```

This is useful ABI regression testing but is **not an AE host test**.

## State of proof

- Original AEX pair succeeded inside real AE2026 (E2-X).
- Corrected Consumer binary is built and PiPL-validated; standalone runtime mock test passed.
- **The corrected Consumer has not yet been reloaded and observed inside AE**. Expected warnings to disappear, not claimed until the user retests.
- MFR flag declaration is a preliminary stateless-render claim, not proof of concurrent stress safety, render dependencies or sequence lifetime.
- The normal effect still outputs a PF_World passthrough; no native AE vector renderer, Timeline Contents, or Pen tool use has been achieved.

## Immediate next host experiment

With AE fully closed, replace the **Consumer** AEX with the new Release binary. Start a disposable project and apply the effect. Success requires the version and flags mismatch dialogs absent and the Effect About still reporting `PICA suite: connected`, four segments. MFR warning should no longer appear if registration/flags match; subsequent multi-frame/time-scrub/close-reload are separate tests.

## Raw evidence

`datasets/ae-pica-vector-bridge-20261011-host-and-fix.json` (machine-readable)
`research/findings/F-VECTOR-020-pica-aegp-effect-ae2026-host-confirmation.md`
`experiments/vector-shape/vector-bridge-lab/` (source-only, no Adobe proprietary binaries)

## Installation status after corrected build

The installed original `C:/Program Files/Adobe/Common/Plug-ins/7.0/MediaCore/VectorBridgeConsumer.aex` has SHA256 `11363e5637f748b2390c8ee084a0590ee676f8978e9d11a732a4c60984ec0793`. Its byte-identical backup was made at `D:/Developer/ShapeLayerAE/backups/VectorBridgeConsumer_pre_PiPL_fix_20261011.aex`. An automated overwrite attempt was **denied by Windows UnauthorizedAccessException** in the protected Program Files directory; the original installed hash remained unchanged. The fixed binary SHA256 `4271c8b7b1c710df12681c57cfda6eb9e148eff59114ffdd1477e31e5d4d411f` remains staged at `D:/Developer/ShapeLayerAE/build/vector_bridge/Release/VectorBridgeConsumer.aex` and **must be copied by an administrator** after closing AE. No new AE2026 host success is asserted for the patched Consumer yet.
