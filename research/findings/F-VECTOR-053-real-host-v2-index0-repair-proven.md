---
status: host-AE2026-confirmed-v2-regression-fixed
date: 2026-10-12
evidence: H two user-run public AEGP native report TSVs, zero private calls
---

# F-VECTOR-053 — AE2026 v2: index-zero assertion eliminated, native ARB leaf identity confirmed

## Actual host result

The user reran the manually installed revised `CNLArchiveIdentity.aex` on AE2026. The tool generated `%TEMP%/CNL_OwnedEffect_StreamIdentity_v2.tsv` at 2026-10-12 16:31:31 (593 bytes) and displayed its normal report dialog, with no internal error dialogs shown in that screenshot. We independently read the real TSV, compared to the earlier error-producing v1 TSV and executed `verify_cnl_identity_v2_real_host.py` against both captures.

### Proven

- 1 matching `CNL Owned Vector Document` host effect; `GetEffectNumParamStreams=5`.
- Explicit `param_skipped\t0\tinput_layer_host_rejects_index_zero`, **no query with param_index 0**. This eliminates the precise two invalid calls that raised AE host assertions in v1.
- Exactly param indices 1, 2, 3, 4 queried; each result agrees **byte-for-byte with its successful v1 row**, and all API error fields are zero.
- Index 1: real `PF_Param_ARBITRARY_DATA=11` and native `AEGP_StreamType_ARB=7`, time-varying=1, with match name `CNL Owned Vector Document-0001`.
- 2: slider/OneD; 3: color/Color; 4: checkbox/OneD.
- `AEGP_GetUniqueStreamID` returns **0** for all four param streams, so cannot be treated as unique per-param or per-vertex identity.
- `private_registry_invoked=0`, `mutations=0`, `opaque_arb_payload_read=0`.

This is an actual **v2 AE host verification**, not merely PE checking. It confirms the CNL Effect's publicly supported host parameter metadata path is stable across the repair. It does NOT prove CNL native sub-Contents, native AE Pen/Undo/selection hit testing, BEE_VectorArt, successful image render or saved-AEP reopen. Avoid overclaiming these.

The full raw user project report stays in local TEMP; only a sanitized machine-checkable result is archived. Verification code is in `experiments/vector-shape/probe-src/tools/verify_cnl_identity_v2_real_host.py`; receipt is `datasets/ae-cnl-owned-effect-identity-v2-real-host-verified-20261012.json`.

The corrected plugin's local code is recorded at `experiments/vector-shape/native-owned-effect-identity-lab/`. The failing v1's cause is in F-VECTOR-052.
