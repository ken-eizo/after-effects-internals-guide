---
status: observed-static-only
last_verified: 2026-10-11
evidence: E2-L
versions: installed AE2025 / AE2026 BEE.dll
---
# EXP-SHAPE-015 — Concrete native vector operator vtables, RTTI inheritance and evaluation-mode split

## Question

Does `BEE_VectorStream::Operator` use a common virtual evaluation entry point, and if so, do native Geometry/Fill and Filter nodes implement distinct modes behind it?

## Method

Load **only local DLL bytes**, identify all 20 exact operator class instances from their registration callsites and MSVC RTTI, enumerate their primary and secondary vtables from PE `.rdata`, and decode the `+0x18` entry instructions. Independently parse C++ RTTI CompleteObjectLocator, ClassHierarchyDescriptor and BaseClassDescriptor for each exact concrete type in AE2025 and AE2026. No host interaction or AE process memory reads/writes.

## Measured results

- Both versions: **20 concrete operator classes**, each with primary object vtable at 0 and secondary at +24 bytes.
- Both versions: every operator has an own `+0x18` native-mode dispatch method.
- Both versions: **9 geometry/graphic/group** operators branch on `test edx,edx`, compatible with mode 0; **11 filter** operators branch on `cmp edx,1`, compatible with mode 1.
- Concrete normal modes delegate to the vtable `+0x20` method; filter mode has further `+0x28` callback path/common filter fallback.
- Base RTTI includes `BEE_VectorStream::Operator` and a dvacore reference-counted family. Seven path filter variants include `PathFilterOperatorT<Params>` between the concrete type and `FilterOperator`.
- Both ordinary `PopulateVectorArt` and `StreamBasedFilter::DoFilter` call this native `+0x18` virtual slot with distinct mode values (from EXP-SHAPE-014).

## Negative control

Neither DLL exposes a supported Effect SDK interface to register an external `BEE_VectorStream::Operator`. C++ structure/allocator/lifetime/ownership is incomplete. No private method or C++ evaluator was executed in AE, and no operator was registered from ShapeLayerAE.

## Reproduce

`tools/audit_vector_evaluator_slots.py`,
`tools/audit_vector_evaluator_virtual_call.py`,
`tools/audit_vector_eval_mode_bridge.py`,
`tools/audit_vector_evaluator_mode_abi.py`,
`tools/audit_vector_operator_inheritance.py`.

Results in AEIG `datasets/ae-vector-evaluator-vtable-slot-map-2025-2026.json`, `ae-vector-evaluator-mode-abi-2025-2026.json`, `ae-native-vector-operator-rtti-inheritance-2025-2026.json`. Caveat: `ae-native-vector-evaluator-virtual-evaluation-2025-2026.json` only records each first `.pdata` segment; use the fixed-window mode script for cold-code dispatch.
