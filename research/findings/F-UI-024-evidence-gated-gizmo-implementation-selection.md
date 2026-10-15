---
status: locally-validated-policy; host-performance-unverified
last_verified: 2026-10-14
scope: AE 26.3 Effect Custom UI and SDK 25.6 reference; host-independent policy test
evidence_grade: E0-G + E0-H for contracts; E2-X for local tests; H for untested runtime candidate ranking
confidence: high on published event/flag contracts and pure branch parity; unknown on AE host gain
---

# F-UI-024 — Evidence-gated native gizmo execution selection

## Statement

The appropriate implementation for a native After Effects Gizmo must
be chosen per operation/ownership boundary: host-input mutation,
native Drawbot UI painting, effect frame rendering, host-managed GPU
compute, optional MFR and OS display composition. A single generic
"fastest API" is not a valid selection criterion across these layers.

An effective selector must **fail closed** on untested host versions,
device/driver combinations and correctness conditions, choosing a
conservative contract-compatible fallback rather than automatically
enabling a GPU/MFR/region-preview path.

## Evidence and scope

- Adobe Custom UI & Drawbot: PF_Event_DRAW is the draw boundary;
  PF_InvalidateRect + PF_EO_UPDATE_NOW are requests to the host.
  https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/
- Adobe MFR and OutFlags: GPU render, pixel independence and
  thread-safe multi-frame rendering are different promises;
  they must be implemented and validated independently.
  https://ae-plugins.docsforadobe.dev/effect-details/multi-frame-rendering-in-ae/
  https://ae-plugins.docsforadobe.dev/effect-basics/PF_OutData/
- Windows scheduler Ready and Running states differ from waits.
  https://learn.microsoft.com/en-us/windows/win32/procthread/context-switches
- E2-L prior WPR:
  GizmoSearchAE's actual operation recorded a heavy AE UI thread
  but included window movement, so ordinary-DRAG p99 cannot be
  deduced unambiguously from its worst pauses. See F-UI-021.
- E2-X GizmoSearchAE pure selector:
  ae_plugin/GizmoImplementationSelection.hpp
  ae_plugin/GizmoImplementationSelectionTests.cpp
  Windows Release CTest name GizmoImplementationSelection.
  The compiled selector is connected to existing production
  POINTS/mode-9 fast scene selection. For all 12 redraw modes ×
  16 input-flag combinations it returns exactly the old path.
- Unmeasured GPU/MFR/cache candidates default to disabled and
  require explicit VerifiedInHost evidence for recommendation.
  These recommendations are not host-auto-switch implementations.

## Reproduction

1. On Windows with AE SDK 25.6, run:
   `python D:\Developer\GizmoSearchAE\tests\validate.py`
2. Verify CTest GizmoImplementationSelection, 5/5 tests total,
   ABI/PiPL consumer tests and Release AEX build.
3. Read the AEIG guide pages for candidate status, fallback and
   host-specific acceptance rules.
4. The host trial of new backend choices (GPU/MFR/LeanPix) is
   **not part of this local test**; no AE application was modified.
5. To promote an unverified candidate, compare A/B/A with exact
   image equivalence, context lifetime, p99 and resource metrics,
   same AE build, GPU driver, monitor and workload.

## Contradictions / Unknowns / Falsification

- A CPU SIMD or GPU path may outperform a batched Drawbot/Gizmo
  implementation on a particular task; current evidence does not
  prove any global ranking. The policy remains workload-specific.
- The public AE SDK does not promise per-refresh 240Hz Custom UI DRAW.
  A counterexample would require an explicit compatible host
  guarantee, not a standalone 240fps Drawbot benchmark.
- Local test success proves the selector truth table, **not**
  a reduction in physical input-to-photon time.
- The long-tail bottleneck in AE's UI thread still requires
  controlled no-window-movement tracing with callback-to-present
  correlation. It cannot be fixed simply by selecting a GPU API.

## Documentation links

- docs/ui-system/gizmo-adaptive-implementation-architecture.md
- docs/ui-system/gizmo-execution-memory-policy.md
- docs/ui-system/gizmo-measurement-acceptance.md
