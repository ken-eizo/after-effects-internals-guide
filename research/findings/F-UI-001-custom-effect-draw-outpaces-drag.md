---
status: observed-scoped
evidence_grade: E2-L and E2-X
last_verified: 2026-10-12
versions: User's actual AE build not recorded in CSV
confidence: High for logged callbacks; limited to this session
---
# F-UI-001 — UI drawing can outpace input-state updates

## Statement

During active user manipulation in one Composition Custom UI
session, the effect received substantially more drawing
callbacks than drag-position callbacks. The extra drawings
could not acquire different positions from the existing
host-event-driven model unless an independent input sample
or changed state was provided.

This is an observation about one host session, NOT a
general After Effects refresh-rate limit.

## Evidence

Archived CSV:
experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v3.csv

SHA256:
4b91e90057004ac3ddfa46791a5c164bd6688ff2cc22d924a83e200e6622d75f

- 4,945 UI callbacks: 552 DRAG, 1,778 DRAW,
  1,841 ADJUST_CURSOR and other event types.
- 11 active DRAG segments (defined by gaps of <250ms,
  each at least six samples): 551 drag events.
- DRAG gap p50 = 15.539ms; p95 = 37.994ms
  inside those segments.
- Per-segment DRAG event averages ~37–61Hz;
  DRAW averages ~110–179Hz for matching intervals.
- One segment had 118 DRAG and 350 DRAW in 2.219s.

The plugin model in this logged version updated dragged
handle positions in DRAG, and DRAW painted its current
stored model. This source observation explains why
extra DRAW calls can repaint identical logical positions.

## Reproduction

Run:
D:/Developer/GizmoSearchAE/tests/analyze_host_drag_cadence.py

The archived CSV is an authentic user-host trace.
The parser is an offline reproducible analysis; it
does not run an AE-host integration experiment itself.

## Caveats and counterhypotheses

An observed 205.1Hz DRAW HUD sample is a short-window
EWMA, not physical monitor presentation. The logged
DRAG gaps can include changes in user velocity, brief
stalls or mouse hardware behavior. The AE version,
present timeline and OS input history were not saved.

The result therefore does not establish that AE
always caps DRAG at 60Hz or that every individual
DRAW produced a physical frame.

## Architectural implication

Input delivery, transient model update, DRAW callback
and display presentation are separate timing domains.
A handler CPU optimization alone need not increase
the number of unique interactive positions.

General model:
docs/ui-system/interactive-ui-latency.md

Full experiment notes:
experiments/ui-gizmo-input/README.md
