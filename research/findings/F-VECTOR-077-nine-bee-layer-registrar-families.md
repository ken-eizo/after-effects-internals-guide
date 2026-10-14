---
date: 2026-10-14
status: PASS AE2025/2026 full named BEE built-in Layer-family startup/teardown direct-call audit
evidence: E2-L exact BEE.dll SHA, full dumpbin exports, PE unwind + Capstone instruction-boundary verified callsites
---
# F-VECTOR-077 — Nine native built-in Layer-family Stream registrars share BEE_Birth/BEE_Death

## Result

F-VECTOR-073 demonstrated `BEE_Birth -> common helper -> RegisterStreams` for four built-in families. The entire **audited named set** of native `BEE_*Layer::RegisterStreams` exports is now enumerated and linked to that helper in the installed AE2025 and AE2026 BEE.dll binaries.

For each version, **9 direct registration call edges and 9 teardown call edges** are verified, covering:

1. `BEE_Layer` (base family; teardown invokes `RegisterStreams(bool)` in the shutdown branch)
2. `BEE_AVLayer`
3. `BEE_MaterialOverrideLayer`
4. `BEE_TextLayer`
5. `BEE_VectorLayer`
6. `BEE_CameraLayer`
7. `BEE_LightLayer`
8. `BEE_ModelLayer`
9. `BEE_ParametricMeshLayer`

This is the set of **native BEE Stream-registration families in the audited common helper**, not a statement that all nine are independent, user-creatable visible LayerType enum values. In particular, `BEE_MaterialOverrideLayer` appearing here is not evidence of a ninth visible layer kind. Native `CreateLayerFromType` still has the closed eight-case dispatch established in F-VECTOR-037.

## Actual machine-call chain

| Branch | AE2025 | AE2026 |
| --- | --- | --- |
| `BEE_Birth` | `0x64A530` | `0x664F70` |
| Common stream-register helper | `0x36DD90` | `0x3787B0` |
| Common stream-teardown helper | `0x36DEF0` | `0x378910` |
| `BEE_Death` | `0x64B090` | `0x6659A0` |

The registration helper has explicit direct calls for the nine concrete families. Every family's native Stream registration is a built-in, statically authored call target. A corresponding shutdown branch calls the eight class-specific `UnregisterStreams` exports and the base `BEE_Layer::RegisterStreams(bool)`.

A direct-calls census of **these routines and this module** cannot exclude indirect dispatch, external modules or some separate unpublished registration mechanism. It does, however, establish that the observed native BEE bootstrap does **not** dynamically iterate a third-party Layer-provider table to call these nine documented built-in registration targets.

## Negative-result boundary, with important distinctions

The following are distinct and must never be conflated:

- An open **TDB Stream creator registry** exists internally (F-VECTOR-008).
- Built-in BEE Layer family Stream registration is performed during `BEE_Birth` and torn down during `BEE_Death` (this finding).
- Public AEGP offers constructors for **existing** Adobe Vector, Text, Light, Camera and other supported Layer types, not arbitrary new BEE subclasses (F-VECTOR-072).
- Independent native ChapeLayer requires an explicitly valid foreign **BEE_Layer subclass/provider**, its factory/attach/serialization/editor/render contracts and deterministic unload. That remains **not demonstrated**.

A native `RegisterStreams` export does not itself register a new BEE layer kind. Manually invoking Adobe-private registrars, patching DLL jump tables or substituting a built-in Shape/Effect carrier is not an acceptable finished plugin.

## Reproduction

- `experiments/vector-shape/probe-src/tools/audit_full_bee_layer_registrar_bootstrap.py`
- `experiments/vector-shape/probe-src/tools/verify_full_bee_layer_registrar_bootstrap.py`
- `datasets/ae-bee-full-layer-family-registration-bootstrap-2025-2026.json`
- `experiments/vector-shape/EXP-SHAPE-077-full-built-in-bee-registrars.md`
- `experiments/observatory/manifests/EXP-SHAPE-077.json`

Audit uses complete `dumpbin /exports` data, avoiding default `pefile` symbol-count truncation, and independently disassembles candidate native `call` instructions to exclude arbitrary matching operand bytes. SHA-pinned verifier passes AE2025 and AE2026, 2/2. All analysis was offline; no private API execution, Adobe file changes, unsafe AEX tests or CompNodeAE edits.
