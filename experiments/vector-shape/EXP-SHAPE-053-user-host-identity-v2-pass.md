---
date: 2026-10-12
status: pass-user-run-AE2026-readonly-v2
evidence: H real TSv from actual AE2026 plugin
---

# EXP-SHAPE-053 — Regress old index-zero crash and check live native Effect ARB metadata

Actual Windows AE2026 `%TEMP%/CNL_OwnedEffect_StreamIdentity_v2.tsv` proves v2 never attempts index=0. Independent regression script `verify_cnl_identity_v2_real_host.py` compares every supported param row with failing v1 and asserts all four valid rows unchanged, all error fields zero, index1 `PF_ParamType=11`/`AEGP_StreamType=7` (native ARB leaf), unique stream IDs all 0, no mutations/private calls/payload inspection. PASS.

This proves the **diagnosed v1 AEGP index-0 host assertion has been corrected in real AE2026** and the Effect's CNL archive really is an AE host ARB parameter. Rendering and save/reopen still require separate user verification. Per-path TDB Contents, AE Pen and BEE_VectorArt are NOT implemented. See F-VECTOR-053.
