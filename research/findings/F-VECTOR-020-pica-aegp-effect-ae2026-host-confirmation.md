---
status: corrected-binary-confirmed-in-host
last_verified: 2026-10-12
evidence: E2-X (user AE host screenshots) + E2-T (compiled mock run) + E0-H (SDK/PiPL)
versions: installed AE2026, SDK25.6, VectorBridgeAEGP + VectorBridgeConsumer x64
---

# F-VECTOR-020 — Independent AEGP→Effect PICA Bézier handoff observed inside AE2026; Consumer metadata repaired

## Host-observed result (E2-X)

On 2026-10-11 the user installed the two separate `.aex` plug-ins and applied `Vector Bridge Consumer (Research)` to a black solid in After Effects 2026. The Effect About dialog **actually displayed**:

```text
CompNodeAE Vector Geometry Bridge
PICA suite: connected
Native Bezier segments: 4; first X: 100.00
This is NOT a host Shape Layer or native AE vector renderer.
```

This is the first user-observed AE host proof that a native AEGP can register a **public PICA procedural geometry service** and an **independently compiled ordinary Effect SDK plug-in** can acquire and consume four double-precision cubic segments inside actual After Effects, without exchanging a raster image between those two plug-ins.

**Precisely what this does NOT prove:** a native AE Shape object owned by the effect; AE Contents tree or Pen editing; BEE VectorArt output; native render-graph connection; a host-declared render dependency; an arbitrary upstream-effect parameter target; or correct MFR/project cache semantics. The Consumer's actual rendered output is still PF_World passthrough.

The user also observed three diagnostic dialogs with the original Consumer AEX:

```text
After Effects: effect 'Vector Bridge Consumer (Research)' has version mismatch.
Code version is 1.0 and PiPL version is 0.2. (80001)
After Effects: effect ... has global outflags mismatch.
Code flags are 400 and PiPL flags are 0.
This effect may slow down Preview and Export as it is not optimized for Multi-Frame Rendering.
```

The first two reflect an initial lab authoring mismatch rather than a failure of the **connected** geometry service. The final is a performance capability notice, not a runtime vector-geometry failure.

## Root causes and corrected consumer (not yet reloaded in AE)

Code defined `PF_VERSION(1,0,0,PF_Stage_DEVELOP,1)`, whose SDK25.6 packed integer is `524289` (`0x80001`), whereas initial PiPL declared `AE_Effect_Version {65536}` (`0x10000`, displaying as 0.2). New PiPL directly declares **524289**.

The original consumer marked its pixel passthrough `PF_OutFlag_PIX_INDEPENDENT` (`0x400`) although output is copied from the original input pixels; this flag was semantically wrong. Both source and new PiPL now declare **PF_OutFlag_NONE = 0**.

The Consumer implementation uses no sequence data or per-frame mutable global state and copies caller-local numeric geometry while acquiring/releasing the public PICA suite. As a preliminary MFR capability claim, `PF_OutFlag2_SUPPORTS_THREADED_RENDERING` is now declared in C++ and PiPL (both **0x08000000**). Adobe's SDK Checkout effect uses the same out_flags2 bit while acquiring custom PICA suites. **This is not equivalent to an actual MFR stress test** of the revised binary.

Recompiled `D:/Developer/ShapeLayerAE/build/vector_bridge/Release/VectorBridgeConsumer.aex`; x64 PiPL PE resource at ID 16000 was inspected directly (not merely the .r source). Properties:

| Binary PiPL property | Hex/type | Effective integer |
| --- | --- | ---: |
| `REVe` Effect Version | 4-byte | **524289** |
| `OLGe` Global OutFlags | 4-byte | **0** |
| `2LGe` Global OutFlags2 | 4-byte | **134217728** |

New Consumer SHA256: `4271c8b7b1c710df12681c57cfda6eb9e148eff59114ffdd1477e31e5d4d411f`. Unmodified Provider SHA256: `85f189f8e3bfa22ba9858ee1b5b95ae21b5462cf271f9f23f889708d306e5802`.

## Independent real DLL test (E2-T, not After Effects)

Both real built AEX modules were loaded from an isolated **mock host process** `VectorBridgeHostMock.exe`; the mock's PF_InData callback table included its missing `PF_UtilCallbacks::ansi.sprintf` stub, matching the SDK macro used by Consumer About. The first mock iteration crashed due to an *incomplete mock callback table*; fixing the mock—not the AEX—resolved it.

