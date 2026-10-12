---
date: 2026-10-12
status: PASS-two-version-offline-native-PE-reconstruction
evidence: E2-L BEE.dll PE exports / actual x64 code / DLL static MatchName constructors / TDB imports
---

# EXP-SHAPE-054 — Native Shape Contents complete Canonical hierarchy and 183 typed creator sites

## Reproduced results

Disassembled actual BEE.dll installed AE2025 and AE2026, pinning hashes. Called **no Adobe native code**. The initial vector RegisterStreams stage and three supporting typed factory registration functions contain respectively 62, 55, 47 and 19 `TDB_ScRegisterStreams::Register` callsites, totaling 183 **static sites**, not unconditional runtime counts. All 20 native BEE evaluator MatchName globals are represented among TDB typed creator registrations in both releases. A distinct BEE polymorphic evaluator registry initializes separately.

Cross-verified the three actual C++ virtual `FillInCanonicalUILayout` classes (`BEE_VectorLayer`, `VectorStreamGroup`, `VectorsStreamGroup`) by resolving imported `TDB_StreamBase::GetCanonicalStream` references and their RIP-relative native MatchName objects. Recovered all root/group child names via the original MatchName static constructor ASCII constant addresses:

- Shape native Layer: 10 canonical fields (AE2025), 11 (AE2026, adding `ADBE Layer Credential ID`).
- `ADBE Root Vectors Group`: four fields, exactly `ADBE Vector Blend Mode`, `ADBE Vectors Group`, `ADBE Vector Transform Group`, `ADBE Vector Materials Group`.
- `ADBE Vectors Group` (Contents): exactly 20 native child types, ordered 1 Group + 4 Shape + 4 Graphic + 11 Filter; same ordering across installed 2025/26.
- `ADBE Root Vectors Group` and `ADBE Vectors Group` share one `VectorsStreamGroup::Create` typed callback with distinct MatchName values; `ADBE Vector Group` uses `VectorStreamGroup::Create`. `BEE_VectorLayer::Create` itself is another registered typed owner callback.
- The `ADBE Vector Group` match identity is also the exact argument to `TDB_StreamFactory::SetupCanonicalStream` in both startup bodies.

Automated verifiers:
`verify_vector_layer_native_schema_bootstrap.py` PASS 2025/26,
`verify_native_vector_three_level_canonical_schema.py` PASS 2025/26,
`verify_native_shape_canonical_hierarchy_named.py` PASS 2025/26.

This resolves **native built-in internal schema and typed creator wiring**, NOT external plugin ownership, safe private registration, native Pen targeting or direct RG/AGM renderer support. The full independent CNL plugin-defined Shape Layer still requires an alternate owner dispatcher beyond the fixed `BEE_Layer::CreateLayerFromType` switch, or a new independently valid host owner type recognized by TDB+editor+renderer.

## Exact datasets

- `datasets/ae-bee-native-vector-registerstreams-three-phases-2025-2026.json`
- `datasets/ae-bee-native-vector-62-creators-2025-2026.json`
- `datasets/ae-bee-native-vector-183-register-calls-2025-2026.json`
- `datasets/ae-bee-native-vector-canonical-three-level-2025-2026.json`
- `datasets/ae-bee-native-vector-matchname-initializers-2025-2026.json`
- `datasets/ae-bee-native-vector-bootstrap-verified-2025-2026.json`
- `datasets/ae-bee-native-vector-three-level-verified-2025-2026.json`
- `datasets/ae-bee-native-vector-canonical-named-verified-2025-2026.json`

Verifier, parser and disassembler scripts mirror into `experiments/vector-shape/probe-src/tools/`. Full interpretation and negative gates F-VECTOR-054.

Neither `CompNodeAE` nor any active AE GUI/plugin install was operated. No private TDB registrars called. Phase F still prohibited.
