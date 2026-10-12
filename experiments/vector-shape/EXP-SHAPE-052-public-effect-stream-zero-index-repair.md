---
status: live-v1-failed-zero-index-fixed-v2-offline-pass
date: 2026-10-12
evidence: H real AE2026 TSV + two MSVC x64 builds + source/PE verifier
---

# EXP-SHAPE-052 — CNL owned effect native stream v1 assertion and corrected v2

User ran `CNLArchiveIdentity.aex` v1 and received two AE2026 internal assertion dialogs (`param_index out of range`, 5027::56 and 5027::150). The tool's read-only completion popup did not signify success. Analysis of the actual generated `%TEMP%/CNL_OwnedEffect_StreamIdentity.tsv`:

- Matched CNL Effect count 1; total param count 5.
- Both official metadata and stream-ref public calls with **param_index=0** returned error code 3, triggering AE assertions.
- Indices 1 through 4 all returned A_Err=0, including index1 **PF_ParamType=11 (ARB) and AEGP_StreamType=7 (ARB)**, confirming native-backed CNL document param in AE2026.
- All successful AEGP UniqueStreamID queries yielded **0**. They do not prove different stable IDs.

Patched `CNLArchiveIdentity.cpp` to never call either indexed SDK API for 0; loops 1..N-1, prints `param_skipped 0`, writes `%TEMP%/CNL_OwnedEffect_StreamIdentity_v2.tsv` (old file preserved). Both local and independently archived AEIG source x64 Release builds pass read-only PE/source checks with explicit index1 bounds regression assertion. No host v2 execution yet. This is an actual failure diagnosed and repaired, **not** product native Pen/VectorArt completion.

Source and evidence: F-VECTOR-052; `experiments/vector-shape/native-owned-effect-identity-lab/`; sanitized dataset and `analyze_identity_v1_host_failure.py` parser. AEGUI/install is user-only; unrelated private-disposable AEX remains forbidden; CompNodeAE stays untouched.
