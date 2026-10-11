---
status: pass-static-two-native-versions
last_verified: 2026-10-12
evidence: E2-L
---

# EXP-SHAPE-036 — Recover native BEE layer-kind dispatcher

The goal is to determine whether registering a new TDB Stream implicitly enables a third-party native Layer kind. Static analysis of both installed BEE.dll builds extracts BEE_Layer::CreateLayerFromType, its x64 integer range check (<= 7), the actual eight-way image-relative jump table, and every direct native concrete Layer constructor.

In BOTH AE2025/2026 the exact cases are: 0 AV, 1 Light, 2 Camera, 3 Text, 4 Vector, 5 Model, 6 AV (shared branch), 7 ParametricMesh. AE2025 includes a beta flag call for ParametricMesh in the examined function. No generic third-party class creator is invoked in this factory. This is scoped negative evidence for this factory, not global disproof of every possible extension boundary.

Cross-check: ShapeLayerAE/tools/audit_native_layer_factory_type_dispatch.py, decode_native_layer_factory_jump_table.py, verify_native_layer_factory_closed_switch.py. JSON evidence in AEIG datasets/ae-native-layer-factory-*. Result PASS offline; no AEX/private host code executed. See F-VECTOR-037.
