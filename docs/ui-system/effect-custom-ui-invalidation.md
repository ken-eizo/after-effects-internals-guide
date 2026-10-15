---
status: active
last_verified: 2026-10-12
primary_evidence:
  - E0-G Adobe Custom UI & Drawbot, PF_EventExtra, Tips & Tricks
  - E0-H PF_AppSuite and PF Event flag definitions
  - E2-L event-context verification warning (finding F-UI-003)
---
# PF_InvalidateRect — Effect Custom UI Redraw Scheduling

## Different operations, different owners

A custom effect's control geometry is drawn on a host-owned
Composition/Layer/Effect Controls UI surface. Requesting a
new UI painting pass is NOT equivalent to recalculating the
underlying composite or to presenting a new physical screen
frame. Separate these transitions:

  view-local state change -> UI region becomes dirty
  -> host invokes PF_Event_DRAW -> Drawbot commands
  -> host/application composition -> OS/driver display

A project parameter edit may independently invalidate render
identity, render caches and composition pixels. Hover/cursor
change need not do so.

## Invalidate the smallest correct region

PF_InvalidateRect takes a PF_ContextH and a pane-relative
rectangle. The documented NULL pointer requests an entire-pane
redraw; a finite rectangle requests the affected region.
PF_EO_UPDATE_NOW requests an immediate DRAW after the current
event returns. Without it, invalidation can be drawn lazily.

A precise dirty region must cover BOTH the old and new
positions of every affected stroke, antialiasing fringe,
selection marker, Bezier curve, shadow and attached label.
For connected geometry, invalidate the hull of the entire
affected connection, not just one moved vertex. A moving
diagnostic HUD elsewhere may need its own region, or must
be allowed to update less frequently.

The SDK's Draw event also carries an update_rect. Using an
exact invalidation region without respecting that rectangle
is an optimization hypothesis until measured against AE's
actual clip behavior and draw contract.

## Output flags are not synonyms

- PF_EO_HANDLED_EVENT: the event was handled.
- PF_EO_UPDATE_NOW: draw the invalidated pane immediately
  after the current event.
- PF_EO_NEVER_UPDATE: defer composite rerender until
  click/drag finishes; it is not a suppression of all
  Drawbot overlay repaint.
- PF_EO_ALWAYS_UPDATE: force composite rerender for
  each click or drag.
- PF_OutFlag_REFRESH_UI: broad redraw request for the
  Effect Controls, Composition and Layer UI surfaces; avoid
  it as a routine high-frequency hover invalidation.

Adobe recommends testing update flags against responsiveness
and correct pixels. Do not combine modes and then infer the
effect of any single flag without a controlled comparison.

**Region size and composite-update policy are independent axes.**
To measure whether a finite PF_Rect saves work, use identical
UPDATE_NOW/ALWAYS_UPDATE/NEVER_UPDATE flags in both the full-pane
and partial-pane cases. Otherwise a subjective improvement or
regression cannot be attributed to the dirty area. A finite region
may also reduce host compositing work without proportionally
reducing the plugin's own Drawbot command-generation cost.

Even in an overlay-only effect, ALWAYS_UPDATE requests composite
rerender for every interaction; rendering dependencies elsewhere
in the project may therefore change performance dramatically.
The flag does not mean that new effect pixel data was actually
computed each time. Count actual PF_Cmd_RENDER calls separately.

## Event-context validity

PF_InvalidateRect requires a valid host event context.
It is not safe to assume it is callable from every non-DRAW
event simply because contextH is non-null. A reproduced
KEYDOWN report and one host verification alert establish
that this boundary matters. The exact callback responsible
for a user's original alert was not captured.

Conservative sample practice restricts direct invalidation
to known DO_CLICK/DRAG contexts and requests
PF_OutFlag_REFRESH_UI for other UI state changes. This is a
DEFENSIVE IMPLEMENTATION CHOICE, not a documented exhaustive
list of legal SDK callbacks. In a historical community
report PF_InvalidateRect also worked from ADJUST_CURSOR,
so per-selector/version tests are needed before expanding
the fast path.

Do not call PF_InvalidateRect from passive PF_Event_DRAW
or from unrelated native worker threads; handle drawing
reference and suite ownership strictly inside supported
event lifetimes.

## What this contract does not guarantee

Neither UPDATE_NOW nor an invalidation call promises a
particular number of DRAW callbacks per second, a maximum
time before presentation, one distinct pointer position
per frame, or a new physical monitor image. Invalidation
can be coalesced. A fast handler may still be limited by
host callback dispatch or application display composition.

Measure requested dirty area, callback delivery,
DRAW CPU duration, host image recomposition and actual
display presentation separately.

## Sources

- https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/
- https://ae-plugins.docsforadobe.dev/effect-ui-events/PF_EventExtra/
- https://ae-plugins.docsforadobe.dev/effect-ui-events/tips-and-tricks/
- https://community.adobe.com/t5/after-effects-discussions/ae-sdk-custom-effect-ui-using-pf-event-keydowns/m-p/13977363
- https://community.adobe.com/questions-529/pf-invalidaterect-31894
- Related: effect-custom-ui-input-routing.md,
  drawbot-ui-drawing.md, interactive-ui-latency.md.

## Requested damage region versus host-reported draw area

A finite region supplied through PF_InvalidateRect is a request to the
host, not a direct graphics scissor or an owned GPU surface. Subsequent
PF_Event_DRAW.update_rect is host-supplied. Its semantics must be interpreted
in the current UI context and validated before using it to suppress
paint, especially when dealing with Composition versus Effect Controls UI.

Do not treat a negative, empty or otherwise unusable update rectangle as
proof that no user-interface drawing is permitted. Equally, do not assume
that the rectangle last submitted by the effect is guaranteed to be
the compositor's actual effective clip. These represent different
contracts and can diverge during host coalescing, view changes and
external repaint requests.

A presentation-only drag model may need room beyond the host's last
delivered pointer: an effect can conservatively request damage
encompassing the previous geometry, confirmed new geometry and a
bounded prospective pointer pose. The region must include connected
Bezier/polygon edges, selected handles, antialiasing margins and old
strokes. It must not mutate AE project state merely to arrange repaint.

If host-provided clip coordinates are unusable, a conservative
last-requested region may serve as a *fallback validation bound* for
an experimental late-input preview. Because this is weaker than
actual clipping information, retain a full host-driven redraw fallback
and test visual erasure/clipping across zoom, pane resize, host
selection changes and rapid mouse motion. Never report a speculative
preview as proof of new physical screen presentation.

An independent session-specific example with exact logs and
limitations is F-UI-008 in the research/findings registry.
