---
status: observed-scoped
evidence_grade: E2-L + E2-X
last_verified: 2026-10-12
versions: user's AE build not captured
confidence: high for QPC callback durations; no matched-movement trial
---
# F-UI-007 — Static diagnostic UI can dominate Custom UI drawing cost

## Statement

In one actual user Effect Custom UI session, the Drawbot
callback was substantially faster when the experimental
diagnostic toolbar and text were hidden, even though the
same native Composition UI/Drawbot system still drew and
allowed manipulation of the geometry.

The observation suggests that the manipulator geometry
itself does not explain most of the plugin-side DRAW CPU
time in this sample. It does not establish general
performance bounds for all custom UIs or physical
input-to-photon latency.

## Primary trace

Unmodified:
experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v6-hud-comparison.csv

SHA256:
14c9971ed841a5d4ed1e9806e1a47cc5de784b1f32ce5d3099585db7105c18ee

18,229 recorded UI callbacks, including 8,634 DRAW.
The most relevant subsets keep REDRAW=0 and LATEST=ON
but differ in HUD state during dragging:

| plugin CPU cost | HUD visible (3488 DRAWs) | HUD hidden (262 DRAWs) |
| --- | ---: | ---: |
| DRAW median | 1.712 ms | 0.134 ms |
| DRAW p95 | 5.058 ms | 0.281 ms |
| DRAW p99 | 7.416 ms | 0.408 ms |
| Drawbot scene median | 1.667 ms | 0.102 ms |
| Text commands per DRAW (median) | 18 | 0 |
| Drawbot acquire median | 0.009 ms | 0.011 ms |

These samples were *not* collected from a matched
randomized controlled experiment, and the user may
have interacted differently. HUD ON also draws
rectangles/text and recomputes readout strings, so
this is not an isolated measurement of font setup
or DrawString alone. The magnitude indicates why
the static diagnostic UI deserves separate treatment
from moving geometry.

## Interpretation

The Drawbot suite acquisition cost was about a
hundredth of a millisecond and did not dominate
these recorded draws. The large decrease was in
scene construction/commands. A reusable design can
keep fixed diagnostic UI out of repeated geometry
updates when the host supports region-limited
redrawing, while allowing the host's actual
update_rect to control what must be repainted.

Even with HUD hidden, DRAW callback p99 inter-arrival
gaps can exceed many display periods. The trace
therefore does not prove a complete solution to
smooth mouse tracking or physically presented FPS.

## Reproduction

D:/Developer/GizmoSearchAE/tests/analyze_v6_phases.py

The new REDRAW 5 experimental option tests:
- The same lazy mode-0 update policy.
- Invalidating a conservative region around old/new geometry.
- Skipping unchanged diagnostic chrome when the host
  actually requests a rectangle that excludes it.
- Rejecting late-sampled presentation estimates that
  would extend outside the real update rect.

This new path is compiled and model-tested. Its impact
within the real AE host still needs a matched comparison
against mode 0. Do not report the above HUD hide speedup
as a measured improvement for REDRAW 5 itself.

## Cross references

docs/ui-system/drawbot-ui-drawing.md
docs/ui-system/effect-custom-ui-invalidation.md
docs/ui-system/interactive-ui-latency.md
docs/research-notes/gizmo-input-probe-2026-10-12.md

## Clarification following v7 callback audit (2026-10-12)

It is incorrect to infer from zero text commands in a HIDE UI capture
that the REDRAW 5 partial-damage optimization has successfully
retained and skipped static HUD while the HUD was actually visible.

In a separate archived v7 user session, 1,963 REDRAW-5 DRAW
callbacks with HUD visible and LATEST ON had a median of 18 text
commands per DRAW (none had zero). By contrast, 1,793 DRAW calls
recorded with HUD hidden had zero text commands by design.
The then-current host-supplied update_rect was not a valid positive
rectangle, so the source's condition for retaining visible HUD
was not met. Earlier prose that mode 5 had already demonstrated
HUD-skip success in AE is therefore NOT supported by this trace.

The generalizable verified result remains only the actual
difference between user-disabled HUD and enabled HUD execution.
Skipping visible static diagnostics without manually hiding the
HUD is an independent rendering strategy requiring its own
installed-host validation. One separate experimental approach
is to deliberately omit diagnostic HUD drawing during active
capture while drawing the manipulator normally, restoring chrome
after capture ends. That changes the interaction display and
must be checked for correct repaint and no ghosting; it is NOT
the same as caching HUD pixels across partial host redraws.

Independent v7 inspection:
D:/Developer/GizmoSearchAE/tests/analyze_native_smoothness.py
