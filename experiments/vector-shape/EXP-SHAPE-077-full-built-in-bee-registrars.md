---
date: 2026-10-14
status: PASS 9 startup and 9 teardown direct-call checks in both pinned AE builds
---
# EXP-SHAPE-077 — Full built-in BEE native Layer Stream registrar bootstrap

Extend EXP-SHAPE-073's four-family direct-call audit to the full audited nine-family native BEE Stream set: base, AV, MaterialOverride, Text, Vector, Camera, Light, Model, ParametricMesh.

For both AE2025 and AE2026, locate all required full-export decorated `RegisterStreams` / `UnregisterStreams` symbols and verify each direct machine CALL from one common startup or shutdown helper using x64 unwind-bounded Capstone decoding.

Results: **9 registration and 9 teardown edges PASS per version**, **2/2 host versions PASS** with exact DLL SHA-256.

Do not mistake the number of stream-registration families for user-visible LayerType enum count. The result does not prove external native Layer registration.

Reproduce: `experiments/vector-shape/probe-src/tools/audit_full_bee_layer_registrar_bootstrap.py` followed by `verify_full_bee_layer_registrar_bootstrap.py`. Data: `datasets/ae-bee-full-layer-family-registration-bootstrap-2025-2026.json`.
