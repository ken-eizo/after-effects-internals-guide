---
status: ongoing-experiment
date: 2026-10-12
evidence_grade: E2-L, E2-X, E0-G, H
probe: GizmoSearchAE
host_version: not recorded
---
# Effect Custom UI Input and Redraw — 2026-10-12

## Research question

A Custom Composition UI manipulator is visibly jerky, even though
its short-window DRAW counter exceeded 200Hz. The aim is to remain
inside AE's ordinary Effect Custom UI, not introduce a separate
transparent GPU window over the host viewer.

The screenshot additionally shows AE's native Point Control and
Color Control effects. These provide possible host-native reference
controls, but no controlled same-gesture comparison has been logged.

## First experiments

The earlier plugin showed an internal-verification error concerning
PF_InvalidateRect. Source inspection found this API reachable from
several UI selectors; the sample switched to a conservative
DO_CLICK/DRAG invalidation adapter. The exact offending selector
was not captured. The user subsequently confirmed the sample draws
its eight test modes in AE, but this alone is not a complete regression.

An archived event log (v3) contains 4,945 host callbacks. Offline
segmentation yielded 11 active drag intervals, with DRAG median
gap 15.539ms and p95 gap 37.994ms. Those intervals had many more
DRAW than DRAG events: approximately 110–179Hz DRAW vs 37–61Hz
DRAG when averaged individually. No ADJUST_CURSOR events occurred
within these captured drags, despite 1,841 callbacks elsewhere.

The separate scoped findings are F-UI-001 (different input/draw
event rates) and F-UI-002 (ADJUST_CURSOR absence during capture).

## Next screenshot and second trace

A later screenshot showed DRAW 164.4Hz and CPU 2.107ms;
the new LATEST button was explicitly OFF. A saved v4 log with
932 rows recorded 141 DRAG, 463 DRAW, 249 ADJUST_CURSOR.
Its late_display_used field was zero in all DRAW rows.
This does not test LATEST efficacy, because the option
was not used in that capture.

The raw v3/v4 files are at:
experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v3.csv
experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v4-latest-off.csv

Original large research narratives are archived, byte-for-byte, under:
experiments/ui-gizmo-input/archive/

## Additional SDK candidate and rejected assumption

PF_AppSuite exposes PF_GetMouse in Custom UI coordinates. This looked
like a possible native-only route to newer pointer coordinates during
DRAW. However, a 2014 developer reported an AE internal-verification
failure specifically from PF_GetMouse in DRAW; a 2017 follow-up
reported the same. No unguarded PF_GetMouse(DRAW) call was added.
The API boundary is a separate historical finding F-UI-004.

## Reconsidered architecture and hypotheses

Distinct scheduling stages are OS input, AE event dispatch,
view-local model, UI dirty region, Drawbot DRAW, host UI
composition and actual presentation. Extra DRAW calls can repaint
unchanged coordinates; CPU draw time and host update region may
still cause other latency.

The current Effect probe invalidates the full pane with a NULL
PF_InvalidateRect rectangle. SDK API can request a local region.
A targeted dirty-region experiment should cover both old and new
geometry and all connecting strokes/labels.

## Next experiments (native viewer only)

1. Compare native Point Control and effect custom handle under
   identical AE tool, view zoom and source content.
2. Compare existing update-flag modes independently.
3. Compare FAST ON versus HIDE UI to isolate text overhead.
4. Compare LATEST OFF versus ON, verifying actual view/DPI
   coordinate mapping and official state after mouse-up.
5. The opt-in REDRAW 4 partial-region path is now implemented
   in the sample and passes compile/model tests. Test it with
   POINTS or BEZIER plus HIDE UI and LATEST OFF. Its actual AE
   correctness, clipping and speed gains remain unverified.
6. Consider no-send_drag as a separate disposable hypothesis,
   only after documenting its impact on AE mouse capture and
   host gestures. Do not assume hover events will replace DRAG.
7. Measure changed handle positions and physical presentation
   separately; callback count is not proof of frame rate.

The present work does not establish a universal 60Hz AE limit
or 240Hz display delivery. The normal Effect Custom UI remains
the chosen integration and redraw system.

## Cross-reference

