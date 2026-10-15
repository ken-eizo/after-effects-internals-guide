---
status: observed-scoped
evidence_grade: E2-L, E2-X, E0-H
last_verified: 2026-10-12
versions: user AE build not captured in log
confidence: high for logged callback values and plugin source; physical clipping not measured
---
# F-UI-008 — Empty host draw update rectangles suppressed late input previews

## Independent observed claim

In a recorded Composition Effect Custom UI session, PF_Event_DRAW
callbacks carried PF_DrawEventInfo.update_rect values which, as read
by the effect, did not represent positive-area rectangles.

The experimental GizmoSearchAE plug-in previously treated this
host-reported rectangle as a mandatory containment check for newer
Windows pointer positions. As a result, REDRAW 5 discarded every
LATEST correction in the recorded capture even though LATEST was ON.

This is an observed plugin-side logic error triggered by an unexpected
callback value. It is NOT proof of incorrect AE GPU clipping or
rendering. The trace cannot distinguish intentionally empty/sentinel
rectangles, host-version behavior, or an unrecognized callback ABI
expectation.

## Primary evidence

Original CSV:
experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v6-host-clip-sentinels.csv

SHA256:
50d0001c21e500254b0a0fedb74e2cfeba1fa5a0bcb73ca655482f7b165af43a

- Total: 31,015 callbacks, including 13,993 DRAW.
- No DRAW had update_right > update_left AND
  update_bottom > update_top, according to the plugin log.
- Most common reported rectangle: (-1, -5, -1, -15),
  seen 10,190 times.
- REDRAW 5 dragging: 4,438 DRAWs; latest_enabled=1 in all,
  late_display_used=1 in ZERO.
- REDRAW 0 dragging: 3,968 DRAWs; latest preview used in 3,419.

Previous source in GizmoInputProbe.cpp reset every visual snapshot
when the candidate was not contained in the host update rectangle.
Given nonpositive host rectangles, mode 5 could never use a
speculative pointer update during DRAW.

Reproduce using:
D:/Developer/GizmoSearchAE/tests/audit_host_clipping_v6.py
Archived with:
D:/Developer/GizmoSearchAE/tests/archive_host_clip_evidence.py

## General interpretation

A PF_InvalidateRect region submitted by an effect and a subsequent
host-reported DRAW update_rect are distinct. Host scheduling and
coalescing may modify actual draw areas, and the public SDK alone
does not guarantee that a requested rect equals the effective clip.

A fallback containment check using the last plugin-requested region
when the host value is invalid is an *experiment*, not a proof of
effective clipping. Host repaint/resizing/zoom and fast motion
must be tested for retained overlays, missing paint or clipping.

## Corrective experiment

The latest v8 research AEX retains host-owned Drawbot rendering.

1. Record the requested finite invalidation region before the
   PF_InvalidateRect call.
2. On a DRAG event, take an OS cursor sample as a presentation-only
   estimate and expand the dirty region around that projected pose
   (48px safety fringe).
3. Inside DRAW, do not treat an invalid host update_rect as an
   automatic permanent veto of all OS pointer previews.
4. Accept a transient model only if its geometry fits the plugin's
   own requested region; additionally respect a valid host rectangle.
5. Never modify committed AE/project/model state in DRAW.
6. Instrument preview candidate, region rejection, requested/host
   validity and requested bounds in v8 CSV.

Build and pure-model tests pass against SDK 25.6. Post-fix in-host
results are pending; no claim of zero end-to-end latency.

## Related separate timing observation

In 22 captured REDRAW-5 gesture segments, there were no
PF_Event_IDLE callbacks between first and last DRAG despite
multiple DRAW callbacks (usually around 3 DRAW per DRAG).
This finite recording does not support relying on IDLE as a
faster input-refresh stream during captured dragging.
Multiple DRAW callbacks do not prove physical presentation.

## See also

docs/ui-system/effect-custom-ui-invalidation.md
docs/ui-system/effect-custom-ui-input-routing.md
docs/ui-system/interactive-ui-latency.md
docs/research-notes/gizmo-input-probe-2026-10-12.md
