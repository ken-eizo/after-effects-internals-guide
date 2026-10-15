---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L
scope: GizmoSearchAE native Custom UI, recorded v9 event trace
---
# F-UI-015: Host redraw API request dominates plugin-owned DRAG CPU

In newly archived 2026-10-12 GizmoSearchAE v9 observations, REDRAW 9
active dragging/HUD ON/LATEST ON had 1781 selected DRAG callbacks.
The measured elapsed duration of the entire SDK redraw request section
(AcquireSuite + PF_InvalidateRect + ReleaseSuite) was:
- p50 302.1 microseconds
- p99 3714.5 microseconds

The remainder of each DRAG handler, after subtracting this section,
was p50 1.7 microseconds / p99 48.78 microseconds.
Therefore a sub-10us pure model does not bound the callback duration.

REDRAW 9 had 1781 matched DRAG-to-next-DRAW intervals in the same
selection: the post-DRAG-return interval was p50 1.0759ms and
p99 3.6557ms. Its cause is not isolated to AE code: OS scheduling,
other callbacks and host application work may contribute.

Source snapshot in GizmoSearchAE:
scratch/end-to-end-audit-20261012/events-v9-snapshot.csv
SHA256 461678CEB1416A1245C9AA7C6F1873545DFC4E6D26678D6DCB0180AEB2BAD020

Analysis:
tests/analyze_input_budget.py
tests/analyze_post_drag_return.py

A new opt-in four-way sampled profiler now separates AcquireSuite,
PF_InvalidateRect, ReleaseSuite, and outer whole-API duration
without changing REDRAW 9 scheduling decisions.
GizmoSearchAE-invalidation-stages-v1.csv will be generated
on the next actual AE host test and EXPORT. No real substage
profile has yet been collected and no speedup is claimed.

Do not cache acquired suites across separate Effect command selectors
without a documented lifetime guarantee. No AE process binary patches
were made. GPU Present and physical visibility were not recorded.
