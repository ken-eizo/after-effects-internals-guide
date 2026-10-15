---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L, E2-X
scope: archived AE native effect custom UI v8 trace, Windows 10
confidence: high for classified QPC callbacks; host/input cause unresolved
---
# F-UI-011 - DRAW gaps must be classified by intervening host input demand

## Observation

An inter-DRAW interval measured during an AE-captured drag is not by itself
proof that an input update was awaiting paint. Some intervals contain
**no PF_Event_DRAG callback** in the recorded event stream; others contain
one or more DRAG callbacks. They must be reported separately.

This does not establish that the mouse physically stopped when no DRAG was
recorded: AE may have withheld/coalesced input. No raw HID timestamps or
physical Present timestamps were recorded.

## Preserved evidence and exact method

Immutable local host trace:
`experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v8-all-redraw-modes-c6cd2633ef5c.csv`

SHA256:
`c6cd2633ef5cb427177c6adf758f570cf1c45be85022067315a01043037de419`

The input TEMP CSV was separately hashed and matched this archived original.
38,805 effect UI events; QPC frequency 10,000,000 ticks/second.

Reproduction:
`python D:/Developer/GizmoSearchAE/tests/analyze_demand_gaps.py <path-to-v8-csv>`

The analyzer considers consecutive DRAWs with active drag state, matching
REDRAW mode, HUD visibility and LATEST state, excluding gaps >=250ms.
It resets at CLICK, terminal DRAG and mode/configuration changes. It
classifies each interval based on whether a host DRAG was recorded
*between* those DRAW callbacks. Percentiles are linearly interpolated.

| Mode / HUD / LATEST | Class | Intervals | DRAW gap p99 | Max |
| --- | --- | ---: | ---: | ---: |
| 7 / on / on | With intermediate DRAG | 392 | 26.429 ms | 70.094 ms |
| 7 / on / on | Without recorded DRAG | 790 | 59.688 ms | 193.543 ms |
| 5 / off / on | With intermediate DRAG | 378 | 61.244 ms | 118.112 ms |
| 5 / off / on | Without recorded DRAG | 761 | 14.320 ms | 21.735 ms |

In mode 7/HUD on/LATEST on, the interval from the last recorded
DRAG to the next DRAW in the demand class had p99 about 14.932 ms,
with a maximum about 20.434 ms.

The striking *opposite* pattern for modes 7 and 5 shows why simple
comparisons of unconditional inter-DRAW p99 do not isolate host scheduling.
The naturalistic trials have different gestures, host image load, cursor
movement, UI state and event delivery. These are **descriptive**, not a
controlled causal comparison or a ranking of redraw modes.

## Design implications

- Record drag demand and DRAW dispatch, not merely overall callback rate.
- Separate demand-bearing and no-recorded-drag intervals, and retain
  sample counts, excluded gaps, sub-condition and confidence bounds.
- For actual end-to-end stall attribution, capture an independent hardware
  pointer-motion timeline, host event-queue/CPU scheduling and actual
  image Present. ETW tracing alone may still be insufficient to prove photons.
- In an input-generation scheduler, distinguish an Invalidate request
  accepted by the SDK, a DRAW callback with submitted Drawbot commands,
  and physical presentation. They are different boundaries.

## Related findings

F-UI-001 (DRAW vs DRAG cadence),
F-UI-006 (callback gaps vs own handler time),
F-UI-009 (fast model is insufficient for end-to-end latency).

Public event contract: `docs/ui-system/effect-custom-ui-invalidation.md`.
