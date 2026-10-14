---
date: 2026-10-14
status: PASS two real Windows Adobe 2025/2026 native module cross-DLL stream factory registrations and host boot lifecycle; NO foreign third-party AEX registration demonstrated
evidence: E2-L SHA-pinned OM.dll / FLT.dll / aelib.dll and full PE imports/exports, precise Capstone x64 .pdata CALL and RDX/RCX dataflow verification, independent verifier
---
# F-VECTOR-093 — Native custom Stream implementation outside BEE.dll: OM mask path, FLT effect groups, and host initialization order

## Why this is a new architectural discovery

ChapeLayer requires **genuinely new C++ property and group classes hosted by Adobe's standard Timeline**, not a clone of pre-existing Shape/Mask/Text, a PF parameter topic, a separate editor panel or a CNL-only typed runtime. Prior evidence primarily followed `BEE_Layer::RegisterStreams` in BEE.dll.

This investigation establishes a **concrete different Adobe module registering its OWN C++ subclass of the native TDB stream base**, not merely reading streams through AEGP: **`OM.dll` implements `OM_Stream` and registers it under the native `ADBE Mask Shape` MatchName at `OM_Birth`**. `FLT.dll`, independently, registers native typed Effect/Mask streams and native groups.

These are **Adobe first-party internal modules**, loaded in native application initialization. Cross-DLL native class registration is therefore real, but no supported external AEX extension ABI is thereby proven.

## Discovery 1 — OM.dll truly registers its own native TDB_StreamBase subclass

The exact 2025 and 2026 OM.dll exports and compiled instructions establish this chain:

```text
aelib.dll native initialization
  └─ OM.dll!OM_Birth()
       ├─ construct TDB_MatchName("ADBE Mask Shape")
       ├─ store owned native MatchName pointer:
       │    OM_StreamNamePtr_MASK_SHAPE
       ├─ Get_AE_StreamFactory()                  [import TDB.dll]
       ├─ std::function constructor from:
       │    &OM_Stream::Create                    [defined in OM.dll]
       └─ TDB_StreamFactory::RegisterFactoryFunc  [import TDB.dll]

aelib.dll native shutdown
  └─ OM.dll!OM_Death()
       ├─ Get_AE_StreamFactory()
       ├─ OM_StreamNamePtr_MASK_SHAPE
       └─ TDB_StreamFactory::UnregisterFactoryFunc [import TDB.dll]
            (then OM releases and clears its owned MatchName pointer)
```

| Code item | AE2025 OM.dll RVA | AE2026 OM.dll RVA |
| --- | ---: | ---: |
| `OM_Birth` | `0x3280` | `0x3180` |
| `RegisterFactoryFunc` actual IAT CALL | `0x332B` | `0x322A` |
| `OM_Stream::Create` | `0x2610` | `0x2650` |
| `OM_Death` | `0x33C0` | `0x32C0` |
| `UnregisterFactoryFunc` actual IAT CALL | `0x3402` | `0x3302` |

Crucial **original MatchName proof**: each OM_Birth body has a literal `ADBE Mask Shape\0` passed via `RDX` into TDB's native `TDB_MatchName` constructor (2025 at `0x32D4`; 2026 at `0x31D4`). The resulting object pointer is stored in the **exported** `OM_StreamNamePtr_MASK_SHAPE`, and that very global is read as `RDX` for `RegisterFactoryFunc` and again for `UnregisterFactoryFunc`. `OM_Stream::Create` is resolved from a `LEA` source operand in the same actual Birth function. This is **not** an inference from file naming alone.

### It is a genuine host-native property type, not a metadata-only adapter

OM.dll exports a concrete `OM_Stream::Create` returning `TDB_StreamBase*`, together with native `OM_Stream` methods:

- `CloneStream`
- `Read` / `Write`
- `SetValue` / `GetValueEx`
- `CanHaveExpression`, temporal/key operations and special OM_Shape value support

These exported C++ methods and the registered class creator demonstrate a substantial separately implemented native stream in an Adobe DLL. `ADBE Mask Shape` is a **pre-existing Adobe native Mask Path type** — this experiment did not create it, nor insert a new CNL property into an active AE project.

The module depends on internal `TDB.dll` and Adobe's memory/lifecycle routines, not public AEGP plugin registration. OM_Death performs explicit unregister; the presence of unregister does not prove every live host reference or serialized object is safe to destroy at arbitrary times.

## Discovery 2 — FLT.dll owns its native Effect property and group registrations

A completely separate native internal path in FLT.dll obtains `Get_AE_StreamFactory` and constructs an `TDB_ScRegisterStreams` registrar with that factory. Exact direct imported `TDB_ScRegisterStreams::Register` calls install these known-native MatchNames:

| FLT MatchName global suffix (verified from `LEA RDX`) | AE2025 | AE2026 |
| --- | :---: | :---: |
| `EFFECT_PATH_PARAM` | ✓ | ✓ |
| `EFFECT_OPACITY` | ✓ | ✓ |
| **`EFFECT_BLENDMODE`** | — | **✓ newly added** |
| `MASK` | ✓ | ✓ |
| `MASKS_PARADE` | ✓ | ✓ |
| `FORCE_CPU_GPU` | ✓ | ✓ |
| `EFFECT_BUILT_IN_PARAMS` | ✓ | ✓ |
| **Total native typed register CALLs in this helper** | **6** | **7** |

