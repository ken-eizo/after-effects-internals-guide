---
status: pass-compiled-not-host-tested
last_verified: 2026-10-12
evidence: E2-B
---

# EXP-SHAPE-032 — Fail-closed public-AEGP project state gate in both probe AEX binaries

## Objective

Prevent the previous dangerous scenario in which a project had no selected layer but contained unsaved or production work. Provide a separate READ ONLY confirmation before even considering native TDB mutation.

## Implementation

Both source labs include the same original host_abi_shared/NativeProjectSafety.h, using public AEGP ProjSuite6, ItemSuite9 and RQItemSuite3. The probe requires exactly one project, non-dirty, valid root folder, no active non-root item, no non-root items in project enumeration, zero Render Queue items and all SDK calls succeed. Unknown state rejects the gate.

The safe CNLNativeVectorHostProbe AEX v2 writes the disposable_project_gate_pass flag and detailed reason plus project/Render Queue counts in the same TSV report as the previously user-validated CNL Bezier/native-TDB export preflight. It shows empty-project gate=PASS or BLOCKED in its information dialog. No private TDB registrar is called.

The dangerous CNLPrivateTDBDisposable AEX performs the SAME guard before reading and consuming its one-time acknowledgements and before entering any private registration. It still requires a hand-installed disposable AE host and manual explicit user authorization; no runtime host test was performed in this session.

## Tests

- Both AEX binaries: Windows x64 MSVC Release build and PiPL static checker passed.
- AEX source verifier validates that the gate appears before opt-in and private Registrar call; checks public suite method names and that the existing exact TDB DLL hash and two independent acknowledgments remain.
- The safe AEX v1 previously ran successfully (EXP-SHAPE-028-LIVE-001), but THIS new v2 gate has not yet been tested on AE GUI.
- The dangerous AEX private registry path remains NEVER RUN.

## Important limitations

No project inventory query can make a private Adobe C++ ABI safe or compensate for an unknown canonical/live-instance lifetime. Even with the gate, the private Creator registration can crash AE or invalidate its in-memory state; unregister return true is only a partial signal. Never test within working projects or install this as a regular effect. This change is risk reduction only.

## Next user validation

Test ONLY the rebuilt safe AEX v2 and inspect the new disposable_project_gate_reason. The dangerous registration must remain off until a separate, explicitly authorized disposable environment is ready. A successful first-stage native type registration would still NOT be native vector Contents or AE Pen/vector renderer.

See F-VECTOR-034 and the per-AEX v2 build receipts.
