---
status: observed-scoped
evidence_grade: E2-L and E2-X
last_verified: 2026-10-12
versions: user's exact AE build not recorded
confidence: High for QPC recorded intervals; stall cause remains unknown
---
# F-UI-006 - DRAW callback gaps can greatly exceed effect drawing CPU time

## Statement

The elapsed interval between successive host DRAW callbacks
during a drag can be far larger than the CPU time consumed
by the plugin drawing function in either callback.
Callback execution time alone therefore does not explain
all measured callback spacing.

## Evidence

Immutable trace: experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v5-all-modes.csv
SHA256: a2ffd279df34c57508da2bc8b9e89388c87fec39b745daf23221a36468b931e1

Reproducible scripts:
D:/Developer/GizmoSearchAE/tests/analyze_stalls.py
D:/Developer/GizmoSearchAE/tests/analyze_v5_gestures.py

One segmented REDRAW 3 drag of about 1.5 seconds recorded a
maximum consecutive DRAW gap of approximately 193ms, while
its longest individual DRAW handler duration was about
7.84ms. Other recorded mode-1 and mode-3 gestures contained
gaps over 100ms with handler durations mostly below 10ms.

This finite trace records neither pointer-hardware event
timestamps nor image Present timestamps. A brief pause
by the operator, AE UI scheduling, OS scheduling or
render contention could all contribute. The observation
must NOT be restated as a 193ms intrinsic host bug.

## Consequences

A benchmark of geometry model nanoseconds or the Drawbot
handler p50 does not prove smooth interaction. Callback
arrival p95/p99, distinct logical handle positions,
host image recomposition, visible Present and source-input
timing are separate metrics. A low CPU handler time
cannot force the application to deliver a new DRAW.

docs/ui-system/interactive-ui-latency.md
