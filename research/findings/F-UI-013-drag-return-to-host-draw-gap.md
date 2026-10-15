---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L, E0-H, E0-G
scope: Native After Effects effect custom UI, recorded v9 event samples
confidence: high for callback QPC arithmetic, unknown for delay ownership
---
# F-UI-013 - Drag handler completion precedes the next host DRAW by milliseconds

## Result

In archived GizmoSearchAE v9 host observations, the effect has returned
from PF_Event_DRAG **milliseconds** before its next observed PF_Event_DRAW.
Therefore cutting the plugin's pure drag-model calculation to 10us
does not bound the callback delivery interval, let alone the physical
input-to-photon latency.

This does NOT prove that the entirety of this time is AE's internal
message queue waiting: intervening host work, Windows scheduling,
other UI callbacks or idle time may contribute.

## Immutable evidence

`experiments/ui-gizmo-input/runs/2026-10-12-user-ae-v9-initial-mode8-comparison-91c9cbb1.csv`

SHA256 `91c9cbb1c178e0ebe0281e71fcb5209bedc932ba6d9f31e8f4e93ef258c8922b`.

14,941 total callbacks; recorded QPC frequency 10,000,000Hz.
The original trace does NOT contain an independently proven Adobe
product/build number; do not assume the current 26.3 executable
generated this earlier capture.

Reproduction:
`python D:/Developer/GizmoSearchAE/tests/analyze_post_drag_return.py <csv>`

On matching mode=8, HUD=on, LATEST=on drag records (862 matched
DRAG-to-next-DRAW transitions, excluding >250ms and incompatible states):

| Interval | Median | p99 |
| --- | ---: | ---: |
| PF_Event_DRAG handler execution | 0.261ms | 1.608ms |
| after DRAG return -> next DRAW entry | 2.164ms | 7.245ms |
| DRAG entry -> next DRAW entry | 2.526ms | 8.193ms |

The comparison is *within one logged mode subset*. The conditional
matching and selected group are not the same population as the
general v9 smoothness analyzer, so percentile values should not be
mixed without recording the selection conditions.

## Host-version and scheduling boundary

Read-only inspection on 2026-10-12 discovered that the currently
running `D:/Adobe/Adobe After Effects 2026/Support Files/AfterFX.exe`
reports FileVersion 26.3. Earlier experimental records identify
25.6.4; the AE application was restarted after those recordings.
Hence any causal comparison must record AE version at capture time.

Adobe's public Effect Custom UI API allows drawing only inside
PF_Event_DRAW on a host-owned Drawbot surface. PF_InvalidateRect
and PF_EO_UPDATE_NOW request host-controlled repaint but do not expose
a callback deadline, a frame-presentation fence or direct control of
the Composition panel's internal scheduler.

A developer-reported AE 26.5 regression of custom UI DRAW delivery
under captured drag was acknowledged by Adobe, with a fix reported
in beta 27.1.0.7 (October 2026). This does not prove a 26.3
regression or explain the current user's experience.

## Next discriminating evidence

1. During click/drag, record the raw SDK `PF_DoClickEventInfo.when`,
   which is `A_u_long`. The SDK header does NOT specify a reliable
   cross-platform conversion to QPC or GetTickCount64. Verify clock
   domains before subtracting and claiming an input-queue delay.
2. Capture host thread scheduling and GPU/DWM with an explicitly
   initiated WPR profile. Identify the UI thread by callstack and
   compare WAIT/READY/RUN intervals against QPC callback markers.
   Do not infer a photon timestamp from a CPU or GPU event alone.
3. Compare the same plugin on AE 25.6.4 and 26.3 with exact
   zoom/viewer/image workload and pointer exercise, and benchmark
   built-in Point Control against Effect Custom UI.
4. Distinguish host DRAW scheduling from Drawbot command submission,
   DWM desktop composition and actual displayed pixels.
5. Avoid changing a proprietary AE binary/patching active host code
   absent confirmed ownership, ABI contracts, crash isolation and
   reversible validation. Such an experiment cannot be the default
   reusable plugin.

The 10us budget is an aggressive target for self-owned CPU work,
not an achievable blanket guarantee over asynchronous host dispatch
and physical monitor scanout.

Related: F-UI-006, F-UI-009, F-UI-011, F-UI-012.
