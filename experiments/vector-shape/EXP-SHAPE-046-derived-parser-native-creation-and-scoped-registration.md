---
status: pass-cross-version-static
date: 2026-10-12
evidence: E2-L
---

# EXP-SHAPE-046 — Genuine native DynamicStreamEffectsParser subclass creates typed groups

Goal: find a real, non-null implementation of `DynamicStreamEffectsParser::CreateEffectGroup` and track its actual owner/registry/cleanup route across installed AE2025/2026 BEE/TDB native binaries.

Methods: decode complete MSVC RTTI inheritance base arrays including non-first BaseClassDescriptor entries, validate x64 CompleteObjectLocator+self RVA and class vtables, correlate slot 22 with the native EndEffect indirect CALL to `CreateEffectGroup`, and recover code that assigns the subclass's vtable. Then decode its bounded .pdata function, TDB constructor calls, memory allocation and persistent string member setup. Finally find direct native xrefs that instantiate the derived parser and correlate with TDB scoped registry and XML parser calls. All analysis is **offline** against installed PE files.

Results PASS both versions:

- Base creator `xor eax,eax; ret` is overridden by `LayerStyleStreamGroupParser` at AE2025 `0x2f6300`, AE2026 `0x2fef50`.
- The override allocates `0x2a0` / `0x270` bytes respectively, constructs a `TDB_NamedStreamGroup`, installs `IndLayerStyleStreamGroup`'s real vtable, sets native members and returns its pointer.
- Two independent native code xrefs to the derived parser vtable were found in each release.
- The real initialization caller has exactly 11 `TDB_ScRegisterStreams::Register` CALLs, 2 TDB `AddStreamToUILayout` CALLs, 1 `dvacore::xml::GetParser` acquisition and 1 explicit `TDB_ScRegisterStreams::UnregisterAll` CALL.
- The register/unregister TDB implementations delegate directly to the underlying factory's corresponding type registration/unregistration functions. Destructor-based cleanup alone is NOT established.
- Host AE2026 public tree corroborates native Layer Style groups exist, but not CNL native group creation.

Sources: F-VECTOR-045/F-VECTOR-046, native code datasets `ae-bee-derived-layer-style-parser-rtti-2025-2026.json`, `ae-bee-layer-style-parser-real-group-2025-2026.json`, `ae-bee-layer-style-parser-creation-callers-2025-2026.json`, `ae-tdb-scoped-registry-lifetime-2025-2026.json`, `ae-native-dynamic-group-lifecycle-crosscheck-2025-2026.json`.

No third-party parser installed, no native CNL group registered, no private mutations run and no Adobe DLL patched. The substantial unsolved product boundaries are (i) legal third-party native owner/child provider registration, (ii) save/reopen and unload-safe stream lifecycle, (iii) AE native Pen/selection binding, and (iv) native BEE_VectorArt/RenderGraph output independent of builtin Shape/Mask layers. Phase F CompNodeAE integration remains prohibited until the user decides.
