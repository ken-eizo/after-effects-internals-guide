---
date: 2026-10-14
status: PASS scoped installed SDK 25.6 static surface audit
---
# EXP-SHAPE-072 — Public AEGP native layer creation versus custom type registration

**Method:** Read the installed `AE_GeneralPlug.h` without invoking AE. Extract all public `AEGP_RegisterSuite5` function-pointer names; assert the full expected 12-name set, check the exact `AEGP_CreateVectorLayerInComp` signature, enumerate `AEGP_ObjectType`, and confirm `AEGP_Menu_NEW` and DynamicStream operations.

**Evidence:** Existing native Vector Layer creation is a first-class public API. The audited Register Suite registers Artisan, IO, commands and other hooks, not arbitrary `BEE_Layer` subclasses or `TDB_StreamBase` child types. An independent ChapeLayer is **not** thereby implemented.

**Scope:** One locally installed SDK 25.6 header. Absence in this finite exported public registration surface is not a proof of global impossibility or of the absence of private registration methods in Adobe DLLs.

**Artifacts:** `research/findings/F-VECTOR-072-public-aegp-native-layer-registration-surface.md`, `datasets/ae-public-sdk-native-layer-extension-surface-25-6.json`, `experiments/vector-shape/probe-src/tools/audit_public_sdk_native_layer_extension.py`.

**Host safety:** No AE GUI, binary modification, private host registration or CompNodeAE mutation.
