---
status: active
last_verified: 2026-10-12
primary_evidence:
  - E0-G Adobe Effect UI & Events, PF_EventUnion, PF_EventExtra
  - E0-H locally distributed AE_EffectUI.h
  - E2-L / E2-X per-experiment callback traces, scoped in findings
---
# PF_Cmd_EVENT — Effect Custom UI Event Routing

## Position within After Effects

Custom Effect UI is a host-owned interaction surface: Effect Controls
Window (ECW), Composition viewer or Layer viewer. The effect registers
interest with PF_OutFlag_CUSTOM_UI and PF_REGISTER_UI, and receives
PF_Cmd_EVENT callbacks selected and dispatched by the host. Ownership
of the viewer, selection, active tool, focus and native input message
pump stays with After Effects.

This interface must not be conflated with AEGP panels, external GUI
windows or the rendered image pipeline. Effect overlays are drawn
over the viewer and need not modify its rendered pixels.

## Event families and their different meanings

- PF_Event_NEW_CONTEXT / ACTIVATE / DEACTIVATE / CLOSE_CONTEXT:
  context lifetime and activation; allocate and discard view-local state.
- PF_Event_DO_CLICK: start of a button interaction, including
  number of clicks, modifiers and callback-specific coordinates.
- PF_Event_DRAG: continued interaction when the host has accepted
  send_drag; its last_time field indicates drag termination.
- PF_Event_ADJUST_CURSOR: a cursor-selection opportunity, not an
  unconditional high-frequency pointer stream.
- PF_Event_KEYDOWN: key-down with printable/control code encoding.
  It does not imply full key-up delivery or that AE shortcuts reach
  the effect.
- PF_Event_MOUSE_EXITED: pointer leaves the effect UI context.
- PF_Event_DRAW / IDLE: redraw opportunity and idle callback,
  neither constitutes an independent animation scheduler.

The event payload's screen_point must be transformed using
the UI callbacks when crossing frame, source, composition and
layer spaces. Its name does not imply that it can always be
interchanged with OS physical GetCursorPos coordinates.

## Click-to-drag transaction

An effect that consumes DO_CLICK can request continued DRAG
delivery with send_drag. The host controls capture, dispatch
frequency, pointer coalescing and interaction with other AE
tools; setting send_drag does not promise one event per physical
mouse movement or per display refresh.

Every model should distinguish:
1. current transient pointer/capture state;
2. view-local selection, hover and drag preview;
3. document-semantic values committed by user action;
4. independently requested UI draws.

Cancel or reconcile capture state when the drag ends, the view
deactivates, the effect loses selection or the context closes.
Do not use DRAW to make arbitrary project mutations.

## Capability and uncertainty

Modifier flags, click counts and keydown codes are documented
by the SDK; the raw event union does not provide a universal
right/middle/X-button, wheel, key-release, pen pressure, tilt or
multitouch packet contract. OS state sampling during a valid
callback can provide extra observations but is not equivalent
to AE forwarding the input transaction.

Input delivery is host, version, tool and context dependent.
The absence of one callback during a particular capture is a
version-scoped observation, not a universal SDK guarantee.

PF_AppSuite also declares PF_GetMouse, which returns mouse position
in Custom UI coordinates. This does NOT authorize calling it from
an arbitrary UI selector. A 2014 DRAW-callback report triggered
an internal verification failure, corroborated in 2017. Treat
this as a historical warning and preserve the event validity
boundary (finding F-UI-004), not as a tested current host rule.

Measured host behavior is intentionally kept OUT of this
system chapter and in independent evidence records. For
example, the archived GizmoSearchAE trace shows distinct
rates for DRAG, DRAW and ADJUST_CURSOR; see research
finding F-UI-001 and F-UI-002, and the experiment family
experiments/ui-gizmo-input.

## Design guidance

Use an AE-neutral model for hit testing, constraints and
selection, with an adapter that converts AE callback events
into model input. Maintain exact host event semantics and
source coordinate transforms in the adapter. Source or
project stream writes should be explicit and undo-aware;
hover should not be serialized as project data.

A native AE parameter such as Point Control can be a useful
comparison baseline, but native control implementation
details and fast host-private rendering paths are not exposed
merely because the controls share the Composition viewer.

## Sources

- https://ae-plugins.docsforadobe.dev/effect-ui-events/effect-ui-events/
- https://ae-plugins.docsforadobe.dev/effect-ui-events/PF_EventUnion/
- https://ae-plugins.docsforadobe.dev/effect-ui-events/PF_EventExtra/
- Related: effect-custom-ui-invalidation.md,
  interactive-ui-latency.md, view-state-and-render-boundary.md.
