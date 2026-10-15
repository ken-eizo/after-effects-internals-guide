---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L / E2-X / E0-H
scope: GizmoSearchAE Effect Custom UI native host, v9 capture, SDK 25.6
confidence: high for callback QPC samples; causal UI smoothness unknown
---
# F-UI-012 - Low Drawbot CPU does not eliminate native drag-to-DRAW latency

## Preserved evidence

- `experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v9-initial-mode8-comparison-91c9cbb1.csv`
  SHA256 `91c9cbb1c178e0ebe0281e71fcb5209bedc932ba6d9f31e8f4e93ef258c8922b`.
- `experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v9-drawbot-profile-d810907a.csv`
  SHA256 `d810907ad29a7982382a7ad38b5ea92570cd575c36143ad96fa801df12f02970`.
- Host event log: 14,941 callbacks, QPC Hz 10,000,000.
- Drawbot sampled sidecar: 408 samples, approximately every sixteenth DRAW.

The user reported REDRAW 8 to be the smoothest and most stable of
the available 0-8 experiment modes, while perceivable delay still remains.
This is subjective observation, not a comparative input-to-photon measurement.

## Scoped measurements

In mode 8 / HUD enabled / LATEST enabled / active drag,
there were 2,581 DRAW callbacks in the budget-gate selection:
- Drawbot acquire p50 7.2us, p99 27.5us.
- OS pointer latest-stage p50 3.4us, p99 97.96us.
- Scene command stage p50 67.4us, p99 272.78us.
- Drawbot release p50 7.2us, p99 27.24us.
- Complete callback p50 82.7us, p99 309.06us.

The same recording's mode 8 / HUD-enabled / all-LATEST drag subset:
976 DRAG and 2,922 DRAW callbacks; DRAG-to-next-DRAW p50 2.578ms,
p99 8.664ms under the script's matching logic. The original
coalescer analyzer reported only 1 coalesced invalidation out of
987 mode-8 click/drag entries: request coalescing was rare in this trace.

Within 163 sampled mode 8/HUD-on/drag-on/LATEST-on DRAWs, the
total Drawbot path stage p50 was 62.50us, p99 162.23us.
The nested path-geometry p50 was 11.80us and
the path-stroke/fill p50 was 43.00us. Path-stage fields overlap,
so do not sum them as independent elapsed times.

The public SDK distinguishes PF_InvalidateRect lazy update from
PF_EO_UPDATE_NOW's immediate post-event draw request. A new
**opt-in mode 9** is an A/B comparator equal to mode 8 in its
coalescing, full-pane redraw, late-sampling and drag HUD suppression,
but turns on PF_EO_UPDATE_NOW. Mode 8 remains intact. Mode 9
is compiled/model-tested but NOT validated as faster or smoother in AE.

## Conclusions with limits

- Fast manipulator model CPU does not guarantee display latency:
  DRAG-to-DRAW alone is millisecond-scale in this host recording.
- 10us p99 for all DRAW phases was NOT achieved. Some phases include
  Adobe Drawbot suite calls and host-controlled waits.
- An "all paths always under 10us" contract cannot be inferred from
  these results, and is not guaranteed by Adobe's public UI API.
- Coalescing is not a demonstrated cause of the user's preference
  for mode 8 given only 1 coalesced update recorded in that subset.
- Compare mode 8 versus 9 in the same AE configuration with
  interval/HUD/geometry settings held constant; use
  `tests/analyze_native_smoothness.py` and
  `tests/analyze_drawbot_profile.py`.
- Neither trace contains hardware pointer-event timestamps, GPU
  physical Present, or input-to-photon measurements.

References:
https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/
https://ae-plugins.docsforadobe.dev/effect-ui-events/PF_EventExtra/

Related: F-UI-006, F-UI-009, F-UI-011.
