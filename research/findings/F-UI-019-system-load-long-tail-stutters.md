---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L / E0-H
scope: AE native Effect Custom UI v9/10/11 under mixed real-user workloads
---
# F-UI-019 - Rare multi-frame UI stalls persist after redrawing-mode experiments

New 2026-10-12 host event and invalidation sidecars demonstrate
that the user's native Effect Custom UI Gizmo still experiences
long-tail processing intervals, even on a genuine 240Hz monitor.

Mode-9 602 sampled PF_InvalidateRect calls:
median 369.6 microseconds, p99 3948.6us, maximum 15.34ms.
AcquireSuite median 7us and ReleaseSuite median 3us,
showing the dominant synchronous cost is the AE-owned call itself.

Matched DRAG entry -> next DRAW callback end, HUD ON/LATEST ON:
mode 9 n=2905, median 1.7951ms / p99 8.082ms
mode 10 n=134, median 5.9145ms / p99 15.645ms
mode 11 n=450, median 2.3067ms / p99 11.538ms.
Different sessions and cursor movements: NOT matched A/B trials.
The measurements do not establish that mode 9 is universally better
or that all stalls occur inside Adobe code.

Using Windows EnumDisplaySettings and MonitorFromWindow, the
currently running AE window was found on DISPLAY3,
which reported 1920x1080 at 240Hz. This excludes using the wrong
120Hz/60Hz display as the immediate cause of the report; it
does not establish actual GPU/DWM presentation cadence.

Evidence in GizmoSearchAE:
scratch/load-jitter-20261012/events.csv
scratch/load-jitter-20261012/invalidate.csv
scratch/load-jitter-20261012/drawbot.csv
SHA256 for events 1DC06760F1D1A8415D24992D1EACC8B0712B7D5C8B4E4002696B910BB6F47793

The new experimental profiling instrumentation adds
QueryThreadCycleTime side by side with a QPC timestamp around
PF_InvalidateRect, sampling under REDRAW 8/9/11. The next
instrumented AE EXPORT writes invalidation-stages-v2.csv.
This is not yet collected in the running AE application, and
cycles are NOT convertible to CPU seconds without calibration.
A low cycles/wall ratio may indicate a wait or OS preemption,
but proof requires a context-switch ETW trace.

Two build variants are available and smoke-tested:
- GizmoInputProbe.aex diagnostic
- GizmoInputProbeLean.aex reduced instrumentation, startup
  mode 9 / fast ON / latest ON / diagnostic HUD hidden.

The user has NOT tested the newly built Lean variant in AE,
and no physical 240Hz frame guarantee is claimed.
Installed host AEX and user project were not modified.
