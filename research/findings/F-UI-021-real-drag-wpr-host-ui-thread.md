---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L
scope: User-triggered WPR CPU/GPU/DWM during AE Gizmo lean active drag, mixed with window movement
---
# F-UI-021 — AE main UI thread consumes significant CPU during real Gizmo operation

## Evidence
User explicitly operated native Gizmo during an elevated WPR recording, but also
moved the application window; the latter is a confounder for long UI stalls.

Source (immutable original):
E:/GizmoSearchAE-WPR/GizmoAE-Approved-20261012-190253.etl
Size: 1,502,609,408 bytes
SHA256: 33B6B0A40FD6B92646C38D17F312417BCAB7EA1A1DCE13F5F934AD7974FD9969

Captured with WPR built-in profiles CPU, GPU.light, DesktopComposition.light.
xperf reports lost buffers=0, lost events=0, overall ETL coverage 36.887s
(includes trace stopping / ETW rundown, not 36.887s of user dragging).

AE 26.3 process PID 60848, main UI thread TID 92276, identified using
GetWindowThreadProcessId and matched to CSwitch event records.

The installed and AE-loaded native effect was the Lean edition:
C:/Program Files/Adobe/Common/Plug-ins/7.0/MediaCore/GizmoInputProbeLean.aex.
SHA256 51E04E35A5F3CE235991F3B95A98D1F3E917BE679CF136895D81E7D9D768B5DD,
equal to project Release build.

## UI-thread CPU execution (xperf -a cswitch -process -thread)
| Trace interval | CPU execution | fraction of one UI thread's wall time |
| 0-9s | 4,738,252us | 52.6% |
| 9-12s | 2,061,786us | 68.7% |
| 12-15s | 934,793us | 31.2% |

AE process cumulative CPU (across threads): 14,353,663us.
Do not equate process CPU with one core or add module attribution
samples: these may be inclusive.

Windows UI responsiveness:
- MsgCheck delay ~2312ms and InputDelay ~2343ms
- Second message/input pair ~938ms
These may include manual window movement and are NOT causally assigned to
Gizmo redraw or baseline drag stutter.

Additional AE process CPU sampling in 9-12s included module labels
NewTek_NDI_Transmit.prm, PF.dll, ImageRenderer.dll and nvwgf2umx.dll.
This confirms their participation in the process-wide sampled workload,
NOT that any particular module caused the long delay, or that those
modules' samples are exclusive, or that they executed on the UI thread.

Physical memory was plentiful (~38GB free of ~80GB total) at inspection.
AE hard page faults in the entire ETL: 86 / 887,808 bytes;
simple global RAM exhaustion is not a supported conclusion.
GPU and DWM event providers are captured, but per-gizmo DRAW->Present
relationships remain unproven because the Lean edition has no
per-callback event markers and the window move confounds the trace.

## Implications
- More local geometry micro-optimization alone cannot guarantee
  240Hz AE delivery when the host main UI thread consumes substantial
  CPU and sporadically stops processing UI messages.
- A controlled "no window movement" trace is needed before assigning
  either ~2.3s or ~0.94s stalls to regular native Gizmo dragging.
- Compare with other plugins/extensions disabled in a test environment
  (especially workload-heavy MediaCore integrations) without modifying
  the real user project or asserting unproven guilt.
- Introduce very sparse opt-in ETW marker instrumentation if genuinely
  needed to correlate the lean Effect Custom UI callbacks with
  host/GPU/DWM presentation. Markers must not alter normal fast path.
- Do not mistake a DXGI/DxgKrnl Present record for physical photon timing.

Detailed Japanese record:
GizmoSearchAE/WPR_GIZMO_ACTIVE_20261012_JA.md

Support evidence files on E:
analysis-190253/trace-stats.txt
analysis-190253/thread-cpu.txt
analysis-190253/threadcpu-09-12.txt
analysis-190253/ui-delay.txt
analysis-190253/cpu-modules-09-12.txt
analysis-190253/hardfaults.txt
