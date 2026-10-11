---
status: generated
last_verified: 2026-09-17
---
# Release Pipeline Self-Test

State: **PASS**.

| Check | Result |
|---|---|
| `finalizer_rejects_missing_capture` | **PASS** |
| `promotion_rejects_unready_state` | **PASS** |
| `protected_state_unchanged` | **PASS** |
| `static_rc_still_valid` | **PASS** |
| `version_not_created` | **PASS** |
| `release_page_not_promoted` | **PASS** |

This test intentionally exercises the no-capture finalizer and blocked-promotion paths. Generated diagnostics/previews may change; prediction/model/release state must not.