General knowledge belongs in docs/ui-system:
effect-custom-ui-input-routing.md,
effect-custom-ui-invalidation.md,
drawbot-ui-drawing.md,
interactive-ui-latency.md.

Reusable findings remain in research/findings/F-UI-001,
F-UI-002 and F-UI-003. Full logs and reproduction scripts
remain in experiments/ui-gizmo-input.

## Follow-up comparison: redraw modes and intermittent stalls (2026-10-12)

The user reported qualitatively that REDRAW 0, 1, and 3 feel
significantly lighter than REDRAW 4, with 3 closest to the
desired tracking feel, while LATEST ON seems lower-latency than
LATEST OFF. Severe intermittent slowness remains. A screenshot
shows REDRAW 3, LATEST ON, a bright-orange composition,
DRAW 25.0Hz and CPU 1.945ms at that instant.
These are **operator observations**, not controlled mode-3 traces.
The 25.0Hz counter is an instantaneous on-screen reading,
not the physically displayed handle refresh during sustained drag.

### A comparison confound identified in the plugin source

Original REDRAW 4 inherited mode 2's PF_EO_NEVER_UPDATE
despite being described as a comparison of partial vs full pane.
Moreover, until HIDE UI is active (and LATEST OFF, POINTS/BEZIER),
the region calculation deliberately falls back to NULL,
i.e. whole-pane PF_InvalidateRect.

Therefore a slow REDRAW 4 with the HUD shown does **not**
establish that region invalidation itself is slow. It may reflect
mode-2-style composite suppression or host scheduling.
Modes 0, 1 and 3 all omit NEVER_UPDATE; this is a notable
association in subjective reports but is not causal proof.

Corrective code change: make REDRAW 4 share mode 1's event
flags (PF_EO_UPDATE_NOW without NEVER_UPDATE or ALWAYS_UPDATE).
Under eligible HIDE UI conditions it uses an explicit PF_Rect;
otherwise it behaves as mode 1. The geometry is conservatively
swept over old/new nodes plus padding.

### Independent source inspection: hover invalidation

In the prior implementation ADJUST_CURSOR requested the broad
PF_OutFlag_REFRESH_UI when the hit-test changed from any hit
category to another, even if the visual display was identical
(e.g. entering a tab or toolbar button).
The Model had also stored the index of non-node hits in the
node-hover field, causing spurious node highlights.

The corrected model only assigns a hover index for visible
node handles. Global host refresh for hover is requested only
when that actually displayed node-highlight index changes,
plus a separate capped coordinate-inspector case.
This is source-level reduction of redundant host work;
the real host impact is pending repeat measurement.

### What existing traces do and do not say

The archived v3 trace (4,945 rows) and v4 (932 rows)
are both REDRAW 2-only samples. For v3, DRAW callback CPU
p95=1.992ms, p99 approximately 2.665ms, active DRAW gap
p95 about 32.1ms. For v4, CPU p95=2.086ms, p99 about 2.6ms,
and active DRAW gap p95 about 23.1ms (gap cutoff 250ms).
A DRAW handler duration is not the delay before the next
callback or physical monitor scanout. A long inter-callback
gap with a short handler duration can be caused outside
the effect drawing function; these traces cannot identify
which host subsystem waits.

### New instrumented schema v5

The new AEX exports to %TEMP%/GizmoSearchAE-events-v5.csv,
never appending new-schema rows to earlier v4 data.

Additional per-event fields:
- invalidation_kind: 0 none, 1 whole pane, 2 specified PF_Rect,
  3 broad host refresh.
- invalidate_call_ticks: QPC time around redraw suite request.
- event_out_flags / host_out_flags: masks requested by the plugin.
- render_calls / render_cpu_ticks: process-wide monotonic
  count/time for GizmoInputProbe PF_Cmd_RENDER passthrough only;
  NOT total AE compositing/GPU work.

This allows the next controlled trial to distinguish event
dispatch gaps, callback CPU cost, invalidation suite call
cost and sample-effect image render work. The telemetry is
a low-overhead sampled host-boundary probe, not a direct
DWM Present or physical input-to-photon measurement.
The test analyzer covers old v3/v4 and the new v5 schema.

### New falsifiable experiment matrix

