---
status: pass-static-cross-version
last_verified: 2026-10-12
evidence: E2-L
---

# EXP-SHAPE-042 — Resolve BEE_StreamSpec from its actual owner/path ABI

Goal: determine what authentic host context `BEE_GetStreamWithSpec` requires, versus assuming a detached vector ID is sufficient.

Procedure: decode the exact installed AE2025 and AE2026 BEE.dll exports. Detect short exported leaf/adjustor thunks with no unwind .pdata; follow their final unconditional JMP to a real .pdata-covered function before disassembly. Extract the first instructions, machine-code register transforms and native `BEE_StreamTypeHasStream`'s special Effect path classification.

Results: PASS. Both versions use the identical register adapter that loads `BEE_Layer*` from `BEE_StreamSpec+8` and uses the inline `TDB_StreamIDPath` at `+16`. Effect path classification is a real native branch. This is static evidence for necessary owner identity, NOT an externally supported writable Effect Contents channel. No native API invoked.

Sources: `experiments/vector-shape/probe-src/tools/trace_native_streamspec_resolver.py`, `verify_native_streamspec_owner_identity.py`; full datasets `ae-native-streamspec-resolver-effect-gate-2025-2026.json`, `ae-native-streamspec-owner-identity-verified-2025-2026.json`. See F-VECTOR-041. Separate native parent admission proof in EXP-SHAPE-041 and additional canonical initialization evidence in EXP-SHAPE-043.
