---
date: 2026-10-14
status: PASS bounded PluginSupport ML module factory ABI test
---
# EXP-SHAPE-078 — Distinguish ML module factory from native BEE Layer factory

The installed AE2025 and AE2026 `PluginSupport.dll` modules each export `RegisterPluginModuleFactory`. The exact decorated signature accepts a dvacore GUID plus an interface reference to `ML::UIPluginModuleFactory`, and the PE import table has no direct `BEE.dll` or `TDB.dll` dependency.

The result supports identifying this as a generic **ML plugin-loader registry**, not an independently verified native AE `BEE_Layer` provider. It cannot establish the absence of dynamic coupling, external plugins or alternate host APIs.

Reproduce: `experiments/vector-shape/probe-src/tools/verify_pluginsupport_factory_not_bee_owner.py`. Full evidence JSON `datasets/ae-pluginsupport-ml-plugin-factory-vs-bee-layer-2025-2026.json`. **2/2 PASS**.

No native Adobe/private API invoked. No user AE project or CompNodeAE modified.
