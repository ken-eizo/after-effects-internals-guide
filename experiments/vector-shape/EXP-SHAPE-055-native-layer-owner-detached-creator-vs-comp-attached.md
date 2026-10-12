---
date: 2026-10-12
status: PASS-cross-version-BEE-native-factory-argument-disparity
evidence: E2-L exact installed BEE2025/BEE2026 native x64 disassembly
---

# EXP-SHAPE-055 — Verify null CompItem in TDB creator vs real CompItem in stock Shape Layer factory

This directly follows EXP-SHAPE-054: registering `BEE_VectorLayer::Create` in TDB is **not automatically the same operation as creating an attached native AE Shape Layer**.

Two pinned BEE DLLs independently verify:

1. `BEE_VectorLayer::Create` (C++ typed `TDB_StreamBase*` creator) allocates **0x2820 bytes AE2025, 0x2830 bytes AE2026**, then calls `BEE_VectorLayer` constructor with **`xor r9d,r9d`**, passing `BEE_CompItem*=nullptr`.
2. `BEE_Layer::CreateLayerFromType(4, BEE_CompItem*,...)` calls the **same** constructor, but passes its real second argument `BEE_CompItem*` through R9 (2025 saves Comp in RSI, 2026 in RBX). Its integer layer kind switch is bounded 0–7.
3. Native `BEE_Layer::SetParentComp`/`GetParentComp` symbols exist but this experiment did not invoke them or prove they register a layer in `BEE_CompItem` or `BEE_LayerSet`.

**PASS** `verify_native_vector_detached_factory_vs_comp_owner.py` on both installed binaries; offline only. New CNL-owned native editable Contents/rendering is still unimplemented. See F-VECTOR-055.

Archival source in `experiments/vector-shape/probe-src/tools/`; three machine readable datasets in `datasets/ae-bee-vector-*-2025-2026.json`. No Adobe GUI, private registry calls, binary patching or `CompNodeAE` edits.
