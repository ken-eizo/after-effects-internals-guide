---
status: strongly-supported-static-two-native-binaries
last_verified: 2026-10-12
evidence: E2-L
versions: pinned AE2025/AE2026 BEE.dll, FLT.dll, TDB.dll; Windows PE
---

# F-VECTOR-043 — DynamicStreamEffectsParser builds native Effect Canonical UI children through real TDB group calls

## Why this matters

F-VECTOR-040/042 identified the whitelist admission gate and virtual Canonical UILayout setup for children of a native Effect sequence. Until now the **actual producer** inserting dynamic effect children into that TDB layout was less clear. In both pinned AE2025 and AE2026 BEE.dll builds, real compiled code in **`BEE::ae::DynamicStreamEffectsParser::EndEffect`** issues two distinct `CALL qword ptr [RIP+...]` instructions importing `TDB.dll!TDB_StreamGroup::AddStreamToUILayout(TDB_StreamBase const*,unsigned int)`. This is executable callsite evidence, not merely an export inventory or import thunk.

| Site | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| EndEffect function start | `0x2f6800` | `0x2ff440` |
| First real TDB AddStreamToUILayout CALL | `0x2f6cbf` | `0x2ff8d9` |
| Second real TDB AddStreamToUILayout CALL | `0x2f6d1a` | `0x2ff92a` |

Before both calls, native code obtains a host object, invokes a virtual slot `+0x88` on it, then sets `RCX=RAX` (group), `RDX` (stream child) and `R8D` (insertion index). These are actual register-transfer witnesses. We have **not yet demonstrated** that the child can be an externally registered custom Bezier/vector type, or that this runtime parser can be invoked as a third-party extension interface. Native class type and lifetime of the returned group at the virtual call still require exact resolution.

There are other direct calls from two additional BEE routines in each pinned version, including AE2026 RVAs `0x2cd09e`, `0x30492a`, `0x30496f`, and AE2025 analogues. This strongly indicates native layout construction is used beyond one parser branch, but the type of each owning stream group must be separately established.

## Another distinct Adobe module boundary

A read-only import inventory of the **443 top-level DLL/EXE** files in AE2026 Support Files found that `BEE.dll` and `FRP.dll` both import the FLT method `FLT_FCSeqSpec::AddStreamToUILayout`; BEE.dll additionally imports the native `TDB_StreamGroup::AddStreamToUILayout`, `FLT_RegisterPseudoEffect`, and the TDB type registrar. `OM.dll` also imports the TDB registrar. This is an upper-level *connection graph*, not permission for plugins to call these exported routines.

**Important falsification:** The scanned `FRP.dll` occurrences of `FLT_FCSeqSpec::AddStreamToUILayout` (2025 `0x1462706`, 2026 `0x14621bc`) are `JMP` import thunks, **not proven real application callsites**. The BEE.dll imported FLT function occurrences are also `JMP` stubs in the inspected scope. Our reliable dynamic parser witnesses are the executable BEE `CALL` instructions into the **TDB** group append method. We must not mislabel trampoline edges as active callsites.

## What the host is actually parsing

The BEE export table contains `DynamicStreamEffectsParser::StartEffect`, `EndEffect`, `HandleParamBase`, `ParameterMatchNameFromExternalID`, `CreateEffectGroup`, `GetExternalTypes`, and `GetStreamFactory`, plus `EffectsParser::HandleSlider/HandleAngle/HandleCheckbox/HandleColor/HandleGradient/HandleLayer/HandlePoint/HandlePoint3D/HandlePopup`. These **export names** and compiled `EndEffect` body establish a native route from dynamic effect parameter definitions to host-owned Canonical UI groups.

They do not by themselves demonstrate support for externally-defined path/Bezier types, arbitrary new object classes, a native Pen tool target or `BEE_VectorArt` return values. The existing public `PF_Param_PATH` only references source layer paths and is not an owned vector object.

## Product-relevant implementation consequence

A realistic Phase C route must examine the creation of the actual dynamic effects' TDB parent, child canonical MatchNames, constructed stream C++ type and `AddStreamToUILayout` ownership, **without** assuming global TDB factory registration edits a real owner's whitelist. Next decode `DynamicStreamEffectsParser::EndEffect` and `StartEffect` inputs along with the downstream host owner; then determine if any supported plug-in registration path can admit a novel compound native vector group and persist it.

A native canonical child alone still leaves Phase D AE Pen/Selection dispatch and Phase E BEE_VectorArt/RG handoff unsolved. The presence of private exported calls is *not* a safe Adobe API; NEVER inject these calls into a working AEX before ABI/lifetime/rollback research and separate manual disposable-host authorization.

## Reproduction and evidence

- `datasets/ae-flt-addlayout-crossmodule-import-inventory-2026.json`
- `datasets/ae-flt-addlayout-crossmodule-direct-calls-2025-2026.json`
- `datasets/ae-bee-dynamic-effects-layout-call-verification-2025-2026.json`
- Source scripts `audit_flt_addlayout_crossmodule_imports.py`, `trace_flt_addlayout_crossmodule_callsites.py`, `verify_bee_dynamic_effect_layout_calls.py` under `experiments/vector-shape/probe-src/tools/`.

Native routines were never invoked in an AE process. Findings are E2-L version-specific PE evidence; no standalone editable renderer or independent Contents plugin is yet established. `D:/Developer/CompNodeAE` remains untouched and Phase F is intentionally not started.

## Default `CreateEffectGroup` is not a group creator (additional cross-version check)

The exported base virtual `BEE::ae::DynamicStreamEffectsParser::CreateEffectGroup(TDB_MatchName const&,wstring const&,wstring const&)` consists solely of `xor eax,eax; ret` in both pinned versions (AE2025 BEE RVA `0xe3960`; AE2026 BEE RVA `0xe9d20`). Thus the base hook itself returns `nullptr`. This places an additional explicit condition on the otherwise promising EndEffect UI-child append sites: any real separately created effect-group owner must come from a different implementation/override or pre-existing group setup. We have NOT traced a concrete override or proven external dynamic parser registration. Do not claim the base dynamic parser instantiates arbitrary independent Contents by itself.

Reproduction source `experiments/vector-shape/probe-src/tools/audit_bee_dynamic_effect_parser_factory_hooks.py` and receipt `datasets/ae-bee-dynamic-parser-factory-hooks-2025-2026.json` (static). The absence of some named helpers in the analyzed PE export set does not prove no other internal call path.
