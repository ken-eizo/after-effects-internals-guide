---
status: observed-scoped
evidence_grade: E2-L and E2-X
last_verified: 2026-10-12
versions: User's AE build not recorded in event log
confidence: High for event absence within sampled segments
---
# F-UI-002 — Cursor-adjust events were absent inside captured drags

## Statement

In the observed Effect Custom UI session, the host
delivered no PF_Event_ADJUST_CURSOR callbacks between
the first and last PF_Event_DRAG callbacks of any
of the 11 analyzed drag segments.

The same session produced 1,841 ADJUST_CURSOR callbacks
outside those sample intervals, showing that the
callback was otherwise active.

This does NOT prove a universal SDK rule. It shows
that ADJUST_CURSOR did not provide a second, faster
mouse-position stream during AE-managed drag capture
for this test.

## Evidence and reproduction

Raw event source:
experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v3.csv

SHA256:
4b91e90057004ac3ddfa46791a5c164bd6688ff2cc22d924a83e200e6622d75f

Run:
D:/Developer/GizmoSearchAE/tests/analyze_cursor_during_drag.py

The parser examines all event timestamps between each
segment's earliest/latest DRAG. Eleven segments each
had at least six events, and each returned zero
ADJUST_CURSOR events. This is a zero count on an
observed finite sample, not an API prohibition.

## Scope and falsification

Repeat with a deliberately continuous drag while
changing the AE build, active tool, Composition/
Layer UI, selection and send_drag policy.
One validated ADJUST_CURSOR during captured DRAG
falsifies any broader assumption that the event
cannot occur during capture.

## Consequence

A custom UI implementation should not depend on
ADJUST_CURSOR to obtain high-frequency positions
during a captured drag without testing its delivery.
Capture and hover routing are separate host behaviors.

General contract:
docs/ui-system/effect-custom-ui-input-routing.md
