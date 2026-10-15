---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L
scope: GizmoSearchAE REDRAW 9 in native AE Effect Custom UI
confidence: moderate on drawn-callback correlation; GPU/physical output unknown
---
# F-UI-020 — Most mode-9 long DRAW intervals are not explained by a >4.167ms synchronous redraw call

## Why this matters

The user reported that sporadic Gizmo stutters worsen when the
whole computer or AE is heavily loaded. A successful low-CPU
plug-in model does not bound input-to-visible-frame timing.

Analyzed an immutable saved v9 callback capture in:
GizmoSearchAE/scratch/load-jitter-20261012/events.csv
SHA256 1DC06760F1D1A8415D24992D1EACC8B0712B7D5C8B4E4002696B910BB6F47793.

For mode 9, consecutive DRAW callback starts in active dragging,
with matching HUD and LATEST settings, gaps <=100ms:
- 4,337 intervals contained >=1 delivered DRAG.
- 2,831 of these intervals exceeded 4.167ms (one 240Hz display period).
- Only **36 / 2,831** such long intervals contained a measured
  synchronous invalidation SDK call longer than 4.167ms.
- In these long intervals the p50 aggregate cost of recorded
  intermediate callbacks was about 0.472ms.
- 13,080 intervals did not contain any recorded DRAG; 6,622 exceeded
  4.167ms. Such no-drag intervals do not demonstrate that a needed
  pointer update was missed.

This is a *correlation from callback events*, not a causal profile.
Input/HID messages before AE dispatch, AE UI thread scheduling,
the rest of host code, GPU queue, DWM, display scanout and photons
are not observed. The long DRAW interval cannot be attributed to a
specific unobserved subsystem without ETW/WPA/Present data.
The log includes ordinary human mouse movement, not a calibrated
constant-velocity 240Hz hardware signal.

Reproduce:
python D:/Developer/GizmoSearchAE/tests/analyze_stall_attribution.py <events.csv>
Synthetic parser regression:
python D:/Developer/GizmoSearchAE/tests/test_analyze_stall_attribution.py

Engineering implications:
- Do not spend all effort caching AE SDK suite pointers or shaving
  only the synchronous invalidation call. Both may lower local CPU
  but do not explain the majority of these host callback gaps.
- Continue aggressive plug-in hot-path reduction in Lean builds,
  but investigate AE UI thread Ready/Wait/Running, message capture
  and DWM actual presents under load as the next high-leverage work.
- Preserve REDRAW 9 as reference. Experimental modes 10/11 did not
  show clear positive real-host results in natural-use captures.
- No new Win32 overlay or privately patched AE scheduler is in use.
