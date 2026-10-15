---
status: active
last_verified: 2026-10-12
primary_evidence:
  - E0-G Adobe Custom UI & Drawbot contracts
  - E0-H local DrawbotSuite.h and AE_EffectUI.h
  - E2-X host-independent geometric drawing examples
---
# Drawbot Suites — PF_Event_DRAW Resource Lifetimes

## Role of Drawbot

Drawbot is an SDK drawing interface for host-owned custom
UI. It provides path primitives, fill/stroke, images,
optional text and surface state. It does NOT transfer
ownership of the Composition viewer, native window or
OS swapchain to the effect.

Drawing is allowed during PF_Event_DRAW. A drag or click
event should change state and request a later redraw,
not paint directly. The host can reuse and invalidate its
view surface at its own discretion.

## References and lifetimes

A Drawbot drawing reference is acquired from the host
event context. Supplier and Surface references are
obtained through Drawbot suites. A plugin that creates
pens, brushes, paths, images or fonts with NewXYZ
must release those objects using ReleaseObject as
required by the SDK.

Do not confuse suite/interface lifetimes with the
drawing reference's validity. Treat host drawing
references and any derived view-context state as
callback-scoped unless a separate documented ownership
contract says otherwise. Avoid retaining them between
independent DRAW callbacks.

## Command and allocation costs

A draw callback may need to create and release style
resources, traverse control-point geometry, and
submit text and paths. These costs can dominate even
when the underlying mathematical transformation is
cheap.

Optimization classes, independent of one particular plugin:
- Reuse identical brush/pen resources within a valid
  drawing context.
- Combine compatible geometry in paths when semantically
  appropriate; preserve path connectivity and fill rules.
- Use PaintRect instead of constructing disposable
  paths for solid rectangular elements.
- Avoid rebuilding fonts and long captions when text
  is not visible or text capability is not needed.
- Minimize repeated coordinate transformation and
  repeated path computation across identical view state.
- Respect surface clip/update region and restore any
  pushed surface state/transform.
- Do not flush aggressively: the SDK cautions that
  Drawbot Flush may cause redundant redraw/flashing.

A cached rasterized glyph/geometry image may be useful,
but its size, DPI, antialiasing and memory ownership
must be measured before treating it as a performance win.

## Composition viewer integration

Effect Custom UI is intended to overlay native viewer
geometry. The SDK provides overlay theme foreground,
shadow, stroke width and vertex size conventions.
Using those contracts can preserve AE's affordances
without creating an independent external window.

The appropriate coordinate system depends on COMP vs
LAYER context, zoom, pan, scaling and pixel aspect.
Host frame/source and layer/comp conversion callbacks
must be used rather than hardcoded screen assumptions.

## Measurements and limits

Instrument path/pen/brush/text creation counts,
callback CPU duration and the actual dirty region,
alongside host dispatch of input and DRAW events.
A reduction in CPU processing time is NOT equivalent
to an increase in distinct screen presentations.

An effect can be drawn 200 times per second yet move
a control in coarser steps if its input position changes
at a much lower rate. See the separate interactive
UI latency system model for the timing boundary.

Concrete implementation benchmarks, source diffs,
failures and session data belong in experiments and
findings, not this architecture chapter.

## Sources

- https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/
- https://ae-plugins.docsforadobe.dev/effect-ui-events/ui-callbacks/
- Related: effect-custom-ui-invalidation.md,
  effect-custom-ui-input-routing.md, interactive-ui-latency.md.

## Decoupling mostly static chrome from changing manipulators

An editor overlay may contain frequently changing geometry and a mostly
static HUD, toolbar, numeric legend or diagnostic label. It is generally
wasteful to rebuild identical text layouts/brushes and repaint fixed
rectangles for every pointer movement merely because the control-point
geometry changed. Distinguish semantic dirtiness for the content
subregions rather than invalidating every visual element together.

With host-owned Drawbot, an implementation can:
1. issue a conservative finite PF_InvalidateRect around the entire
   changed geometry (previous and new positions, curves, antialiasing);
2. inspect PF_Event_DRAW.update_rect in the host's window coordinate
   system to discover what actually needs repainting;
3. omit static HUD Drawbot commands when the update rectangle is
   fully outside that HUD and the host is retaining the untouched area;
4. fall back to full drawing if a host-supplied clip intersects the HUD,
   an update rect is invalid, text/style state changed, or the host
   requests a full repaint.

This is not equivalent to caching DRAWBOT_SurfaceRef across events.
It keeps all drawing within a valid host PF_Event_DRAW. A temporary
predictive drag preview must either remain within the invalidated
region or be rejected/fall back to confirmed coordinates; otherwise
partial redrawing may clip the visual control.

The correctness of the host's actual partial-repaint behavior
must be validated in the installed AE build, at varied zoom/DPI,
while panning and resizing. Region-only invalidation may still
cause the host to deliver a full update_rect. Neither region
invalidation nor reduced Drawbot CPU time independently guarantees
a specific monitor presentation frequency.

Measured costs from particular UI implementations belong in
research/findings and experimental raw records, not this general
contract description.

## Dynamic interaction complexity and predictable latency

For a low-latency manipulator, distinguish two types of content:
(1) the geometry that must move on every pointer update, and
(2) diagnostic or decorative chrome that does not participate
in the active drag.

When the effect's host-reported update rectangle is empty,
cannot be trusted, or the host does not offer a separately
retained HUD plane, partial invalidation by itself does not
prove the immutable chrome can be skipped while remaining
visible. One safe-to-experiment fallback is to deliberately
hide nonessential chrome only during active input capture,
request normal redraw within the documented host contract,
and explicitly restore it on release/deactivation. This
reduces Drawbot command generation at the cost of a
different transient visual state. It is not equivalent to
reusing or owning a host drawing surface across events.

Low CPU time in DRAW and a late OS cursor sample are separate
optimization axes. Neither forces the host to dispatch DRAW
callbacks regularly or proves when the monitor presents pixels.
Capture-tail gap metrics (p95/p99), confirmed-versus-speculative
handle pose, and actual input-to-present measurement are needed
before asserting overall responsiveness.

Do not merge widget appearance changes, region invalidation,
input prediction, and compositing policy into one uncontrolled
benchmark. Isolate them as independently reversible choices.
