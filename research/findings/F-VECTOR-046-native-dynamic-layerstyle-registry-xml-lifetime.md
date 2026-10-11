---
status: static-cross-version-verified-no-private-host-activation
last_verified: 2026-10-12
evidence: E2-L
versions: installed AE2025/2026 BEE.dll and TDB.dll
---

# F-VECTOR-046 — Scoped factory registration, native XML parser and explicit cleanup in real Layer Style initialization

## Native pipeline

F-VECTOR-045 identified `LayerStyleStreamGroupParser` and the concrete `IndLayerStyleStreamGroup` Creator. Finding the derived parser vtable's actual machine-code references led to native BEE initialization routines: AE2025 RVA `0x2FBB60`; AE2026 RVA `0x304640`. Their bounded bodies contain the following **direct imported CALL counts**, verified independently in both versions:

- **11** calls to `TDB_ScRegisterStreams::Register` for native type/creator registration.
- **2** calls to `TDB_StreamGroup::AddStreamToUILayout`, forming canonical UI children.
- **1** call to `dvacore::xml::GetParser` to obtain the host XML document parser.
- **1** call to `TDB_ScRegisterStreams::UnregisterAll` during cleanup.
- AE2025 also contains **one** additional direct `TDB_StreamFactory::UnregisterFactoryFunc` call; the AE2026 body inspected does not.

The same function initializes the derived `LayerStyleStreamGroupParser` vtable, and other code in the module calls the registered `CreateEffectGroup` override during native `EndEffect`. The 11 registrations and host Layer Style hierarchy are consistent in scale but their exact one-to-one MatchName correspondence has not been decoded.

## Factory implementation and safety limits

Separate disassembly of TDB.dll confirms that `TDB_ScRegisterStreams::Register` directly invokes `TDB_StreamFactory::RegisterFactoryFunc`, and that `UnregisterAll` loops through registered MatchNames and invokes `TDB_StreamFactory::UnregisterFactoryFunc`. Thus Adobe's internal example is **temporary scoped registration plus explicit bulk cleanup**, not an isolated registration with no lifetime management.

Do NOT infer that `TDB_ScRegisterStreams`'s destructor automatically performs complete unregistration. The destructor code does not by itself prove such cleanup; the native BEE caller explicitly calls `UnregisterAll`. Nor does this prove every instance/refcount/undo/serialized stream has ceased using factory vtables at cleanup time. The 2025 and 2026 C++ object layouts differ.

A future CNL implementation cannot safely call these private functions solely from the decorated symbol and must establish the full callback, allocation, instance ownership, exception unwind, rollback and plugin unload contracts. No risky `CNLPrivateTDBDisposable.aex` activation occurred, and there has been no new host-authored CNL native Contents creation.

## Reproducibility

- `datasets/ae-tdb-scoped-registry-lifetime-2025-2026.json`
- `datasets/ae-bee-layer-style-parser-creation-callers-2025-2026.json`
- `datasets/ae-native-dynamic-group-lifecycle-crosscheck-2025-2026.json`
- `experiments/vector-shape/probe-src/tools/audit_tdb_scoped_registration_lifetime.py`
- `experiments/vector-shape/probe-src/tools/trace_layer_style_parser_creation_callers.py`
- `experiments/vector-shape/probe-src/tools/verify_native_dynamic_group_lifecycle.py`

`EXP-SHAPE-046` records the verified compiled call chain. No binary copied, modified, or loaded in the AE process, and no `CompNodeAE` modification or Phase F integration performed.
