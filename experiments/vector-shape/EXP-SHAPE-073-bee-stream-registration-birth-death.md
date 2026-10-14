---
date: 2026-10-14
status: PASS exact AE2025/2026 native registration lifecycle direct-call graph
---
# EXP-SHAPE-073 — BEE_Birth and BEE_Death own native Layer stream registrations

**Goal:** Identify where real native Adobe Layer/AV/Text/Vector stream factory routines are called, and whether these routines are registered by built-in module lifecycle rather than AEGP menu handlers.

**Setup:** Inspect locally installed AE2025/2026 BEE.dll without executing or loading it. Obtain complete `dumpbin /exports` data (over 13k names per version, avoiding `pefile` default 8,192-symbol cap). Recover exact direct x64 CALL/JMP candidates to exported register/unregister routines, require .pdata-containing function decode via Capstone to confirm instruction boundaries, then identify caller export names.

**Result:** Both versions show `BEE_Birth` -> common startup helper -> four family RegisterStreams calls. Both show `BEE_Death` -> common teardown helper -> BEE_Layer RegisterStreams(bool) plus AV/Text/Vector UnregisterStreams. Machine-checkable full graph and RVA differences in dataset and F-VECTOR-073.

**Limit:** Direct calls in these two BEE DLLs only; no indirect-call, other Adobe module, or dynamic plugin type admission completeness claim. Independent external ChapeLayer registration is unproven, not impossible by this evidence alone.

**Safety:** No AE host execution, private call, DLL patch, or CompNodeAE changes.