- Input/callback cadence: same POINTS drag, same zoom/tool,
  REDRAW 1 full pane vs REDRAW 4 partial pane,
  HIDE UI and LATEST OFF. Compare kind 1 vs kind 2 in v5 CSV.
- Image recomposition: REDRAW 1 vs 3, same drag and image
  complexity, with requested event flags and PF_Cmd_RENDER count.
- Input freshness: REDRAW 1, LATEST OFF vs ON, separate logs.
  Review mouse/handle alignment and last-frame snap.
- Long stalls: log p95/p99 inter-arrival gaps alongside DRAW
  callback time, redraw API cost and render-copy time.
  Compare native Point Control (host control) at similar
  tool, view and project conditions.

The AEX may show a different behavior in a project with
expensive upstream effects, so the selected layer/material
must be controlled. None of the above has yet been validated
by installing the newly changed AEX into AE; do not present
the code-level guard as achieved perceptual smoothness.

## All-five-mode host trace, callback-stall analysis, and revised baseline

The user's latest v5 AE session has been preserved without editing:
experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v5-all-modes.csv
SHA256:
a2ffd279df34c57508da2bc8b9e89388c87fec39b745daf23221a36468b931e1
The CSV contains 17,275 timestamped callbacks, distributed as
mode 0=1,162, mode 1=5,704, mode 2=1,766, mode 3=7,348,
and mode 4=1,295.

The user reports mode 0/1/3 approximately equivalent and light, mode 4
now light, and mode 2 persistently heavy. Latest ON/OFF is hard to
distinguish by feel; occasional large stutters and residual pointer
latency are the main problems.

Separate event parser:
D:/Developer/GizmoSearchAE/tests/analyze_v5_gestures.py.

v5 DRAW p95 CPU by mode (in ms): 0=4.363, 1=3.818,
2=2.675, 3=4.424, 4=2.740. DRAW active-gap p95
(capped to gaps below 250ms) was 0=13.931ms, 1=14.561ms,
2=25.876ms, 3=16.886ms and 4=15.708ms.
These samples are NOT matched in gesture duration, AE composition
render workload, device path, zoom, panel placement, or HUD state.
Do not interpret them as a strict numerical ranking.

The 37 segmented drag intervals include a mode-3 gesture of
approximately 1.5 seconds with a maximum observed inter-DRAW gap of
about 193ms, while the maximum Drawbot plugin callback CPU cost in
the same gesture was about 7.84ms. The difference can arise from host
scheduling, image evaluation, OS scheduling or a momentary pause
in input; this is not proof of a 193ms host stall.
The plugin handler CPU cost alone cannot account for the entire
elapsed gap. A controlled input source and actual Present timeline
would be needed to decide if there was an unintended visible freeze.

An actual 2,135 DRAW callbacks used LATEST preview.
The estimated OS-pointer displacement ahead of last official AE
DRAG has p50=12.530px and p95=44.820px, assuming unchanged
1:1 physical pixel mapping from the original down event.
This is evidence that the sampler used different/newer coordinates
during some DRAW callbacks, not proof of lower input-to-photon time.
Comparing CPU medians for mode 1 gives approximately 1.500ms on
late-preview DRAWs versus 1.464ms on no-preview DRAWs, with serious
selection/interaction-state confounding.

### Changes prepared as another native Drawbot/Effect lab build

- Default REDRAW 1, not REDRAW 2 (PF_EO_NEVER_UPDATE).
- Default LATEST ON, disabled by user when OS/view mapping is
  inaccurate or in order to compare.
- Windows cursor sampling now happens after acquiring host
  Drawbot references/surface instead of beforehand, reducing
  pointer sample age before command emission.
- Opt-in partial-region mode 4 continues to compare against mode 1.
- Existing guard avoids broad refresh for hover hits that do not
  visually alter node geometry.

The new CSV format v6 adds four internal drawing phase durations:
Drawbot suite/surface acquisition, late-pointer sample, scene
geometry/text processing and release/destruction. It also records
latest-enabled/HUD/FAST/dragging state and both host-confirmed
and actually drawn handle positions. Its analyzer can count distinct
positions that the plugin submitted to Drawbot, but cannot prove
that the compositor physically displayed each one.

