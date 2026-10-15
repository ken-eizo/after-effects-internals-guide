---
status: supported-contract-plus-observed-warning
evidence_grade: E0-G, E0-H, E2-L, E3
last_verified: 2026-10-12
versions: SDK contract; user runtime host build unrecorded
confidence: High for validity constraint; exact failing selector unknown
---
# F-UI-003 — UI invalidation requires a valid event context

## Statement

Calling PF_InvalidateRect with a non-null contextH
is not enough to guarantee that the host considers
the current callback a valid UI invalidation
opportunity.

A real effect-host session displayed the warning:
"PF_InvalidateRect can only be called during valid events."

The offending callback was NOT captured in an event trace.
The source code before repair had direct invalidation
reachable from KEYDOWN, ADJUST_CURSOR, DEACTIVATE
and MOUSE_EXITED, so several candidates existed.

## Independent evidence

- E0-G Adobe Custom UI & Drawbot defines lazy
  PF_InvalidateRect plus PF_EO_UPDATE_NOW and
  wide PF_OutFlag_REFRESH_UI behavior.
- E2-L user-supplied AE alert screenshot, archived
  at experiments/ui-gizmo-input/user-2026-10-12-observation.md.
- E3 Adobe Community 2023 KEYDOWN report reproduces
  the same error and suggests PF_OutFlag_REFRESH_UI.
- E3 historical 2011 report says
  PF_InvalidateRect worked in ADJUST_CURSOR for
  that developer, so forbidding that selector
  categorically would overstate the evidence.

## Implication and boundary

The conservative GizmoSearchAE sample only calls
PF_InvalidateRect from DO_CLICK/DRAG and requests
broad REFRESH_UI when an actual state change arises
in other selectors. That is an implementation
guard, NOT a confirmed exhaustive list of legal
event contexts.

Test each selector and installed AE version
separately to tighten the rule. Do not make
project changes merely to force redraw.

## Sources

- https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/
- https://community.adobe.com/t5/after-effects-discussions/ae-sdk-custom-effect-ui-using-pf-event-keydowns/m-p/13977363
- https://community.adobe.com/questions-529/pf-invalidaterect-31894
- General contract:
  docs/ui-system/effect-custom-ui-invalidation.md
