---
status: live-AE2026-host-errors-explained-v2-public-probe-built-offline-passed
date: 2026-10-12
evidence: H actual AE 2026 TSV + local SDK headers + two v2 compiled AEX builds
---

# F-VECTOR-052 — Actual host `param_index=0` assertion, correct ARB type observed, probe v2 repaired

## Direct screenshot + real captured host evidence

The user ran the previously built `CNLArchiveIdentity.aex` (EXP-SHAPE-051, **v1**) in real AE2026. AE emitted:

- `After Effects error: internal verification failure, sorry! {param_index out of range}` (5027::56).
- `After Effects error: internal verification failure, sorry! {effect param_index out of range ([i_num_streams-1])}` (5027::150).
- The AEGP finally displayed its generic read-only TSV report path, which was **not an indication all API calls succeeded**.

The newly generated `%TEMP%/CNL_OwnedEffect_StreamIdentity.tsv`, confirmed written 2026-10-12 16:11:04, has `effect_count=1`, matching Effect `CNL Owned Vector Document`, and `AEGP_GetEffectNumParamStreams=5`. The v1 test then iterated `index=0..4`. **Both** `AEGP_GetEffectParamUnionByIndex(index=0)` and `AEGP_GetNewEffectStreamByIndex(index=0)` returned **A_Err=3**. Those invalid queries correspond to the two host internal assertions. Source had no effect mutation calls.

At **indexes 1–4**, all public metadata queries succeeded (`A_Err=0`). Verified actual values:

| Index | PF_ParamType | AEGP_StreamType | Time-varying |
|---|---:|---:|---:|
| 1, CNL Owned CNL archive | 11 (PF_Param_ARBITRARY_DATA) | 7 (AEGP_StreamType_ARB) | 1 |
| 2, Stroke Width | 1 (Slider) | 5 (OneD) | 1 |
| 3, Stroke Color | 5 (Color) | 6 (Color) | 1 |
| 4, Transparent Input | 4 (Checkbox) | 5 (OneD) | 1 |

`AEGP_GetUniqueStreamID` returned **0 for every index 1–4**, all with `A_Err=0`. The returned zero cannot serve as proof of distinguishable stable stream identity. Native CNL per-vertex StreamIDs remain unimplemented.

The Adobe SDK header for these two APIs describes index 0 as the Effect input layer. **Do not generalize** the unexpected AE2026 runtime error as a universal Adobe SDK contract. The evidence proves this host/effect/probe combination rejects those v1 calls at index 0; it does not isolate whether all other AE versions behave identically. This is a public-API probing failure, not evidence of corrupted CNL archive data or a private registry operation.

## Exact defensive patch and test

The independent probe's entry `labs/native_owned_archive_identity/CNLArchiveIdentity.cpp` is updated to:

- Only enumerate actual effect-owned parameter indices **1 through `N-1`**. It no longer calls **either** metadata or stream query API for index 0.
- Emit explicit `param_skipped\t0\tinput_layer_host_rejects_index_zero` marker.
- Write to new `%TEMP%/CNL_OwnedEffect_StreamIdentity_v2.tsv`, keeping the valuable v1 error evidence intact.
- Maintain strict READ-ONLY behavior: no arbitrary payload reads, no project writes, no private native FLT/TDB/BEE call.

The patched AEX built successfully in Windows x64 Release and passed the source+PE verifier with explicit `index=1` loop regression assertion. A *second independent source-only rebuild* from AEIG's archived experiment path also built and passed the same static verifier. These are **offline checks**, not successful AE host execution of the patched version. No Adobe GUI was operated by the agent.

### Actual files

- `ShapeLayerAE/build/native_owned_archive_identity/Release/CNLArchiveIdentity.aex` (v2 candidate).
- `experiments/vector-shape/native-owned-effect-identity-lab/` (standalone archived source).
- `datasets/ae-cnl-owned-effect-identity-v1-host-error-sanitized-20261012.json` (privacy-safe host result; raw user TSV not committed).
- `datasets/ae-cnl-effect-identity-v2-local-build-20261012.json` and `datasets/ae-cnl-effect-identity-v2-independent-build-20261012.json`.
- `experiments/vector-shape/probe-src/tools/analyze_identity_v1_host_failure.py`.

## User guidance

Do not run the v1 AEX again. If optional revalidation is desired, **close AE, manually replace the installed AEX with the rebuilt v2 binary, then restart AE**, use only a disposable project and inspect the new `_v2.tsv`. Do not keep v1/v2 versions side by side: the internal plugin registration/menu names overlap. No need to repeat the old error-producing probe solely to establish ARB type; its successful index1 report already proves the host native ARB stream.

The result still does not establish project save/reopen, native Pen path editing, dedicated CNL host Contents, or BEE_VectorArt rendering. All remain separate gates. `CompNodeAE`/Phase F stay untouched.
