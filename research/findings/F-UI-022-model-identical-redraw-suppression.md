---
status: source-change-validated
last_verified: 2026-10-12
evidence_grade: E1-code / E1-model-benchmark, not in-host result
scope: GizmoSearchAE native Effect Custom UI; reductions in redundant PF_InvalidateRect attempts
---
# F-UI-022 — Suppress visually identical redraws without discarding input

## Defect and fix
Former GizmoSearchAE Model::move returned redraw=true for every
pointer-position change during dragging, including when snapped or
axis-constrained positions had *not* changed.

Fixed the host-independent model in GizmoSearchAE/ae_plugin/GizmoModel.hpp:
- NodeHit or Translate: compare newly transformed visible node
  coordinates to the previous nodes; request redraw only on change.
- Rotate: respect angular quantization, including subthreshold motion.
- Scale: respect quantized scale when Shift is held.
- Preserve input pointer, modifier state, last input position, and
  selected node state even when no redraw is necessary.
- Preserve redraws for live event-counter HUDs in legacy modes 0-6;
  the no-visual-change suppression applies only when drag chrome is
  omitted or the HUD is hidden.
- Preserve press and terminal DRAG invalidation behavior in adapter.

PF_InvalidateRect, previously measured at median ~370us and
p99 ~3950us, is an expensive host-owned synchronous request.
Avoiding calls for identical visual states can lower total AE UI
synchronous workload, but it cannot force host DRAW every 240Hz tick.

## Evidence
Reproducible portable executable:
GizmoSearchAE/build-ae/Release/GizmoRedrawSuppressionBench.exe
Source:
GizmoSearchAE/ae_plugin/GizmoRedrawSuppressionBench.cpp
Regression:
GizmoSearchAE/ae_plugin/GizmoCoreTests.cpp
CTest GizmoRedrawSuppression

Synthetic 200,000 integer-pixel events per scenario:
- Free movement: 200,000 redraw requests (zero loss).
- Grid snap: 10,417 requests (94.79% avoided).
- Shift-constrained Y jitter: one redraw request.
Observed single-core steady_clock block-average model costs
were 16.42ns (free), 58.35ns (snap), 21.11ns (axis) per packet.
These are model-only block averages, not distribution percentiles,
AE SDK calls, Drawbot, GPU presents or input-to-photon speed.

## AE host and physical limitations
WPR trace captured 2026-10-12 19:03 on actual AE/Lean drag:
UI TID 92276 CPU-run intervals were 52.6%, 68.7%, 31.2% of
three successive observation windows. The user also moved the
AE window; ~2.3s and ~0.94s UI delays are confounded.
The AE UI workload is dominated by more than this local model code;
user-visible 240Hz every-refresh delivery is not guaranteed.

Latest Lean source also omits QPC and draw/drags-per-second smoothing
statistics while the HUD is hidden, and computes atan2/sqrt at the
beginning of a drag only when in the Rotate/Scale transform tool.
Both preserve user-facing geometry/control behavior.

Real host latency improvement from the rebuilt AEX is **not yet
measured**; in-use AEX should not be hot-replaced while AE is running.
