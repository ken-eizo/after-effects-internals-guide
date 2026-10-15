---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L
scope: AE native PF_Event_DRAW during captured DRAG
---
# F-UI-018 — 240Hz host DRAW cadence is not reliably sustained

## Data

A retained AE session recording yielded 45 sustained active-drag
sessions (>=0.5s) in REDRAW 9, HUD ON, LATEST ON.
Total duration 54.71 seconds, 10,063 PF_Event_DRAW callbacks.
Observations:
- Conditional DRAW gap median 4.223ms.
- 50.8% of gap samples exceeded 4.167ms (240Hz frame period).
- Gap p95 11.607ms, p99 23.382ms.
- Observed callback mean in these selected sessions 183.1/s.
- The display handle changed between two Drawbot callback
  submissions in 5,172/10,018 intervals.

This is NOT a measurement of actual displayed frames per second,
input-to-photon latency, or a universal ceiling on AE's event rate.
Selected sessions, pointer activity, and host scheduling may bias
rates; the display handle may remain stationary legitimately.

Comparative mode-8 HUD ON/LATEST ON selected sessions showed
162.5 callbacks/second, gap median 3.485ms; 46.4% were above
4.167ms. These samples do not establish identical pointer load.

## Display configuration

Read-only Windows EnumDisplaySettings reported:
DISPLAY1: 1920x1080@120Hz
DISPLAY2: 3840x2160@60Hz
DISPLAY3: 1920x1080@240Hz

The physical 240Hz monitor is available to Windows, but the
currently selected AE composition viewer's actual display
was not established before AfterFX exited. Monitor configuration
alone does not imply any AE callback delivery rate.

## Evidence

Source event snapshot:
GizmoSearchAE/scratch/240hz-audit-20261012/events.csv
SHA256:
95A7BF79979ECCDC8D04EC0FCF3642FF8F4A7FEB9765932731C0EE0AB7DCEC1A

Reproduce:
python GizmoSearchAE/tests/analyze_240hz_eligibility.py events.csv

## Interpretation

To deliver an updated native gizmo on every monitor refresh, AE
must schedule and paint appropriate host overlays before each
presentation deadline. A fast plugin callback alone does not
guarantee AE will generate 240 distinct rendered frames.

Further work requires controlled movement, confirmed AE target
monitor, ETW UI-thread scheduling, GPU/DWM Present timestamps,
and display measurement where strict photon timing is desired.
