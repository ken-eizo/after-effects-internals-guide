---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L, E2-X, E0-H
scope: GizmoSearchAE; official SDK 25.6; Windows 10
confidence: high for measured callback timings; host scheduling owner unresolved
---
# F-UI-009 - Sub-microsecond manipulator model does not bound host DRAW delivery

## Independent observation

In an After Effects Effect Custom UI session, a pure manipulator
state update can complete in well below 0.01 ms while the host
still supplies some PF_Event_DRAW callbacks tens of milliseconds apart.
Source-level CPU optimization does not therefore provide a bound on
input-to-display delay or physical frame presentation.

This does NOT establish that the host caused all elapsed gaps:
gaps may contain stationary mouse periods, focus changes, UI scheduling,
GPU contention, or DWM compositor scheduling.

## Preserved user AE host trace

Path:
experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v8-all-redraw-modes-c6cd2633ef5c.csv

SHA256:
c6cd2633ef5cb427177c6adf758f570cf1c45be85022067315a01043037de419

38,805 UI callbacks were recorded. In active REDRAW-7 / HUD-visible /
LATEST-enabled drags (1,188 DRAW callbacks):
- DRAW CPU median about 0.154 ms and p99 about 2.618 ms;
- inter-DRAW gap median about 6.397 ms and p99 about 57.249 ms;
- 23 gap observations over 50 ms (gaps over 250 ms excluded).

In active REDRAW-5 / HUD-hidden / LATEST-enabled drag (1,143 DRAWs):
- DRAW CPU median 0.108 ms, p99 0.485 ms;
- inter-DRAW gap p99 about 28.388 ms.

These are naturalistic traces, not gesture-matched comparisons.
The trace lacks physical Present, photon and raw HID timestamps.

## Release-only core microbenchmark

Command:
D:/Developer/GizmoSearchAE/build-ae/Release/GizmoPipelineBench.exe --strict

7 isolated, host-independent CPU paths were measured using 6,000
blocks of 64 calls. p99 of per-call BLOCK AVERAGE (microseconds):

| Pure CPU path | p99 |
| --- | ---: |
| Model move, 6 handles | 0.173 |
| Model move, 24 handles | 0.175 |
| Swept geometry, 24 handles | 0.739 |
| OS-pointer-to-view math, without actual OS query | 0.214 |
| Input generation / coalescing state | 0.0078 |
| Redraw policy lookup | 0.161 |
| 24-handle geometry staging | 0.103 |

All seven p99 values are under a 10-microsecond research goal.
These are not per-call worst-case bounds: scheduler interruptions
produced much slower individual block averages in this run.
No AE, Drawbot, GPU or display operation is included here.

## Unmet callback performance gate

D:/Developer/GizmoSearchAE/tests/latency_budget_gate.py

Applying a 100-microsecond p99 gate to Drawbot acquisition,
cursor-sampling stage, scene submission, release and total DRAW
in the v8 AE trace produced 47 stage-by-mode/HUD/LATEST violations.
Thus the user-requested maximum budget is NOT achieved, and the
current build must not be described as a completed 0.01ms engine.

For REDRAW 7/HUD-visible/LATEST-enabled, Drawbot scene p99 was
about 2.26 ms and complete DRAW callback p99 about 2.62 ms.

## Independent host scheduler experiment

The new host-independent GizmoFrameScheduler.hpp tracks semantic
input changes and outstanding whole-pane redraw requests.
An opt-in REDRAW 8 experiment uses lazy invalidation flags,
Drawbot and full-pane repaint as REDRAW 7, while coalescing a
redundant PF_InvalidateRect request until the host DRAW arrives.
The first CLICK and final DRAG force requests; if a pending DRAW
is not received for approximately 24ms, the next DRAG may reissue.

This is NOT guaranteed to help. If the host requires repeated
invalidate requests for proper scheduling, mode 8 can regress.
Its advantage and correctness require a live AE trial and v9 log.
Do not promote the mode to default without measured improvement.

## Necessary next step: trace the boundary

A user-initiated WPR run with CPU/GPU/DesktopComposition profiles
could reveal UI thread scheduling, GPU submission and DWM frame
timing missing from AE callback logs.

D:/Developer/GizmoSearchAE/tests/capture_host_etw.ps1

ETW is deliberately opt-in, requires elevation and may use
substantial disk space. It is not a physical photon sensor.
No corresponding ETL has yet been collected.

Public contract: https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/
General design: docs/ui-system/interactive-ui-latency.md
Raw evidence: experiments/ui-gizmo-input/README.md
