---
date: 2026-10-14
status: PASS pinned local aelib.dll imported BEE lifecycle functions cross-module
---
# EXP-SHAPE-074 — aelib -> BEE_Birth/Death direct native calls

**Goal:** Connect the native BEE Layer stream registration lifecycle from EXP-SHAPE-073 back to the host startup module, rather than assuming the BEE code initializes itself.

**Method:** Inspect the PE import tables of ten named modules in each installed AE2025/AE2026 Support Files directory. Identify BEE_Birth and BEE_Death imported symbol/IAT slots. Within the importing aelib.dll, scan RIP-relative CALL/JMP bytes and confirm candidates against complete x64 Capstone instruction boundaries derived from the local PE .pdata function extents. Require file SHA-256 and expected sites on validation.

**Result:** Only `aelib.dll` among the inspected top-level modules directly imports these BEE lifecycle symbols. In each version, two separate aelib callsites target the BEE_Birth IAT slot and one targets BEE_Death. Offline validation 2/2 PASS.

**Limits:** Named ten-module static import set only, and direct RIP-relative IAT calls only. No indirect dynamic DLL loading exclusions, caller runtime reachability, external native class registration, or successful independent Adobe layer creation claims.

**Artifacts:** F-VECTOR-074 and `datasets/ae-aelib-bee-lifecycle-crossmodule-2025-2026.json`; source and verifier under `experiments/vector-shape/probe-src/tools`.

**Safety:** No Adobe host launch/private calls, DLL modifications, potentially hazardous AEX, or CompNodeAE changes.
