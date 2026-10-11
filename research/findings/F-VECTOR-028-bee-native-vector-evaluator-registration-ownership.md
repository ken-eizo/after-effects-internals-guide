---
status: strongly-supported-static
last_verified: 2026-10-12
evidence: E2-L
versions: pinned installed AE2025 and AE2026 BEE.dll
---

# F-VECTOR-028 — BEE's separate geometry evaluator registry retains polymorphic operators

## Scope

A new native TDB Stream object is not a native vector-evaluator output. AE has a separate private BEE registry mapping a TDB MatchName to a C++ polymorphic geometry operator object; this structure already supports its 20 built-in Shape/Filter/Graphic operators. The goal of this experiment is to decode external lifetime blockers without creating or using a Mask or built-in Shape.

## Newly verified in two native runtimes

The BEE private registrar at RVA 0x6eeb20 (AE2025) and 0x713120 (AE2026) traverses a MatchName-keyed tree, checks duplicates, clones/moves the key into a newly stored native entry, and calls virtual functions on the operator pointer (slot +0x0 and +0x8 are visible in the registration routine). Operator destructor and refcount details are represented by the existing RefCountedObject/RefCountedInterface/RefCountedImplementation RTTI hierarchy (F-VECTOR-015), but the two calls alone do NOT prove which virtual offset is AddRef vs Release. The registry accessor and lookup routines are independently present and reference the same singleton.

The registrar itself is an internal BEE routine at those executable RVAs, not a public Effect SDK or AEGP registration suite. A matching native TDB type registration does not automatically insert an evaluator into this registry. The registry's ordinary lookup path is driven by the native Shape VectorLayer evaluation and filter chain, not by arbitrary PF_World effect frames.

| Path | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| BEE native evaluator registrar | 0x6eeb20 | 0x713120 |
| BEE evaluator registry initializer | 0x6eef40 | 0x713550 |
| lookup by MatchName | 0x6f9020 | 0x71cc00 |
| accessor | 0x6f87e0 | 0x71c2f0 |

The old F-VECTOR-014/015 evidence also shows all 20 native evaluators have a primary virtual dispatch and a secondary reference-counting polymorphic view with RTTI subobject offset +24, and separate native evaluation modes 0 and 1. Those facts restrict any third-party callback object design.

## What is and is not known about cleanup

The existing static registry-lifecycle corpus shows BEE-owned startup/shutdown allocation and object release traversal. This new bounded analysis verifies registration and lookup callback sites in both versions but does not reconstruct a safely callable third-party unregister method for this BEE table. No externally supported unregister API was found or tested. If a plugin code module is unloaded while host-owned operator vtables remain registered, dangling code pointers may result.

An external registry-write experiment must be gated on an exact binary hash, pointer layout, complete reference-counted class ABI, timing and rollback. The existence of an internal registrar alone is not permission or evidence that late third-party insertion is supported. No private registrar was invoked in the active AE host.

## Native vector renderer remains a third distinct boundary

AE2025/AE2026 native BEE_VectorLayer::Rasterize2DGraph lives at a class-specific vtable entry (F-VECTOR-025). Even if the TDB source and BEE evaluator registries accepted a third-party pair, an ordinary Effect would still need a legitimate host-native owner and VectorArt-to-RG output path. Therefore successful pair registration by itself is not the promised new native vector effect.

## Reproducibility

- datasets/ae-bee-evaluator-register-shutdown-callback-abi-2025-2026.json
- datasets/ae-native-vector-owner-serialization-gates-2025-2026.json
- experiments/vector-shape/probe-src/tools/audit_bee_evaluator_registration_teardown.py
- experiments/vector-shape/probe-src/tools/verify_native_vector_clone_io_bee_abi.py
- F-VECTOR-014/015/025.

No Adobe binary copied to this repository, no memory hook or injection, no AE GUI operation. E2-L only.

## Future product potential

A safely extensible BEE evaluator registry would permit new native CNL geometry operators — procedural paths, field-driven curves, boolean/offset operations — as first-class evaluated vector entities. AE native Contents, Pen tool selection and true native rendering additionally require the host to accept an independently owned vector provider.
