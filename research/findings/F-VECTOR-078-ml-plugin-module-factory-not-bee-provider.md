---
date: 2026-10-14
status: PASS pinned AE2025/AE2026 PluginSupport module factory ABI classification
evidence: E2-L exported decorated signatures, exact SHA-256, imported module census
---
# F-VECTOR-078 — PluginSupport RegisterPluginModuleFactory is an ML plugin-loader registry, not a demonstrated BEE Layer provider

## Why test this alternative?

Previous findings showed that built-in native BEE Layer/AV/Text/Vector/Camera/Light/Model/Parametric Mesh Stream families register during BEE startup. Yet `PluginSupport.dll` exports a function named `RegisterPluginModuleFactory`. Could this be a supported path for a foreign subclass of `BEE_Layer`?

## Evidence on installed AE2025 and AE2026

Both versions export a decorated C++ signature corresponding to a function under the **ML** namespace:

```cpp
ML::RegisterPluginModuleFactory(
    const dvacore::utility::Guid&,
    dvacore::classref::InterfaceRef<ML::UIPluginModuleFactory>
);
```

That signature concerns a GUID and an `ML::UIPluginModuleFactory` interface, **not** a `BEE_Layer` class factory callback, a TDB MatchName/type creator, a BEE VectorArt operator or the AE host Timeline editor.

In the inspected two `PluginSupport.dll` PE import tables, neither `BEE.dll` nor `TDB.dll` is directly imported. Other relevant exports include `PluginLoaderRegistry` and `FindPluginFactoriesForModule`. This is consistent with a distinct generic module-loader service. Its existence alone does not establish a BEE owner-subclass contract.

| Property | AE 2025 | AE 2026 |
| --- | ---: | ---: |
| Full module exports | 260 | 259 |
| `RegisterPluginModuleFactory` RVA | `0x3BEC0` | `0x41BD0` |
| Export uses `UIPluginModuleFactory` | Yes | Yes |
| Direct PE imports BEE/TDB | None | None |

## Bounds

**Not demonstrated**: a plugin registered with this ML service creating a new native AE `BEE_Layer`, reaching the closed native Layer constructor dispatcher, being admitted to BEE_CompItem, exposing native Timeline Contents, persisting in `.aep`, using the native renderer, or surviving teardown.

**Not globally excluded**: dynamic loads, other modules, indirect calls or an undocumented bridge between ML plugin factories and BEE owners. The absence of BEE/TDB *direct imports in this DLL* is not proof of a general impossibility.

Therefore the ML factory export is **not an evidenced solution** to ChapeLayer's missing external native owner registration. Invoking a private registration API is unwarranted without an actual Layer provider contract.

## Reproduce

- `experiments/vector-shape/probe-src/tools/verify_pluginsupport_factory_not_bee_owner.py`
- `datasets/ae-pluginsupport-ml-plugin-factory-vs-bee-layer-2025-2026.json`
- `experiments/vector-shape/EXP-SHAPE-078-ml-plugin-module-factory.md`
- `experiments/observatory/manifests/EXP-SHAPE-078.json`

Exact SHA-gated files and full exports checked, **2/2 PASS**. No Adobe code executed, no host registration or patch, no CompNodeAE changes.

## Current decision boundary

A native custom `BEE_Layer` requires a host-defined, ABI-stable `register_layer_provider` equivalent with constructor/clone/owner lifecycle and editor/renderer/serializer support. No such contract has yet been found in the inspected public AEGP SDK or these audited Adobe-private native bootstraps and plugin-loader signatures. The investigation should be described as a *bounded unsuccessful provider search*, not a proof that Adobe can never implement such an extension.
