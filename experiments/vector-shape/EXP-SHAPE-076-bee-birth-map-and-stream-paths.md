---
date: 2026-10-14
status: PASS native cross-version byte-map initialization separation
---
# EXP-SHAPE-076 — Follow BEE_Birth map argument through native consumers

**Question:** Is `BEE_Birth`'s `map<string, bytes>` directly used as a third-party native Layer/stream Creator registration table?

**Method:** On pinned AE2025 and AE2026 BEE.dll files, disassemble `BEE_Birth` and the immediate callee receiving its saved second parameter. Match the exact `mov rcx, saved map` and direct CALL machine instructions, and contrast with the separate later CALL passing the original first parameter into the built-in stream registrar. Audit map helper's imported localizer/ScScript calls. Fail closed on binary SHA or assembly mismatch.

**Result:** In both versions the byte map flows to one initializer calling Localizer and ScScript facilities; the fixed built-in Layer/AV/Text/Vector stream registration is a separate call. 2/2 PASS.

**Limit:** No full map schema reverse engineering or proof of absent indirect calls. No foreign Layer constructor registration, native timeline or ownership acceptance proven.

**Safety:** Read-only offline PE analysis, no private AE invocation, Adobe modification or CompNodeAE changes.
