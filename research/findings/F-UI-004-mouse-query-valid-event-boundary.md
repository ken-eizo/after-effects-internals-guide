---
status: historical-report-not-host-confirmed
evidence_grade: E0-G, E0-H, E3
last_verified: 2026-10-12
versions: CS6/CC-era reports (2014, 2017); current 26.x untested
confidence: documented API presence; limited runtime callback validity evidence
---
# F-UI-004 — PF_GetMouse has an event-context validity boundary

## Statement

PF_AppSuite contains PF_GetMouse(PF_Point*), which the Adobe SDK Guide
describes as returning mouse coordinates in the custom UI coordinate
space. However, the existence of that function does not imply it is
callable from every PF_Cmd_EVENT subtype.

An Adobe Community developer report (2014) describes receiving the exact
error "PF_GetMouse can only be called during valid events" when calling
it from PF_Event_DRAW. A 2017 follow-up reports the same limitation.

## Evidence

- E0-G: Adobe Useful Utility Functions / PF_AppSuite, PF_GetMouse.
- E0-H: AE_EffectSuites.h in distributed SDK, comment restricting use
  to processing an event in an effect with custom UI.
- E3: 2014 first-person DRAW failure and 2017 follow-up.

## Interpretation

The header comment is not an exhaustive selector whitelist.
The failure is historical and not yet independently reproduced
on the user's AE build. Calling PF_GetMouse from DRAW solely to
seek smoother input would risk a host internal-verification alert,
so it must not be added as an unguarded fast path.

Do not conflate this error with PF_InvalidateRect's independent
valid-event restriction. Do not infer that storing coordinates in
a click-only continue_refcon array makes them persist across DRAW;
the forum thread also documents that this failed for its author.
Use context-local state for presentation, with documented lifetime
and host-appropriate persistence boundaries.

## How to falsify / update

A safely isolated version-specific test should first confirm legal
non-DRAW selectors and coordinate units without changing project
state. The historical DRAW failure is already sufficient not to
experiment with unguarded calls in production or the current user's
live project. Host validation of DRAW should be avoided unless a
new official contract explicitly permits it.

## Sources

- https://ae-plugins.docsforadobe.dev/effect-details/useful-utility-functions/
- https://community.adobe.com/questions-529/get-mouse-position-during-custom-ui-draw-event-29345
- General model: docs/ui-system/effect-custom-ui-input-routing.md
