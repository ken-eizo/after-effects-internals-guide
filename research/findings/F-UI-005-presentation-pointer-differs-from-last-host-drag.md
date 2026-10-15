---
status: observed-scoped
evidence_grade: E2-L and E2-X
last_verified: 2026-10-12
versions: actual user's AE build not captured
confidence: High for sampler output; coordinate mapping not independently verified
---
# F-UI-005 - Late OS pointer samples can differ from the last host DRAG position

## Statement

During a user AE Effect Custom UI session, DRAW callbacks sometimes
observed a newer physical cursor position than the most recent
PF_Event_DRAG coordinate stored by the plugin. The experimental
presentation-only model was updated from the OS pointer sample.

The observation is scoped to an assumed 1:1 mapping of OS mouse
pixel displacement to host viewer-local pixel displacement.
It is not proof of improved end-to-end input-to-photon latency.

## Evidence

Immutable trace: experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v5-all-modes.csv
SHA256: a2ffd279df34c57508da2bc8b9e89388c87fec39b745daf23221a36468b931e1

Among 17,275 recorded AE callbacks, 2,135 DRAW callbacks
set late_display_used=1. The reported OS estimated displacement
ahead of the stored AE DRAG point had median 12.530px and
p95 44.820px within these calls. Selection changes,
mouse velocity and monitor scaling were not controlled.

The host-independent implementation is
D:/Developer/GizmoSearchAE/ae_plugin/GizmoLateLatch.hpp.
The late-preview Model is a scratch copy; official DRAG
coordinates and effect stream values were not overwritten
during passive DRAW.

## Interpretation / limits

This shows that obtaining a fresh OS pointer sample in a
host-delivered DRAW can make the INPUT to a custom manipulator
differ from the older AE capture event. This does not create
additional DRAW callbacks and does not show that each submitted
drawing was physically presented. The cost and improvement
under an identical gesture with LATEST OFF/ON remains to be
verified in a controlled side-by-side experiment.

DPI, multi-monitor, window movement and AE viewer zoom
can invalidate a simplistic 1:1 physical-pixel-to-view mapping.

## Generalizable system contracts

docs/ui-system/effect-custom-ui-input-routing.md
docs/ui-system/interactive-ui-latency.md