AEX compile and model tests have passed. An AE interactive trial
with v6 is PENDING. Do not claim 240Hz or zero-latency.

The next measurement compares v6 LATEST ON/OFF with identical
REDRAW 1/HUD ON gestures; then repeats with HIDE UI to expose
Drawbot text overhead. It should include the native AE Point
Control reference and record the AE product/build. The current
trace supplies no actual physical present timestamps.

## Further user observation: lazy redraw feels better, and v6 HUD cost

The user reports the native redraw policy 0 subjectively feels
smoother than mode 1, with somewhat fewer intermittent stalls.
There remains occasional jerkiness and the handle still does not
track the OS cursor at perceived zero latency. The user asked to
continue maximizing native Custom UI performance rather than
using an externally presented graphics window.

The v6 CSV has been archived intact under
experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v6-hud-comparison.csv
SHA256 14c9971ed841a5d4ed1e9806e1a47cc5de784b1f32ce5d3099585db7105c18ee.
It contains 18,229 events, including 8,634 DRAW callbacks. In the
REDRAW 0 / LATEST ON drag subset:

- With HUD showing (3,488 DRAWs): plugin DRAW CPU median 1.712ms,
  p95 5.058ms, p99 7.416ms.
- HUD hidden (262 DRAWs): plugin DRAW CPU median 0.134ms,
  p95 0.281ms, p99 0.408ms.
- Median Drawbot scene time fell from 1.667ms to 0.102ms.
- Median text command count fell from 18 to 0.
- Drawbot reference/suite acquisition stayed near 0.01ms.

These were naturalistic sessions, NOT a matched controlled sweep,
and HUD also changes rectangles and string preparation. The
specific scoped observation is Finding F-UI-007, not an alleged
universal Adobe performance fact.

### New native experiment: REDRAW 5

The probe now defaults to REDRAW 0 / LATEST ON.
REDRAW 5 was added as a controlled experiment:
the same host update flags as 0 (lazy, no UPDATE_NOW), but a
conservative region around before/after node geometry.
Unlike REDRAW 4, this experiment can work while HUD and
LATEST are enabled, with two safety mechanisms:

- An AE-provided DRAW update_rect is checked before omitting
  static HUD draw commands. If the actual area intersects
  the HUD or clip info is absent, draw the HUD normally.
- A late OS pointer-sampled display snapshot is rejected
  if the visual geometry would leave the AE update_rect.
  This never commits speculative coordinates to source
  effect/project parameters.

A final drag/release, control-mode change, altered toolbar setting
or other incompatible state falls back to whole-pane redraw.
The no-UPDATE_NOW policy is unchanged, so it cannot guarantee an
autonomous callback or 240Hz actual physical presentation.

### Verification needed

1. Install rebuilt AEX; compare mode 0 and 5 under same HUD ON,
   FAST ON, LATEST ON, POINTS, comp zoom and monitor Hz.
2. Inspect host DRAW update_rect and per-frame text command count.
   With mode 5, expect a nonzero fraction of draw_texts=0
   when the actual affected region excludes the HUD.
3. Confirm static HUD remains visually intact and all old node
   geometry is erased. Check snapping, high velocity, release,
   drag with nodes near HUD, zoom, scaling, resizing.
4. Capture callback p50/p95/p99 and actual pointer tracking;
   distinguish measurable plugin CPU improvement from render
   scheduling/physical presentation.
5. If partial drawing misbehaves on a particular AE build,
   use REDRAW 0 while investigating the contract boundary.

GizmoSearchAE/test analyzers and source modifications have local
build/unit-test verification only. No user in-host result exists yet
for the newly introduced mode 5. Comparing HUD visible and hidden
is useful, but a successful synthetic geometry test is not proof
of the installed host compositor retaining static chrome.

## Host SDK provenance and latency sampling phase (2026-10-12)

User identified the canonical Adobe After Effects SDK 25.6 package at
E:\ae25.6_61.64bit.AfterEffectsSDK\Examples, with the public headers
under Examples\Headers and suite helper in Examples\Util.
The earlier GizmoSearchAE CMake cache/default had pointed at
D:\Developer\AE-FFT-Plugin; its Headers directory was observed empty.
An intermediate build from TweeqTransformAE's copied headers was only
a stopgap and is no longer the canonical setup. CMake and the
validator now consistently target the SDK 25.6 Examples root.
The plugin, core tests and external-consumer compile passed against
these SDK 25.6 headers. This does NOT establish in-host 25.6 AE
runtime behavior; that needs a user install and capture.

