# EXP-SHAPE-093 — OM native Mask Shape Stream and FLT effect stream class registration across DLL boundaries

**Result: PASS offline, both installed Windows AE 2025 / AE 2026.**

This experiment proves real code paths that are architecturally closer to an Adobe-host-native third-party Stream extension than PF param arrays or a separate timeline editor — but **they are still Adobe first-party DLLs, not third-party plug-in registration**.

## Discoveries

- `OM.dll!OM_Birth` constructs `TDB_MatchName("ADBE Mask Shape")`, binds a `std::function` to its own `OM_Stream::Create` C++ class creator, and directly calls `TDB.dll!TDB_StreamFactory::RegisterFactoryFunc`. `OM_Death` calls `UnregisterFactoryFunc` and releases its global native match-name object. Both versions verified.
- `OM_Stream` is an actual native path-like class with exported clone, read/write and value operations. This is a real Adobe host-native stream implemented outside TDB/BEE.
- `FLT.dll` constructs `TDB_ScRegisterStreams` and registers **6** (AE2025) or **7** (AE2026) native Effect/Mask Stream classes/groups with direct imported CALL instructions and concrete `LEA RDX` global MatchName pointers.
- AE2026 adds `FLT_StreamName_EFFECT_BLENDMODE` compared with 2025.
- `aelib.dll` includes one native host initialisation function per version containing direct CALL instructions in the sequence `OM_Birth → FLT_Birth → BEE_Birth`, and one native teardown function with `OM_Death → FLT_Death → BEE_Death` callsites (code order; not universal proof of execution of every conditional branch).
- Exhaustive local direct-import census: 1,073 installed PE files in 2025, 1,219 in 2026. Native type registrar importers are host-owned `BEE.dll`, `FLT.dll`, `OM.dll` and aelib's teardown. No standard third-party AEX provider interface demonstrated.

## Reproduce

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_om_flt_bee_crossmodule_native_registration.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\resolve_flt_native_effect_registered_names.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\trace_aelib_native_stream_family_boot_order.py"
```

Optional larger scans (static, several minutes on a spinning disk):

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\audit_native_tdb_registrar_imports_all_pe.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\scan_native_registrar_direct_callsites.py"
```

Detailed source evidence: `research/findings/F-VECTOR-093-om-flt-crossdll-native-timeline-stream-registration.md`. Reproducible JSON in the five `datasets/ae-native-*`, `ae-flt-*` and `ae-aelib-*` receipts enumerated there.

## Completion gate

**NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM.** The discovery proves a native cross-DLL class creation architecture within Adobe, not yet a foreign `CNL:` Stream/Group added to the native AE Timeline. No private host function was invoked, no production AE project or Adobe installed binary modified, and the paused VirtualBox/VM project remains paused.
