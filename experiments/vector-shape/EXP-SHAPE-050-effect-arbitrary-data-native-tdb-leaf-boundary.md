---
status: pass-offline-cross-version-native-PE
date: 2026-10-12
evidence: E2-L
---

# EXP-SHAPE-050 — Prove Effect-owned arbitrary archive's FLT native TDB stream boundary

Read exact installed 2025/26 FLT.dll export tables, vtables and .pdata-bounded x64 code for `FLT_ParamArbDataStream::Create`, `CloneStream`, ctor, `DisposeValue`, `FLT_ArbitraryPrint`/`PrintSize`/`Scan`, `DeleteArbDataItem`, and `FLT_SeqInqParamStream`. Cross-version verifier confirms allocation size `0x470`, derived TDB stream constructor, native clone, host `TDB_StreamBase::GetParamDef` use during disposal, and associated Effect spec lookup for print/scan. NO private Adobe code executed.

**PASS** AE2025 and AE2026. The host really implements `PF_Param_ARBITRARY_DATA` as an FLT/TDB native parameter **leaf**, providing a legitimate host-owned storage boundary for the CNL blob of EXP-SHAPE-049. This is **not** a native CNL TDB Contents hierarchy: no per-vertex IDPath, no Pen hit-test, no BEE_VectorArt. Actual host persistence requires manual user test of `CNLOwnedVectorEffect.aex`.

Full static evidence and scripts in F-VECTOR-050 and the `ae-flt-effect-arbitrary-native-stream-bridge-*.json` datasets. CompNodeAE untouched and Phase F prohibited.
