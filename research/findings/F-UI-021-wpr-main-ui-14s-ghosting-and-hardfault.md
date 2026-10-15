---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L
scope: AE 26.3 main-window UI thread, approved WPR CPU/GPU/DWM ETW
confidence: high for ETW event contents, low for causal link to routine Gizmo stutter
---
# F-UI-021 — A 14-second AE UI message delay with 43ms UI-thread page fault was observed in WPR

The user authorized elevated WPR tracing on 2026-10-12.
A 12-second memory-mode CPU/GPU.light/DesktopComposition.light trace
was captured, merged successfully, and archived as an ETL in
`D:/Developer/GizmoSearchAE/scratch/etw/`.

Immutable trace:
`GizmoAE-Approved-20261012-184548.etl`
1,408,237,568 bytes, SHA256
`E5FCCF0FBF4ABE56B3F68E4E7DFD634D8DCCDFA825190BFBB3F7D5244B541446`.

xperf tracestats: trace 43.816 seconds (capture/control and merge
period included); **zero lost buffers and zero lost events**.
User consent did not authorize modifying AE binaries or settings;
none were changed.

By `GetWindowThreadProcessId`, AfterFX.exe process ID 90148 owns
the main window through UI thread TID 72940. ETW `uidelay` reported
two views of what appears to be the same long-latency episode:
- MsgCheck Delay **13,937 ms** with `HasGhosted`.
- Input Delay **14,000 ms**.

Do not sum these as two distinct freezes. This is a Windows-observed
message-pump responsiveness problem, NOT a 14-second measurement of
Gizmo input-to-photon lag or evidence that a particular plugin caused it.

ETW `cswitch` totals over the broader trace:
- UI TID 72940: 575,722us CPU execution;
- entire AE PID: 870,153us CPU execution.
The substantial gap between message delay and running CPU time
is consistent with blocked/idle/unscheduled time but does NOT identify
which waiting mechanism dominates. WPA precise wait-state stack
analysis is still required.

A finer `xperf -a dumper` slice near 13.036s captured
on the same AE main thread:
- DiskRead on `D:/Adobe/Adobe After Effects 2026/Support Files/TDB.dll`,
  recorded duration 43,039us;
- matching HardFault around 13.036241s, recorded elapsed 43,115us;
- kernel stack included Ntfs.sys and FLTMGR.SYS;
- afterwards CSwitch recorded old AE UI TID72940 in the
  `Waiting` state with `Executive` wait reason.

An AE-wide hardfault summary recorded **515 page faults**, totalling
**6,477,312 bytes**, mostly DLL/plugin/driver code and metadata.
This is not evidence of insufficient physical RAM by itself.
AE disk cache traffic included 257 writes totalling 8,323,072 bytes.

Other processes (Chrome, DWM, Taskmgr, Defender, multiple CompNode
test executables) executed during the trace. Their coexistence
demonstrates parallel workload; their effect on AE is unproven
without controlled A/B under identical input and more detailed
thread scheduling/GPU present correlation.

Useful extracted data:
`D:/Developer/GizmoSearchAE/scratch/etw/analysis-20261012/`
- ui_delay.txt, thread_cpu.txt, hardfault.txt, diskio-summary.txt,
  ae-wpr-summary.json.
Reproducer: `D:/Developer/GizmoSearchAE/tests/summarize_ae_wpr.py`.
Full Japanese audit:
`D:/Developer/GizmoSearchAE/WPR_AE_LOAD_STUTTER_20261012_JA.md`.

This is evidence that AE host UI long-tail responsiveness can dominate
a lightweight custom Gizmo's local compute. The exact underlying
14-second stall cause and any normal 240Hz frame drop rate are still
unmeasured. Do not infer physical Present cadence from event callbacks.

## Storage-risk observation after capture

Read-only PSDrive query showed D: at 2.75GiB free out of
2,794.52GiB (about 0.1%). AE's binaries and Disk Cache are on D:.
The WPR trace itself uses about 1.31GiB, but other reductions in D:
free space between capture preparation and post-analysis were not
attributed. Storage pressure is a plausible separate risk to AE
disk caching; it is not a demonstrated cause of the 14s UI delay.
Do not delete/cache-clean or relocate without explicit user approval.