The final standalone test returned PASS with:

```text
suite_registered=1
native_cubics=4
time0_radius=100.000
time05_radius=115.130
consumer_suite_acquires=1
consumer_about= ... PICA suite: connected ...
```

This proves the modified AEX pair can perform a standalone service handshake and time-varying geometry computation. It is **not a new AE host retest** of MFR/version dialogs. The next user test must close AE, replace **Consumer** with the corrected staged AEX, restart AE, and verify warnings disappear while the Suite remains connected.

## Product capability unlocked

An After Effects plug-in can expose a **non-raster geometry data service to other cooperating plug-ins in the same AE process**, using the Adobe-supported PICA extension mechanism. This can underpin cross-plug-in Bezier path pipelines (source→deformer→stroke, vector instancer, signed geometry, procedural outline) without automatic pixelization between those cooperating plug-ins.

This is a distinct, shippable-architecture research route from the private `BEE_VectorStream::Operator` and `TDB_StreamFactory` registries. The eventual user goal—an ordinary effect which **itself** owns fully native editable AE Contents and uses the production vector renderer—remains **unachieved**.

## Artifacts

- `experiments/vector-shape/vector-bridge-lab/VectorBridgeConsumer.cpp` and `VectorBridgeConsumer_PiPL.r` patched, source-only
- `experiments/vector-shape/vector-bridge-lab/verify_pipl_metadata.py` PE resource verifier
- `experiments/vector-shape/vector-bridge-lab/VectorBridgeHostMock.cpp` corrected mock callback table
- `datasets/ae-pica-vector-bridge-20261011-host-and-fix.json` machine-readable state
- `D:/Developer/ShapeLayerAE/results/vector_bridge_final_mock.log` test output on the user's authorized computer
- Adobe SDK 25.6: `AE_Effect.h` `PF_VERSION`, `PF_OutFlag*`, `AE_EffectCB.h` `PF_SPRINTF`, and samples `Sweetie` / `Checkout`

Original screenshots were user-supplied in the conversation and their text was transcribed above; screenshot binary assets are **not** copied into the repository. No private registry operations were attempted.

## Installation status after corrected build

The installed original `C:/Program Files/Adobe/Common/Plug-ins/7.0/MediaCore/VectorBridgeConsumer.aex` has SHA256 `11363e5637f748b2390c8ee084a0590ee676f8978e9d11a732a4c60984ec0793`. Its byte-identical backup was made at `D:/Developer/ShapeLayerAE/backups/VectorBridgeConsumer_pre_PiPL_fix_20261011.aex`. An automated overwrite attempt was **denied by Windows UnauthorizedAccessException** in the protected Program Files directory; the original installed hash remained unchanged. The fixed binary SHA256 `4271c8b7b1c710df12681c57cfda6eb9e148eff59114ffdd1477e31e5d4d411f` remains staged at `D:/Developer/ShapeLayerAE/build/vector_bridge/Release/VectorBridgeConsumer.aex` and **must be copied by an administrator** after closing AE. No new AE2026 host success is asserted for the patched Consumer yet.


## 2026-10-12 actual corrected AEX host confirmation

The user submitted an additional After Effects 2026 screenshot showing the applied effect and its About dialog:

  CompNodeAE Vector Geometry Bridge
  PICA suite: connected
  Native Bezier segments: 4; first X: 100.00
  This is NOT a host Shape Layer or native AE vector renderer.

A separate authorized local hash check read both the installed Consumer AEX and the staged corrected Release Consumer binary and returned the EXACT SAME SHA256 for each: 4271C8B7B1C710DF12681C57CFDA6EB9E148EFF59114FFDD1477E31E5D4D411F. Therefore the **corrected Consumer AEX was indeed installed and running successfully inside AE2026**; the earlier "not yet reloaded" installation paragraph above is HISTORICAL and superseded by this later observation.

The user screenshot shows no active yellow warning icon next to the effect and no error popup; the user did not report the previous PiPL mismatch dialogs in this retest. This supports the metadata fix, but absence of warning on one screenshot does not test all project/startup conditions or concurrent MFR rendering. The exact original provider-to-consumer PICA native cubic handoff remains correct after rebuild.

Product boundary is unchanged: numeric cross-plugin geometry service is host-confirmed; native BEE_VectorArt output, editable native Contents owned by an Effect SDK effect, and host renderer integration remain unproven.
