---
status: observed-static-only
last_verified: 2026-10-11
evidence: E2-L
versions: AE2025/AE2026 BEE.dll
---
# EXP-SHAPE-014 — BEE's second native vector evaluation registry, 20 MatchNames and concrete classes

Using locally installed AE2025 and AE2026 BEE.dll, reconstruct the chain:
(1) `PopulateVectorArt` and `StreamBasedFilter::DoFilter` dispatch to one global MatchName-keyed evaluator map;
(2) a separate private `BEE` registrar adds polymorphic evaluator objects;
(3) native initialization registers 20 evaluator objects;
(4) each object's name and concrete C++ RTTI can be derived from its callsite and vtable metadata.

Both versions expose **20** evaluator registrar CALL sites. Their `TDB_MatchName` constructor literals are identical across versions (11 filters, 1 group, 4 shapes, 4 graphics). All 20 callsite-associated concrete `BEE_VectorStream::*Operator` classes agree between versions. Native rendering dispatch calls evaluator vtable +0x18 with mode 0 for ordinary geometry and mode 1 for vector filters (two distinct code paths). Multiple vftables and the `PathFilterOperatorT<Params>` hierarchy are observed RTTI details, not supported third-party interface contracts.

The static data shows internal Adobe architecture, **not** an externally registrable plugin ABI or a live CompNodeAE vector emitter. No third-party creator or operator class was registered or invoked, no AE host process state changed.

Datasets: `ae-vector-stream-populate-dispatch-2025-2026.json`, `ae-native-vector-populate-recursive-helpers-2025-2026.json`, `ae-vector-evaluator-registry-xrefs-2025-2026.json`, `ae-native-vector-evaluator-registry-lifecycle-2025-2026.json`, `ae-native-vector-evaluator-registration-records-2025-2026.json`, `ae-vector-evaluator-matchname-xrefs-2025.json`, `ae-vector-evaluator-matchname-xrefs-2026.json`, `ae-vector-evaluator-matchname-identities-2025-2026.json`, `ae-native-vector-evaluator-vtable-rtti-2025-2026.json`.

Findings: `F-VECTOR-014-dual-native-vector-evaluator-registry.md`. Working scripts: `experiments/vector-shape/probe-src/tools`. Hypothesis and dependency contracts: `H-SHAPE-006-dual-factory-evaluator-registration.md`.