Because mode 5 is confirmed by the user as smooth and stable,
an independent mode 6 was introduced to isolate pointer sampling
phase. Both modes have identical AE lazy invalidation and region
policy. Mode 5 samples current OS mouse position after acquiring
host Drawbot; mode 6 waits until immediately before submitting
moving-geometry Drawbot commands, after submitting static HUD
commands. Both operate solely in PF_Event_DRAW and transient
presentation state. They do not claim a new callback source,
present rate, or perfect input-to-photon latency.

New CSV files are schema v7 to keep prior v6 evidence unchanged.
The v7 parser can compare sample-to-DRAW-end timestamps for modes
5 and 6, but visual presentation remains unmeasured until actual
host execution. Mode 6 has passed C++ build/model and parser
tests; an installed-AE experiment remains pending.

## Root cause discovery: LATEST was fully vetoed in REDRAW 5 (2026-10-12)

New scrutiny of the existing real AE v6 log (now preserved as
experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v6-host-clip-sentinels.csv,
SHA256 50d0001c21e500254b0a0fedb74e2cfeba1fa5a0bcb73ca655482f7b165af43a)
found **31,015** callbacks, including 13,993 PF_Event_DRAW.
Every recorded DRAW update_rect failed the sample's positive-area
rectangle test. The prevalent values were (-1,-5,-1,-15) in
left,top,right,bottom order.

Among 4,438 REDRAW 5 drawing calls while drag capture was active,
latest_enabled was set in all but late_display_used was set in
**zero**. By comparison, REDRAW 0 used an OS late preview in 3,419
of its 3,968 active-drag DRAWs. This is a stronger, independently
reproducible explanation for residual pointer lag than merely
assuming the cursor was sampled too early.

The previous code guarded speculative previews against the
host-reported update_rect even when it was invalid/sentinel,
in effect turning LATEST OFF during every mode-5 DRAW. This is a
source-level logic error. The available data cannot establish
whether the host rectangle is a legitimate sentinel, version
difference, or sample interpretation mismatch. This finite trace
also shows that PF_Event_IDLE cannot be relied upon during captured
DRAG in this host session: 22 mode-5 gesture segments contained
zero IDLE callbacks and about three DRAW callbacks per DRAG.

### Corrective experiment (v8, no host independent window)

- Retain host-owned AE Effect Custom UI / Drawbot, mode 5 and 6.
- On DRAG, record the effect-requested dirty region and enlarge it
  to cover an extra transient OS pointer estimate with 48px fringe.
- On DRAW, a usable host update rectangle remains a required
  containment constraint; a nonpositive host rectangle no longer
  automatically rejects the candidate. Validate against the
  effect-requested region instead.
- Candidate outside requested coverage is still rejected; no
  project mutation or new rendering thread is introduced.
- New v8 CSV tracks late_candidate, late_region_reject,
  request_valid, host_clip_valid and requested region bounds.

The exact client-visible improvement depends on the AE compositor's
effective clipping and scheduling; this cannot be determined from
the callback evidence. The compiled AEX and pure-model tests
have passed, but in-host visual correctness and input-to-photon
latency remain unverified. See independent Finding F-UI-008.

A Japanese implementation/experiment guide lives at
D:/Developer/GizmoSearchAE/LATENCY_ROOT_FIX_JA.md.

## User feedback: after late-region expansion, tracking improved but smoothness regressed

The user reports an improved attachment between the cursor and mode-6
handle, but sporadic single-frame stutters and reduced smoothness in
modes 5 and 6. This is an operator observation (E2-X), not controlled
quantitative evidence; there is NO exported v8 event CSV on the user's
machine as of the investigation.

The latest recorded test file is the earlier v7 CSV (12,708 events).
That trace documents:
- REDRAW 5 + HUD + LATEST: DRAW CPU p50 about 1.42ms;
  DRAW interval p99 about 24.7ms; late preview applied in 0/2061
  sampled dragging DRAW callbacks.
