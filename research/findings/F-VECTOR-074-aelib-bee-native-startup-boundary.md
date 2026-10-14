---
date: 2026-10-14
status: PASS pinned AE2025/2026 native aelib-to-BEE birth/death IAT direct calls
evidence: E2-L local aelib.dll PE import tables, exact RIP-relative IAT CALL and x64 .pdata disassembly, SHA-256
---
# F-VECTOR-074 — Adobe aelib.dll drives native BEE startup and teardown before built-in stream registration

## Cross-module finding

F-VECTOR-073 linked `BEE_Birth` and `BEE_Death` to the native Adobe BEE Layer/AV/Text/Vector stream type register/unregister helpers. The caller on the other side of that BEE module boundary is now recovered from **both installed Adobe versions**.

`aelib.dll` directly imports the two decorated `BEE.dll` exports and contains instruction-boundary-verified RIP-relative imported-function `call` operations at TWO native `BEE_Birth` callsites and ONE native `BEE_Death` callsite in each version.

| Evidence | AE2025 | AE2026 |
| --- | --- | --- |
| Importing module | `aelib.dll` | `aelib.dll` |
| Imported BEE startup symbol | `?BEE_Birth@@...` | `?BEE_Birth@@...` |
| BEE_Birth IAT VA | `0x18010E770` | `0x180126758` |
| First Birth CALL RVA | `0x6E272` | `0x70647` |
| Second Birth CALL RVA | `0x6F6CF` | `0x71BC8` |
| Birth caller function RVAs | `0x6D9B0`, `0x6F550` | `0x6FD80`, `0x71A60` |
| BEE_Death IAT VA | `0x18010E768` | `0x180126750` |
| Death CALL RVA | `0x6EF56` | `0x712E6` |
| Death caller function RVA | `0x6EDC0` | `0x71150` |

The complete, now cross-module, native direct-call evidence chain is:

```text
aelib.dll --calls imported BEE_Birth--> BEE.dll
  --> shared built-in registration helper
    --> BEE_Layer::RegisterStreams
    --> BEE_AVLayer::RegisterStreams
    --> BEE_TextLayer::RegisterStreams
    --> BEE_VectorLayer::RegisterStreams

aelib.dll --calls imported BEE_Death--> BEE.dll
  --> shared built-in teardown helper
    --> BEE_Layer::RegisterStreams(bool)
    --> BEE_VectorLayer::UnregisterStreams
    --> BEE_TextLayer::UnregisterStreams
    --> BEE_AVLayer::UnregisterStreams
```

`AfterFX.exe`, `AfterFXLib.dll`, `Plugin.dll`, `PluginSupport.dll`, `ae_sweetpea.dll` and `aerender.exe` did not directly import `BEE.dll` in the **selective, top-level ten-module PE import audit**. That is only a module-import inventory result and NOT proof that these modules never load BEE dynamically, transitively or in a separate configuration.

## Why this matters to independent ChapeLayer

The built-in native layer type registration lifecycle is not merely an unscoped AEGP command registration. The exposed native entrypoints are internal module initialization/cleanup across the `aelib.dll` -> `BEE.dll` boundary. This supports the hypothesis that the four built-in registrars are embedded in host startup, not dynamically published as a third-party property-class provider.

**This does NOT establish that a separately callable, supported external registration route is impossible.** A true independent ChapeLayer needs explicit, guaranteed foreign class registration, type identity, clone, native attached owner, undo, project serializer, native editor/evaluator and deterministic unregister. The registered built-in handlers in F-VECTOR-073 do not provide that contract.

The two distinct `BEE_Birth` callsites should not be interpreted as two actual startup executions without runtime evidence (branches and run states have not been established here).

## Reproducible evidence

- `experiments/vector-shape/probe-src/tools/audit_aelib_bee_lifecycle_calls.py`
- `experiments/vector-shape/probe-src/tools/verify_aelib_bee_lifecycle_calls.py`
- `datasets/ae-aelib-bee-lifecycle-crossmodule-2025-2026.json`
- `experiments/vector-shape/EXP-SHAPE-074-aelib-bee-host-startup-boundary.md`
- `experiments/observatory/manifests/EXP-SHAPE-074.json`

The offline tests verify each locally installed aelib DLL SHA-256, the exact import symbols/IAT addresses and machine-instruction callsite membership in unwind functions. Verified both versions, 2/2 PASS. No Adobe DLL loaded or patched, no AEX host experiment, no other research tree modified.

## Follow-up technical boundary

Trace the incoming initialization calls into `aelib.dll` and distinguish genuinely configurable BEE boot arguments from native Adobe startup flags. Search independently for an authorized plugin-native owner registration service. An internal callable exported function is not itself a supported plugin ABI.
