---
status: passed-user-manual-AE2026-readonly
date: 2026-10-12
evidence: E2-X
---

# EXP-SHAPE-045 — Public AE2026 parent-specific native owner admission

The user manually executed `CNLNativeOwnerAdmission.aex` on a selected native Shape Layer inside AE2026. The actual host-generated `%TEMP%/CNL_NativeOwner_Admission.tsv` was inspected on the authorized Windows PC and verified through `ShapeLayerAE/tools/verify_host_owner_admission_capture.py` without private API calls.

Tested sample: 186 stream nodes, 33 parent groups, 198 `AEGP_CanAddStream` attempts over six candidates, five positive standard candidate admissions, 33/33 negative returns for unregistered CNL independent group. Root and child tree resolved normally. Real `ADBE Root Vectors Group`, `ADBE Effect Parade`, and `ADBE Layer Styles` with style children were observed. `private_registry_invoked=0`, `stream_created=0`, and no project changes made by the AEX.

Critical limit: maximum traversal depth 4 and 240 nodes, only a selected Shape Layer and only six candidate MatchNames. Do NOT claim the CNL type is globally impossible, that an admitted hypothetical prefix name can be instantiated, or that a standard Shape Layer can be used as the final independent CNL vector owner.

Privacy: **No complete user project TSV is committed to GitHub**. Only type-neutral aggregate counts and standard Adobe type confirmation are included as `datasets/ae2026-owner-admission-host-aggregate-20261012.json`. See F-VECTOR-044.
