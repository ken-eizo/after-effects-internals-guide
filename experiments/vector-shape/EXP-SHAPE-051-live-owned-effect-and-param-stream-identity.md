---
date: 2026-10-12
status: host-evidence-pass / new-focused-read-only-AEGP-offline-build-pass / new-AEGP-host-test-pending
evidence: H + E2-L
---

# EXP-SHAPE-051 — CNL effect's true native host owner and parameter-stream identities

## Confirmed user-run AE2026 log

After user invokes the existing CNL Native Owner Admission in real AE2026, read `%TEMP%/CNL_NativeOwner_Admission.tsv` (not just the "Read-only trace" popup). Snapshot is 21,353 bytes, last written at 13:23:48. It confirms real `ADBE AV Layer` → `ADBE Effect Parade` → `CNL Owned Vector Document`; this named Effect group has five `-0000 ... -0004` native leaves and one built-in group. 173 streams visited, no registry writes or newly created streams. All candidates for dynamic CNL Vector native Contents under the Effect group returned `CanAdd=0`; this is a negative result for the simple public AddStream implementation route, independent of static FLT/BEE restrictions.

Sanitized JSON preserves CNL tree without revealing other user project contents. See F-VECTOR-051.

## New executable host probe (read-only)

Standalone, independently built `native-owned-effect-identity-lab/CNLArchiveIdentity.aex` uses documented public AEGP SDK `AEGP_EffectSuite5`, `AEGP_StreamSuite6` and `AEGP_DynamicStreamSuite2` to query actual param indexes, PF types, AEGP stream types, stream unique IDs, time variance and match names **for CNL Owned Vector Document only**. No arbitrary payload bytes read; no writes, TDB registrar or Adobe private methods.

Original ShapeLayerAE Release AEX and fresh AEIG-archived-source build both compile; both verify PE/PiPL/read-only API constraints. These **are offline results**; the new plugin has not been installed or run inside AE. User may manually test on a disposable project and return `%TEMP%/CNL_OwnedEffect_StreamIdentity.tsv`; preserve first TSV before running again after a save/reopen test.

## Expected evidence to resolve next

Determine if `-0001` is `PF_Param_ARBITRARY_DATA=11` and `AEGP_StreamType_ARB=7`, whether public stream unique IDs are returned, and whether the same CNL Effect, archive value and rendering survive actual AE project save/reopen. If true, focus on legitimate host write/Undo path for a CNL blob separately from the still unproven native per-vertex Pen/Contents evaluator. Never claim a CNL opaque ARB leaf is a native Pen-editable path.
