---
status: generated
last_verified: 2026-09-17
---
# Prediction Lock Integrity Self-Test

State: **PASS**.

| Check | Result |
|---|---|
| `baseline_freeze_pass` | **PASS** |
| `baseline_lock_unchanged` | **PASS** |
| `mutable_fields_allowed` | **PASS** |
| `mutable_fields_do_not_relock` | **PASS** |
| `immutable_change_rejected` | **PASS** |
| `immutable_rejection_preserves_lock` | **PASS** |

Status/evidence are mutable post-observation fields. Prediction text and other immutable preregistration fields cannot be silently re-locked by the freeze tool.
