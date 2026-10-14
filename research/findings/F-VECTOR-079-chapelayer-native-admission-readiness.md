---
date: 2026-10-14
status: PASS 9/9 baseline evidence checks; independent host-native Layer admission NOT DEMONSTRATED
evidence: E2-L pinned installed binaries, installed public SDK25.6, AE26.5 published SDK documentation, CNL CTest
---
# F-VECTOR-079 — Evidence-gated native ChapeLayer readiness and missing host provider contract

A repeatable machine gate now verifies the collected F-VECTOR-071 through F-VECTOR-078 static native evidence and the CNL core's 4/4 offline CTest, while refusing to translate those successes into a false claim that a new host-native BEE_Layer is registered.

Entry point: `experiments/vector-shape/probe-src/tools/verify_chapelayer_native_host_readiness.py`

Output: `datasets/chapelayer-native-host-admission-readiness.json`

Current result: **9/9 checks PASS**, compiled CNL AEX exists, but `independent_chapelayer_product_complete=false` and `decision=NOT_DEMONSTRATED_HOST_NATIVE_LAYER_ADMISSION`.

An exhaustive global non-existence proof is not claimed. The inspected public AEGP25.6 Register Suite offers no custom BEE Layer class registration, the published 26.5 guide adds a built-in Parametric Mesh creator and updated Stream Suite but no documented third-party native Layer provider, and the inspected native bootstraps/lifecycle/module loader entrypoints do not supply an evidenced safe native Layer-provider contract.

Critical interpretation: success of a cross-DLL Mock C++ host, CNL typed animation runtime, private native disassembly or built-in Shape Layer creation does **not** satisfy a new Adobe-owned Layer kind.

See `docs/vector-shape-system/independent-native-layer-provider-admission.md` for complete product criteria, why a generic plugin factory cannot substitute for a BEE owner provider, and a hypothetical Adobe-supported API needed to unblock genuine implementation. No unsafe host execution.

Officially documented current capability references in the published developer guide:
- https://ae-plugins.docsforadobe.dev/intro/whats-new/
- https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/

The result is a bounded, reproducible engineering readiness verdict, not a completed plug-in and not a blanket claim that Adobe can never introduce native Layer extension APIs.