- REDRAW 6 + HUD + LATEST: DRAW CPU p50 about 1.63ms;
  DRAW interval p99 about 22.0ms; OS sample-to-callback-end
  median about 0.092ms, yet preview applied in 0/1345
  sampled dragging DRAW callbacks.
- REDRAW 5 + HIDE UI: DRAW CPU p50 about 0.129ms,
  DRAW gap p99 about 25.3ms.
- In these samples, a late OS cursor read by itself did not
  increase the number of accepted speculative visual frames,
  because the clipping guard rejected them all before v8.
- The v7 trace cannot directly explain the user's experience
  with the later v8 build. Do not claim its measured intervals
  are v8 outcomes.

The last v8 implementation uses two extra operations during each
DRAG when partially invalidating:
(1) OS pointer sampling and transient pose construction and
(2) an enlarged PF_InvalidateRect region for the prospective
motion. Either can add work; neither has a measured causal
connection to the reported stutter without a new v8 trace.
An alternative hypothesis is the host's inherent asynchronous
DRAW and compositor scheduling, which is independent of model CPU
and pointer sampling age.

### New controlled experiment: mode 7 — lazy / full / lean

The next host-native AEX retains the proven model-only
DRAG handling and the AE Custom UI/Drawbot path. It adds
an opt-in REDRAW 7:
- Same lazy invalidation flags as 0/5/6, without UPDATE_NOW.
- Requests full-pane PF_InvalidateRect rather than constructing
  and enlarging an expensive / potentially unstable partial area.
- Drawbot input sample acquired at the moving geometry stage
  (mode-6 phase), rather than before static HUD work.
- During captured DRAG, deliberately does not draw the experimental
  diagnostic HUD; focuses DRAW work on moving handles and paths.
  When DRAG ends, forces redraw to restore the HUD.
- Does not depend on an empty/invalid update_rect to authorize
  suppression of a panel that was supposed to be retained.
- No alternative window, swapchain, overlay surface or global
  input hook. No thread-based GPU rendering.
- REDRAW 5 remains the context default and working comparison
  reference; 6 remains available.

The new mode separates two suspected stutter sources:
(1) region-enlargement/rejection and (2) diagnostic HUD Drawbot
work. Its advantage has not yet been measured in live AE,
and intentionally hiding the HUD during a drag is an
experiment-specific interaction compromise, not a final
consumer UI decision.

Additional analysis tool:
D:/Developer/GizmoSearchAE/tests/analyze_native_smoothness.py
It reports host DRAW and DRAG interval tails, DRAG-to-next-DRAW
latency, Drawbot CPU, preview-use, and visible handle coordinates
per submitted callback. No physical screen Present/HID timestamps
are included.

Cross-reference separate finding F-UI-007 (measured HUD costs),
F-UI-008 (host update_rect sentinel and preview veto).

## Deep whole-pipeline performance work (2026-10-12)

The user explicitly required aggressive performance targeting:
0.01ms-class per-stage execution, rejecting callback path p99 above
0.1ms, while significantly lowering hardware requirements.
This is treated as an acceptance test, NOT a claim that AE guarantees
such timing through every host/OS/GPU boundary.

New standalone Release tests on the user's Windows 10 machine:
- GizmoPipelineBench: 7 independent core C++ paths, each measured
  in 6,000 blocks of 64 calls. All seven had p99 of block-average
  cost below 10 microseconds. Sampled maxima were not universally
  below that bound; it is not a hard real-time guarantee.
- GizmoCopyBench: CPU RGBA8 memcpy p50 was 170us at 720p,
  342us at 1080p and 2793us at UHD4K. These are independent
  CPU memory transfers, not AE rendering measurements.
- v8 actual-host 38,805-event trace: mode 7/HUD-visible/LATEST
  DRAW CPU p99 about 2.618ms, Drawbot scene p99 about 2.261ms,
  active DRAW gap p99 about 57.249ms. A strict 100us stage p99
  gate rejected 47 measured stage-by-mode/HUD/LATEST groups.
