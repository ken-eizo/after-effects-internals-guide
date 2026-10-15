---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L
scope: GizmoSearchAE v9, one recorded host session (AE build not encoded)
---
# F-UI-014 - No sample effect pixel render during mode-8 captured drag

## Claim and scope

In the archived 14,941-event v9 log, the process-wide
`render_calls_total` counter did **not increase** during
any of the 3,909 mode-8 drag-active event entries. Of those, 2,922
were PF_Event_DRAW. Therefore the research effect's CPU pixel-copy
render path did not execute in that selected window, even though
its own UI produced thousands of Drawbot scenes.

This proves only that this research effect's `PF_Cmd_RENDER` counter
was unchanged at sampled callback boundaries. It does NOT prove
that AE performed no other effect renders, preview recomposition,
graphics allocations, DWM work, GPU submission or physical presents.
It is also not a universal result for other AE projects.

## Evidence

Immutable file:
`experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v9-initial-mode8-comparison-91c9cbb1.csv`

SHA256 `91c9cbb1c178e0ebe0281e71fcb5209bedc932ba6d9f31e8f4e93ef258c8922b`.

Reproduce with:
`python D:/Developer/GizmoSearchAE/tests/analyze_render_pressure.py <csv>`

The counter progressed from 0 to 5 across the whole capture,
but **all five** new render calls appeared in mode 5, drag
inactive (two sampled counter-increase events).
`mode 8, dragging=1: callbacks 3909, DRAWs 2922, effect render delta 0`.

This is especially significant because an earlier candidate
optimization consolidated image identity copying into one large
memmove. That optimization may benefit image rendering, but the
log demonstrates it cannot account for mode-8 drag smoothness
in this selected test.

## Engineering impact

Focus the investigation on host-input routing, redraw scheduling,
Drawbot submission, Composition/Layer viewer overlay compositor,
GPU queue, DWM and display. In particular, see F-UI-013 for
the millisecond-class interval between PF_Event_DRAG handler
completion and the next PF_Event_DRAW.

On future tests, record the current AE build separately, because
the v9 log schema does not include a host file-version field.

Related: F-UI-009, F-UI-012, F-UI-013.
