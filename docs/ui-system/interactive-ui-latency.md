---
status: active
last_verified: 2026-10-12
primary_evidence:
  - E0-G Adobe Effect UI & Events and Custom UI/Drawbot
  - E0-H effect event and draw reference API
  - E2-L observed callback timestamps in version-scoped UI probes
---
# PF_Cmd_EVENT — Input-to-Drawbot Presentation Boundaries

## Distinct clocks

An editor's manipulator is an interaction pipeline rather than
a single frame rate. Its independently timed stages include:

1. Pointer hardware reports and OS pointer state.
2. Application input dispatch, selection and capture.
3. UI interaction model updates (hover, snap, drag preview).
4. Invalidation requests and host DRAW callbacks.
5. CPU draw-command preparation and GPU/UI composition.
6. OS display presentation and physical scanout.

The viewer's timeline/composition FPS is a separate content
evaluation rate. The monitor refresh is a physical display
cadence. Neither determines how often a plugin receives
distinct input coordinates or how many UI overlays are
actually presented.

## Independent observables

Measure callback arrival using a monotonic clock
and examine inter-arrival p50/p95/p99, not only
the inverse of the last time gap. Record at least:

- pointer coordinate change count and timestamp;
- input callback type, delivered event and capture state;
- value/update generation number in the interaction model;
- requested dirty region and update flags;
- draw callback start/end and the generation drawn;
- actual application/OS present and observed visible
  position (requires separate capture/instrumentation).

A high DRAW callback count can repaint unchanged input
positions; a high event count can also be collapsed into
fewer visible presentations. Conversely, low callback CPU
time does not prove low input-to-photon latency.

GPU submission, swapchain Present and physical screen
appearance are different stages. Tools measuring one do
not automatically establish the other.

## Latency and sampling strategies

A robust design distinguishes authoritative editing
state from short-lived presentation state.
A simple state machine can process ordered press/release,
snap, key and document writes while using the freshest
currently available pointer sample for visual preview.

Potential implementation classes:
- reduce unnecessary host recomposition and large
  invalidations;
- maintain lightweight view-only drag previews and
  commit semantic changes at valid user-action boundaries;
- obtain newer pointer samples, where permitted, before
  a host-owned drawing callback;
- coalesce obsolete intermediate moves while preserving
  event ordering, hit targets and drag cancellation;
- cache purely presentational display geometry
  separately from render-dependent image data.

Late sampling cannot force the host to dispatch DRAW at
a higher cadence. The mapping from OS physical pointer
coordinates to host viewer pixels is also a distinct
coordinate contract to validate under DPI, zoom and
monitor changes.

## How to choose experiments

To distinguish different bottlenecks, compare input
arrival vs DRAW, unchanged vs changed model generations,
DRAW CPU time vs visible presentation, and large vs
small invalidated regions. Keep other factors fixed:
host version, active tool, panel focus, monitor refresh,
viewer zoom, content render load and device.

An ordinary built-in point control can serve as a
host-native reference to distinguish plugin code costs
from global composition-view scheduling. Do not infer
its private implementation from similar appearance
alone. Native-host parity is a useful acceptance target
even if an arbitrary 240Hz figure proves unrealistic
on a given display and host build.

## Scope and evidence

This chapter contains general timing distinctions,
not one plugin's incident timeline, benchmark numbers
or a proposed external GPU window architecture.
Per-run data, negative results and host-version
details remain under experiments; observed claims
are promoted to one finding per independent fact.

## Sources and cross-references

- https://ae-plugins.docsforadobe.dev/effect-ui-events/effect-ui-events/
- https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/
- https://ae-plugins.docsforadobe.dev/effect-ui-events/PF_EventExtra/
- Related: effect-custom-ui-input-routing.md,
  effect-custom-ui-invalidation.md, drawbot-ui-drawing.md,
  view-state-and-render-boundary.md.

## Old and new pointer sample coordinates are separate states

Native Effect Custom UI may deliver a captured DRAG coordinate at
one cadence, while a later DRAW observes a more recent mouse position
through a permitted operating-system query. A late-sampled cursor
position can be used to produce a **temporary presentation model**
without overwriting the host-delivered editing transaction.

Region-limited rendering introduces a second correctness constraint:
the prospective visual model may extend outside the region previously
invalidated. Keep both the confirmed edit model and the independent
damage-bound geometry; allow a bounded preview only when it is
conservatively covered by a requested and, when available, valid
host-reported draw region.

Never interpret a missing/invalid host update rectangle as a fresh
cursor position; the two data types describe different layers of
the pipeline. Similarly, receiving more DRAW than DRAG callbacks is
only an *opportunity* for fresher input sampling if the rendering
and clipping policy actually permits presentation of the candidate.

Timing observables should include not only OS sample age and DRAW
CPU cost but also the number of candidates tested, the number of
visually accepted samples, and reasons for rejection. That avoids
misidentifying a seemingly enabled but always-vetoed input feature
as evidence that input sampling cannot improve responsiveness.

## Strict budget acceptance requires per-boundary evidence

For native manipulator engineering, establish separate latency budgets
rather than one undifferentiated "fast" number:

1. Pure interaction model and geometry staging (the effect owns these).
2. Synchronous API calls to request host invalidation.
3. Drawbot suite acquisition, path submission and release (host APIs,
   sometimes with expensive text and dynamic object creation).
4. Delay until the next host PF_Event_DRAW callback (host-owned).
5. GPU composition, DWM scheduling and physical screen presentation.
6. Image-render copy or cache identity work, if a separate effect
   instance was used to host the UI.

A release-mode model microbenchmark can show extremely short CPU
execution times, even below a hundredth of a millisecond. However,
a block-average p99 benchmark does not establish a worst-case
per-callback bound under OS preemption. Likewise, a low Drawbot
handler duration does not bound the next DRAW arrival.

Never promote an implementation to a global "0.01ms" performance
claim unless each included stage has explicitly identified
sampling methods, input conditions, percentile definitions,
outliers, and a clear host boundary. A zero-copy rendering
assumption is invalid without a documented host identity contract.

A whole-pane redraw request may be consolidated while an earlier
request is still awaiting dispatch if the application returns the
latest complete geometry in each DRAW. This may reduce redundant
API requests, but it is an **experimental scheduling policy**:
the host may depend on repeated invalidations, and the plugin
must not invent independent DRAW callbacks. State the retry
policy and record stale requests and coalesced attempts.

For Windows investigations, a user-triggered WPR trace using
CPU/GPU/DesktopComposition providers can complement plugin QPC
logs and identify which UI thread or GPU queue was active.
Such a trace requires elevated permissions and may perturb the
workload. It does not by itself measure photons or guarantee
hardware HID-to-display synchronization.

Implementation-specific data and acceptance gates belong in
research/findings/F-UI-009 and F-UI-010, plus the gizmo-input
experiment record; this page defines the general reasoning model.
