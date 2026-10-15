---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L / E0-G / E0-H
scope: Native Effect Custom UI, v9 recorded host trace, AE 26.x
---
# F-UI-017 — PF_InvalidateRect dominates sampled redraw request CPU

## Observation

A newly obtained timing sidecar from GizmoSearchAE contains 565
mode-9 successful redraw request records, sampled approximately once
per fourth eligible DRAG. The adapter's QPC timestamps measure the
calls separately:
- AEFX_AcquireSuite p50 7.0us, p99 23.608us.
- PF_InvalidateRect p50 367.9us, p99 3953.916us.
- AEFX_ReleaseSuite p50 3.0us, p99 14.336us.
- Total p50 380.3us, p99 3973.208us.

The invalidation call itself is the dominant synchronous delay;
trying to cache Suite handles across event lifetime would not solve
the main observed cost and risks breaking host reference management.

## Evidence

The original CSV was preserved at:
GizmoSearchAE/scratch/240hz-audit-20261012/invalidate.csv
SHA256:
0E6932D99FE2803887D3EE93B2D3520E635818D8FBDA8ED19D14AD969696B5CC

The source host event/Drawbot records are preserved in the same
folder; modes and sample populations are mixed.

Reproduce:
python GizmoSearchAE/tests/analyze_invalidation_stages.py invalidate.csv

## Architecture and limits

PF_InvalidateRect takes a host-owned pane and triggers the host's
invalidation scheduler. The public SDK exposes no option to guarantee
10us return time, no GPU completion fence, and no 240Hz callback
delivery schedule. The cost observed is wall-clock elapsed time
of the call, not a profile of its internal subfunctions.

User-reported lag and host delivery intervals cannot be fully
attributed to this call; separate QPC and ETW evidence are needed.

Experimental mode 10 uses PF_OutFlag_REFRESH_UI instead of
PF_InvalidateRect, with UPDATE_NOW. This may refresh the ECW,
Comp and Layer views more broadly and hurt performance.
Experimental mode 11 uses a swept finite invalidation rectangle
in Points/Bezier drag while retaining UPDATE_NOW and clipping
out-of-bounds late samples. Both are opt-in and NOT host-validated.
Mode 9's original behavior remains intact.