- The user's installed stable AE exe was confirmed as version
  25.6.4, matching the user-supplied public SDK 25.6 roots.
  A separate community report of a 26.5 DRAG custom-UI callback
  regression is not proof of this machine's current issue.

Refactoring:
GizmoFrameScheduler.hpp is an independent C++ generation-based
redraw queue. An opt-in REDRAW 8 keeps AE native lazy full-pane
Drawbot and geometry-stage latest pointer acquisition, but
suppresses repeated Invalidate calls while a previous one is
pending, with a 24ms opportunistic reissue via the next DRAG.
This mode may improve or worsen real AE responsiveness, and is
not the default. All other modes are preserved; REDRAW 5 remains
default until a real host comparison passes the budget.

Version 9 CSV adds coalesced/stale invalidation and generation
telemetry. Older v8 evidence remains immutable. Synthetic tests
verify parsing and that the explicit performance gate rejects
above-budget paths. A new optional elevated WPR capture protocol
was written to capture CPU/GPU/DWM ETL on user demand, but WPR
has NOT been run, and physical input-to-photon remains unmeasured.

Separate findings:
F-UI-009 (pure core vs DRAW dispatch/presentation boundaries)
F-UI-010 (sample effect pixel transfer vs zero-copy identity)

## Drawbot internal stage profiler (research build, 2026-10-12)

A separate low-rate detailed Drawbot profiler has been added to
the native custom UI adapter rather than extending the already
large main event-log struct. Only 1 in 16 DRAW callbacks is sampled.
A fixed-size 1024-entry Context-owned profile buffer is used; it
has no dynamic allocations on the sampled hot path. A separate
CSV is emitted only on EXPORT or context-close, never from DRAG/DRAW.

GizmoSearchAE-drawbot-profiler-v1.csv records:
- Drawbot path creation/build/complete path CPU time;
- path geometry command preparation CPU;
- FillPath/StrokePath CPU;
- total text preparation + DrawString CPU;
- DrawString-only synchronous CPU;
- font setup time on the first DrawString;
- PaintRect synchronous CPU;
- NewBrush/NewPen resource allocation CPU.

These measures overlap (e.g. all_text contains DrawString and
font initialization); they must NOT be summed as independent stages.
QPC sampling itself has cost and the subset may miss rare
long-tail events. It is host API *submission* time, not GPU
execution or monitor Present.

New analysis tool:
D:/Developer/GizmoSearchAE/tests/analyze_drawbot_profile.py
with --strict --budget-us 100 --target-us 10 for sampled stage gates.
Synthetic parser/strict-gate regression tests have passed.
Host in-app observations of this profiler are PENDING.

The main mode-8 generation coalescer remains research-only,
non-default; no evidence yet that it reduces actual host-DRAW
tail gaps. The user-requested 0.01ms whole-system bound is NOT
satisfied in the v8 host data; 47 callback-stage p99 violations
remain as an explicit rejection state.

## REDRAW 8 source audit, failure recovery and demand-gated log analysis (2026-10-12)

The next agent resumed from the existing working tree without resetting
GizmoSearchAE, AEIG or preserved v3-v8 recordings. The native AEX and
the complete SDK 25.6 validation suite were built on DESKTOP-OAL1L2V.
The v9 host log still did not exist; no result for mode 8 in AE is claimed.

### Two source-level mode-8 correctness hazards

1. PF_AppSuite6::PF_InvalidateRect returns PF_Err. The former adapter
   ignored it. The independent scheduler marked its request pending
   before an unconfirmed host API call; a rejected call could incorrectly
   suppress new invalidations until stale retry or the next DRAW.
   GizmoAEHostRedraw now reports whether the SDK accepted the call.
   On failure the Context cancels the pending state and logs
   invalidation_kind=4. This is an attempted request, not a painted frame.
   Existing v9 CSV field ordering was retained.
2. Mode 8 hides diagnostic chrome while dragging but did not force
   a redraw at the final zero-delta DRAG. Mode 7 already did.
   Both modes now use a common pure policy for restoring the chrome.
   Deactivation and mouse exit also clear pending requests even
   without a changed hover or transform.

Separate model tests cover the failed-request retry path, a DRAW
declined due to invalid surface, and a terminal zero-delta DRAG.
The source build and offline tests are NOT substitutes for verifying
lifecycle events in the live AE Composition viewer.

