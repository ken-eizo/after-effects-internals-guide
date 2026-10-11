---
status: verified-in-AE2026-readonly
last_verified: 2026-10-12
evidence: E2-X
---

# EXP-SHAPE-038 — Active-item-not-root preflight is a conservative safety block

The user manually executed CNLNativeVectorHostProbe.aex in AE2026. The screenshot said Bezier=YES, pinned TDB=2026, factory getter=1, empty-project gate=BLOCKED (reason=active_item_not_root).

The actual user-host-generated TEMP TSV, modified at 2026-10-12 05:36:49, was read from the Windows device and archived in experiments/observatory/runs/EXP-SHAPE-038. Key values: project_count=1, project_is_dirty=1, project_has_saved_path=0, active_non_root=1, non_root_items=-1 and render_queue_items=-1 (not reached; NOT confirmed empty). The independent CNL Bezier document succeeded with four cubics and a 373-byte archive. Private TDB factory getter pointer was nonnull and private_registry_registration_invoked=0.

Both dirty project and non-root active item violate the conservative high-risk test gate. Clearing selection alone is insufficient while project_is_dirty=1. This host observation is not a new native registered type, independent Contents, Pen binding, or BEE_VectorArt renderer.

No mutation of native private registration was performed; do NOT execute CNLPrivateTDBDisposable.aex based on this preflight.
