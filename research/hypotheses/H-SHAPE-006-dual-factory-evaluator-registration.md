---
status: hypothesis
last_verified: 2026-10-11
evidence: H + E2-L + E2-X
---
# H-SHAPE-006 — CompNodeAE must cross separate TDB stream schema and BEE evaluator registries

## H-DUAL

A custom native vector stream created by an independent plugin might require registration **both** in TDB's `StreamFactory` and in BEE's `BEE_VectorStream::Operator` evaluator table, keyed by the identical `TDB_MatchName`. Counterhypothesis: even with both registrations, internal BEE VectorLayer class validation, serializer and allowed operator registry scope may block foreign types entirely.

Testable E2-L anchor: The BEE evaluator registry contains 20 native Shape/Graphic/Filter/Group names and 20 concrete RTTI operator classes, while TDB uses separate creator callbacks. The actual AE2026 AEGP invoked only a **getter**, not either registrar.

## H-OWNER

A plugin-owned Effects/Effect Parade instance is not a `BEE_VectorLayer`. A registered TDB + BEE evaluator may still be fundamentally tied to an existing native Shape Layer's owner, failing the requirement of an **effect that is itself a native editable shape**. Success must produce its own regular Timeline indexed hierarchy with stable native selection, no separate Shape Layer.

## H-EDIT

Even if VectorArt is materialized, native Pen tool handles and vertices require `TDB_StreamIDPath` identity, `OriginInfo` mapping, selection hit testing, commands, Undo/Redo, and supported host tool integration. Merely using a custom overlay does not qualify.

## H-LIFECYCLE

TDB registration eagerly invokes the creator, canonical/separated dimension registration. BEE evaluator registration stores an owning polymorphic operator. A plugin unloading before host-owned callbacks die may leave dangling vtables. Third-party ABI and lifetimes are unknown.

## Controlled discriminators

1. Cross-version static recovery of base class RTTI, calling convention, virtual `+0x18` semantics, creator/canonical lifecycle and private global registration order — evidence can be collected without modifying AE.
2. Read-only AE host shape topology and SVG/native path selection changes using existing AEGP, with separate session/undo fixtures; no mock native stream additions.
3. Only after precise ownership contracts, disposable isolated host and rollback: test reversible registration; observe immediate creator invocation, canonical values and cleanup.
4. Independent Timeline and Pen selection test **without** a native Shape Layer, and VectorArt/RG handoff test; these are different milestones and cannot be inferred from earlier stages.

No private registration operation currently exists in the active `ShapeLayerAE` AEX. Do not call `AEGP_AddStream` with unregistered unknown names despite observed CanAdd=true.
