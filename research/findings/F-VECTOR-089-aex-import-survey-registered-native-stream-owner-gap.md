---
date: 2026-10-14
status: PASS read-only cross-version direct-import audit, no external registrar entrypoint demonstrated
evidence: E2-L parsed installed AE2025/AE2026 AEX PE import tables and full native DLL export census; reproducible aggregation without publishing personal third-party installed names
---
# F-VECTOR-089 — AE2025/AE2026 AEX survey: native internal APIs versus external Stream creator registration

## Exact requirement

Can a loadable Adobe/third-party AEX register a **new** host-native TDB Stream class and a new native parent group schema that directly appears in Adobe's ordinary Timeline, like the built-in Paint Strokes or Text Animator, rather than merely access existing Adobe property types?

## Full installed AEX direct import audit

Scanned every file ending in `.aex` under each installed `Required` and `Plug-ins`, including both Adobe and user-installed third-party modules. To avoid publishing the user's private installed plugin inventory, only aggregate counts and the names of explicitly recognized bundled Adobe/Maxon modules are included in the committed dataset.

| Measure | AE2025 | AE2026 |
| --- | ---: | ---: |
| Installed AEX parsed | **481 / 481** | **633 / 633** |
| Direct `TDB.dll` importer AEX | **22** | **23** |
| Direct `BEE.dll` importer AEX | **50** | **52** |
| Directly imports `TDB_ScRegisterStreams::Register`, `TDB_StreamFactory::RegisterFactoryFunc`, `UnregisterFactoryFunc` or `BEE_Layer/AVLayer::RegisterStreams` | **0** | **0** |

The interesting fact is that **Adobe-owned AEXs do use private native BEE/TDB interfaces**, so a simplistic claim that all AEXs use only public PF/AEGP is false. Examples:
- `Roto Brush.aex`, `SVGImporter.aex`, `Character Palette.aex`, `AEGPDriver.aex`: direct BEE/TDB imports.
- `Paint Palette.aex`: BEE import but no direct TDB import.
- `Required/Paint.aex`: no direct BEE/TDB import; it uses the host-provided `Paint Suite`, previously proved to link to `AfterFXLib.dll!PaintEffectEntryPoint`.

However none of the installed AEXs directly import the **specific native Stream factory type-registration functions**. This observation is consistent with registration occurring in BEE's native startup, as previously proven by F-VECTOR-080.

### Limits of a direct-import result

It does NOT rule out `GetProcAddress`, OS dynamic loading, PE delayed imports (not parsed in this audit), a host-provided Suite function pointer, static-linked code, or a private partner SDK with a different ABI. Therefore no universal technical impossibility claim is made.

Additional AE2026 AEX ASCII-suite census found 328 distinctive printable suite-like literals, dominated by public `AEGP Stream Suite`, `AEGP Dynamic Stream Suite` and the `PF` suites. No direct ASCII `Native Stream Provider Suite` or `Native Layer Provider Suite` literal appeared in that scoped scan. A `BIBStreamFactoryInterface` UI string occurred in some built-in effects; its name is not an established native TDB creator extension interface.

### Cineware false lead

Bundled `Cineware_AE_SceneLayer.aex` has `EntryPointFunc` and Maxon/Cineware exports, with no **direct** BEE/TDB imports. Its filename is not evidence that Maxon added a new native `BEE_Layer` class. Adobe's Cineware documentation says that using a Cinema 4D footage layer automatically applies the Cineware effect to an ordinary composition layer:
https://helpx.adobe.com/jp/after-effects/desktop/work-with-other-applications/work-with-cinema-4d-and-cineware/c4d.html

### Offline source and dataset

- `experiments/vector-shape/probe-src/tools/verify_aex_native_registrar_imports_2025_2026.py`
- `datasets/ae-installed-aex-native-registry-direct-imports-2025-2026-aggregate.json`

PASS 481/481 and 633/633 import parses. No AE host code executed or modified. This does not satisfy `NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM` in F-VECTOR-088. Existing CNL C++ typed Timeline remains a separate nonhost-native engine.

## Engineering decision

Retain **external native class registration** as the primary missing proof gate. Even registering a class with the Adobe PRIVATE TDB native registry would not alone satisfy native parent canonical admissibility (F-VECTOR-084), host timeline ownership, archive, editing and lifecycle. Do not describe an experimental AEX returning success as a finished plug-in.