### The inter-DRAW pause is not one unqualified number

A new analyzer, `tests/analyze_demand_gaps.py`, uses the immutable
38,805-event v8 host log and partitions consecutive DRAW intervals
depending on whether an AE DRAG callback occurred between them.
The exact evidence and numeric table are in
`research/findings/F-UI-011-draw-gap-demand-classification.md`.

Mode 7 / HUD ON / LATEST ON:
- With intermediate DRAG: 392 DRAW intervals, p99 26.429ms.
- Without recorded DRAG: 790 intervals, p99 59.688ms.
- Last DRAG to next DRAW in the first class: p99 14.932ms.

Mode 5 / HUD OFF / LATEST ON shows the opposite association:
- With intermediate DRAG: 378 intervals, p99 61.244ms.
- Without recorded DRAG: 761 intervals, p99 14.320ms.

Therefore the original unconditional p99 cannot by itself attribute
pauses to AE's redraw scheduler, model cost or user input inactivity.
Recorded DRAG absence is NOT hardware input absence. Comparisons
between modes are observational and were not gesture-matched.

Do not use the result to select mode 8 as default. A same-gesture
mode-7 versus mode-8 test, a sampled Drawbot sidecar, and optionally
a deliberately user-initiated CPU/GPU/DWM trace are still required.
The physical input-to-photon path remains unmeasured.

## Native mode-8 low-latency follow-up and mode-9 A/B probe (2026-10-12)

User's new in-host feedback: REDRAW 8 felt the smoothest/stablest among
0-8, while visible cursor tracking still lags. This subjective outcome
has been retained as the baseline; mode 8's existing rendering,
coalescing, late sampling and lazy invalidation are not replaced.

New v9 host evidence has been archived unchanged:
- experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v9-initial-mode8-comparison-91c9cbb1.csv
- experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v9-drawbot-profile-d810907a.csv

The former contains 14,941 events and the latter 408 sampled Drawbot
records. In the mode-8 active-drag/HUD/LATEST subset (2,581 draws):
- Drawbot acquisition p50/p99: 7.2 / 27.5 us;
- OS newest mouse sample stage: 3.4 / 97.96 us;
- scene commands: 67.4 / 272.78 us;
- suite/resource release: 7.2 / 27.24 us;
- complete DRAW callback: 82.7 / 309.06 us.

In the related but not identical mode-8 broader active-drag subset,
DRAG-to-next-DRAW p50/p99 was 2.578/8.664ms.
The coalescer analyzer observed 1 suppressed redundant invalidate
out of 987 mode-8 click/drag callbacks for the measured conditions.
That alone does not establish a causal explanation for stable motion.

The sidecar's 163 mode-8 active-drag/LATEST-on samples show total
Drawbot path work p50/p99 62.5/162.23us; path-geometry
p50 11.8us and stroke/fill p50 43us. These subfields overlap.
No 10us p99 guarantee is possible on this observed host path.

A strict controlled opt-in policy experiment, REDRAW 9, has been
implemented: *identical to 8 except PF_EO_UPDATE_NOW on a successfully
submitted invalidation*. The official SDK documents this as a request
for immediate redraw after event return. Tests cover policy isolation,
drag chrome restoration and round-robin switching. In-AE effectiveness
and smoothness remain **unmeasured**. Mode 8 must stay available
unchanged and should remain the subjective reference.

A separate host-independent GizmoPixelTransfer.hpp reduces the
identity effect's pixel copy call count for equal row-pitch worlds:
1 memmove for a contiguous region instead of N per-row calls; an
in-place alias is an explicit no-copy case. Unequal row stride uses
the existing row-wise transfer behavior. Independent C++ tests verify
padding, overlap, in-place, truncation by height and invalid dimensions.
This can reduce the sample effect's CPU demand but cannot remove
required AE image processing nor change the Drawbot host dispatch contract.

Measured source: F-UI-012-drawbot-cpu-vs-drag-to-draw.md.
New experiment protocol: GizmoSearchAE/MODE8_MODE9_LATENCY_TRIAL_JA.md.
Physical input-to-photon, GPU Present timing and calibrated multi-display
pointer mapping are still missing.
