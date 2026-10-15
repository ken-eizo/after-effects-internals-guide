---
status: observed-scoped
last_verified: 2026-10-12
evidence_grade: E2-L / E0-H / E0-G
scope: GizmoSearchAE Custom UI clock field
---
# F-UI-016: Custom UI click/drag when advances ~60 units/second

The AE SDK declares PF_DoClickEventInfo.when as A_u_long.
Adobe describes it as OS-level click time but does not define
the exact unit or direct correlation to Windows QPC.

Observed 313 REDRAW-9 records yielded a regression slope of
59.99815 raw units per QPC second and 59.99970 raw units per
Windows GetTickCount64 second; an increment is consistent with
about 16.67ms on a uniform counter. The median absolute regression
residual is ~0.276 raw units.

This prevents microsecond input latency measurement from this
field alone. It does NOT prove AE dispatch runs at 60fps or
identify the originating physical HID event.

Source snapshot in GizmoSearchAE scratch/end-to-end-audit-20261012:
host-dispatch-v1-snapshot.csv
SHA256 07D568EE575FB4C48DF8EEF82E68E8D0081ABDE20EE95FB514A560316FE1DF09.

Reproduce:
python tests/analyze_ae_when_clock.py <host-dispatch-snapshot.csv>

True input-to-photon latency requires distinct hardware input timing,
AE delivery QPC, UI-thread ETW trace and GPU/DWM presentation,
plus ideally actual display response measurement.
