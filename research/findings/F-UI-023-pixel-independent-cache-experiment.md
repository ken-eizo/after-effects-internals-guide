---
status: implementation-validated-not-host-tested
last_verified: 2026-10-13
evidence_grade: E1-L compiled-resource-and-ABI; E0-H real host performance
scope: GizmoSearchAE pure-image-identity Effect Custom UI, AE 26.x
---
# F-UI-023 — Pixel-independent identity effect: cache optimization A/B experiment

## Premise
Adobe Effect SDK defines PF_OutFlag_PIX_INDEPENDENT when a pixel's
output depends only on the corresponding input pixel. This native
Gizmo's PF_Cmd_RENDER is an identity/passthrough copy; the changing
Gizmo visuals are drawn in PF_Event_DRAW, not in the rendered image.
The pixel-independent flag may allow better AE frame caching
or renderer pruning. No such improvement is established in the host.

Official spec:
https://ae-plugins.docsforadobe.dev/effect-basics/PF_OutData/
https://ae-plugins.docsforadobe.dev/effect-basics/PF_InData/

## Controlled variants
- GizmoInputProbeLean.aex: PiPL OutFlags 0x02008000, no pixel-independent bit.
- GizmoInputProbeLeanPix.aex: PiPL OutFlags 0x02008400,
  also set in EffectMain(PF_Cmd_GLOBAL_SETUP).
- Both are compiled from the same source and use the same
  REDRAW 9/Drawbot/Gizmo geometry and event policy.
- Same Adobe Match Name; only ONE can be installed.
- No AE in-use plug-in was replaced.

A compiled Win32 PiPL resource check and a DLL EffectMain
GLOBAL_SETUP invocation proved that the two flags agree for
the control and experiment. Host effect registration, rendering
behavior, colored 8/16bpc frames and mask/extent correctness
are NOT yet verified. These need a real AE A/B/A test.

The Lean Drawbot Surface now uses cache arrays of 16 brushes/pens
instead of 48 (with existing temporary-resource overflow fallback),
plus compile-time sizeof(view::Surface)<2048 and
Context size under 16384. This reduces stack/memory footprint,
not proven host milliseconds or GPU use.

The Lean HUD-free late-latch threshold uses squared distance >0.25
instead of computing sqrt just to test a 0.5px movement threshold.

## Related pixel-transfer regression
The passthrough implementation was found to overwrite unread data
for in-place copy when destination rowbytes > source rowbytes.
A newly introduced regression failed on the unmodified code.
Reverse-order row traversal for this unusual in-place expansion
now passes, and deterministic separate/in-place tests across
9x9x7 stride/height combinations pass.
The usual equal-pitch contiguous memmove remains untouched.

## Host-independent CPU copy benchmark
UHD 3840x2160 RGBA8: median 2.83ms, p99 3.98ms for a memcpy
in a standalone test, NOT AE and NOT frame presentation.
More CPU arithmetic micro-optimization cannot guarantee
10us input-to-photon at 240Hz (period ~4.167ms).

## Reproduction
- tests/validate.py (Release, CTest, compiled PiPL, GLOBAL_SETUP smoke)
- tests/test_compiled_pipl_flags.py
- ae_plugin/GizmoEffectFlagsSmoke.cpp
- ae_plugin/GizmoPixelTransferTests.cpp
- Scratch logs:
  GizmoSearchAE/scratch/cache-hypothesis-20261013

Full Japanese report:
GizmoSearchAE/CACHE_RENDER_OPTIMIZATION_20261013_JA.md