The effect-local path parameter type uses `FLT_EffectMaskParamPathStreamRef::Create`, while the `MASK` and `MASKS_PARADE` groups use their own concrete `FLT_Mask::Create` and `FLT_MasksParade::Create`. Other native value types use Adobe's float/popup stream templates and the built-in effect-parameter group.

FLT's explicit native teardown path calls `TDB_ScRegisterStreams::UnregisterAll`; the object also has its own destructor. This is a **different lifecycle wrapper** from OM's direct `RegisterFactoryFunc`/explicit unregister. Both patterns exist in shipped native host DLLs, but neither is a documented third-party SDK API.

## Discovery 3 — Native owner registration is orchestrated through aelib.dll

In both installed versions, **one and the same aelib.dll native initialization function** contains real x64 CALL instructions to the three module Birth exports in this code order:

```text
aelib.dll native initialization body:
  OM_Birth()  -> FLT_Birth(...) -> BEE_Birth(...)

aelib.dll native teardown body:
  OM_Death()  -> FLT_Death()     -> BEE_Death()
```

| Call instruction | AE2025 aelib.dll | AE2026 aelib.dll |
| --- | --- | --- |
| OM_Birth | `0x6E05D` | `0x70444` |
| FLT_Birth | `0x6E08B` | `0x70472` |
| BEE_Birth | `0x6E272` | `0x70647` |
| OM_Death | `0x6EF24` | `0x712B4` |
| FLT_Death | `0x6EF40` | `0x712D0` |
| BEE_Death | `0x6EF56` | `0x712E6` |

**Careful interpretation:** These are machine-code callsite ordering facts, not proof that every conditional branch in every user session executes them all in exactly this runtime sequence. Each module also has other native callsites for its Birth. This is not ordinary user AEX AEGP plug-in startup. It is Adobe's own `aelib.dll` orchestrating its internal DLLs.

### Full installed Adobe executable-module registrar audit (distinct from AEX-only scan)

Scan of every installed `.dll/.exe/.aex` under Support Files yielded:

- AE2025: **1,073/1,073** PE modules parsed, zero parsing failures.
- AE2026: **1,219/1,219** PE modules parsed, zero parsing failures.
- The direct `TDB_ScRegisterStreams::Register` callers/importers include `BEE.dll` and `FLT.dll`.
- The direct `TDB_StreamFactory::RegisterFactoryFunc` callers/importers include `BEE.dll` and **`OM.dll`**.
- `aelib.dll` additionally imports the direct unregister method (one direct CALL in AE2025 `RegisterSamuraiDynamicStreams`; only an import thunk in the audited AE2026 case).
- The prior AEX-only scan (F-VECTOR-089) found **zero direct native registrar imports by AEX files**. None of the 1,073/1,219 PE importers demonstrates a supported external plug-in ABI.

The source/aggregate is intentionally privacy scoped: names of user-installed third-party plug-ins are **not included in published data**. This is a direct-import inventory; it does not rule out `GetProcAddress`, delay imports, or host-supplied Suite callbacks.

## Consequence for independently authored ChapeLayer

The new finding is affirmative and narrow: **cross-DLL class registration of host-native TDB Streams, including a separately implemented complex Mask Path value, is a real architectural mechanism**. The OM native module is a better technical reference than trying to equate `PF_Param_ARBITRARY_DATA` or an independent CNL vector runtime with Adobe host property classes.

What it does NOT establish:

1. An AEX loaded through the public Adobe SDK can register an arbitrary `CNL:` native C++ Stream class at the correct time in the host lifecycle.
2. Adobe will admit an unknown child type to Paint/Text's fixed canonical parent layout, or a Shape prefix-passing parent will successfully construct the new class.
3. C++ class RTTI, host allocation, TDB virtual layout, clone/archive/version migration and cleanup remain compatible when a third-party DLL is unloaded.
4. Adobe's standard Timeline Property Editor will display/edit/keyframe a new type and serialize it into an .aep.
5. BEE_VectorArt native operator evaluator/renderer will accept a foreign operator, or macOS supports the equivalent private ABI.

`OM_Stream` demonstrates an **Adobe-owned** correctly integrated implementation, not a newly tested third-party extension. No private APIs were invoked in AE; no Adobe files changed. The user requested to defer VM construction, which remains paused.

## Reproduction (original Windows AE 2025 + 2026 PE images only)

- `experiments/vector-shape/probe-src/tools/verify_om_flt_bee_crossmodule_native_registration.py` — **independent complete PASS 2/2**, verifies original file hashes, OM match literal, creator/global dataflow, direct registrar and unregister CALLs, concrete read/write/clone/value methods, FLT typed MatchNames and aelib initialization order.
- `experiments/vector-shape/probe-src/tools/resolve_flt_native_effect_registered_names.py`
- `experiments/vector-shape/probe-src/tools/trace_aelib_native_stream_family_boot_order.py`
- `experiments/vector-shape/probe-src/tools/audit_native_tdb_registrar_imports_all_pe.py`
- `experiments/vector-shape/probe-src/tools/scan_native_registrar_direct_callsites.py`

Pinned datasets:

- `datasets/ae-native-om-flt-bee-crossmodule-boot-verified-2025-2026.json`
- `datasets/ae-native-tdb-registrar-import-graph-2025-2026.json`
- `datasets/ae-native-tdb-registrar-direct-callsites-2025-2026.json`
- `datasets/ae-flt-native-effect-register-types-2025-2026.json`
- `datasets/ae-aelib-om-flt-bee-native-birth-death-2025-2026.json`

No Adobe binary distributed, no runtime private call executed, and original user AE processes or user projects were not altered.
