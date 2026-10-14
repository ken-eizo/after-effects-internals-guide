---
status: architecture-reference
last_verified: 2026-10-14
evidence: E0-H + E2-L + E2-X + H
versions: Windows AE2025/2026; SDK25.6
---

# Native Property Ownership, Timeline Editor and Rendering

**Registering a Stream class is not the same as creating a new AE Layer, editable Timeline item or native renderer operator.** This distinction is essential when interpreting internal C++ exports and controlled prototypes.

## Four separate hosts/owners

| Boundary | Concrete implementation | What it owns/does | Evidence |
| --- | --- | --- | --- |
| Type registry | `TDB_StreamFactory` | MatchNames, Creators, canonical prototypes | F-VECTOR-095/096, E2-L |
| Document owner | `BEE_Layer`, `BEE_CompItem`, `BEE_LayerSet` and Effect owners | Real layer attachment and document instance lifetime | F-VECTOR-055/067/071, E2-L |
| Editor/command path | `BEE_StreamSpec`, `TDB_StreamIDPath`, native Task/Undo/UI | Selection, property mutations, editor interaction | F-VECTOR-056–059, E2-L |
| Render/evaluation path | BEE evaluator registries, `BEE_VectorArt`, AGM/RG | Vector operators, geometry, drawing, rendering, cache | F-VECTOR-062 and evaluator research, E2-L |

These objects are connected but **not interchangeable**. A CNL C++ document with its own Undo/archive may exist independently, yet is not an Adobe-host native document if it does not enter these systems.

## Native Layer creation and CompItem attachment

The built-in Shape Layer uses Adobe's fixed layer-kind **4** route:

```text
BEE_NewLayerTask<4>
 → BEE_Layer::CreateLayerFromType(4, parent BEE_CompItem, ...)
 → BEE_CompItem::AttachLayerToCompOnly
 → host layer collection, Timeline selection, native Stream hierarchy
```

The C++ private factory Creator `BEE_VectorLayer::Create` can produce a **detached** `BEE_VectorLayer` with null CompItem, whereas the real built-in type-4 path is passed the actual owning CompItem. The latter must perform native bookkeeping, IDs, vtable calls, project dirty state and Undo.

The analyzed `AttachLayerToCompOnly` contains multiple virtual dispatches and version-dependent fields. One observed Layer offset changes from `+0x2D8` (2025) to `+0x26C` (2026), and another virtual slot from `+0x550` to `+0x560`. It is unsafe to assume a third-party invented `BEE_Layer` matches either layout without a complete ABI contract. See F-VECTOR-070/071.

## Timeline presentation and native editing

Timeline presentation requires a **real host document instance** with a permitted parent-child path. It also requires host bindings for property selection, displayed widgets, edit input, path tools, Undo and cache invalidation. `TDB_StreamGroup::SetUILayout` configures a canonical group list — it does **not** grant a general-purpose public UI widget registration API.

Examples of existing editor families:

- Paint: Brush tool edits special Paint Atom/Shape/Properties with internal Paint suite.
- Text: Animator, Selector and per-character properties.
- Shape: Contents, Path/Rectangle/Ellipse, Filters, Pen/Selection and path provenance.

A custom `PF_ADD_TOPIC`, effect parameter, Drawbot panel, pseudo-effect or separate C++ timeline cannot be counted as this host-native editing surface.

## Rendering and vector operator registry

The native vector graph is not merely a flat list of typed properties:

```text
BEE_VectorStream and time-evaluated TDB properties
 → BEE native evaluator registry by vector operator kind
 → BEE_VectorStream::PopulateVectorArt
 → BEE_VectorArt groups / paths / graphic filters
 → vector bounds / transforms / origin info
 → BEE_VectorLayer::Rasterize2DGraph
 → AGM / render graph / cache output
```

The independent BEE evaluator registry covers 20 recognized built-in operator families in the inspected versions (see [Native Vector Evaluator Registry](../../vector-shape-system/native-vector-evaluator-registry.md)). A new MatchName passing Shape Contents' prefix predicate still lacks evaluator dispatch if no corresponding native operator exists.

An effect raster output `PF_World` or Drawbot overlay is **not** a native `BEE_VectorArt` provider. Use the `BEE_VectorArt::OriginInfo` evidence to distinguish native source geometry identity from raster pixels (F-VECTOR-062 and subsequent native vector findings).

## Persistence, render snapshots and lifetime

A host Layer may have document-authored Stream objects, time-evaluated values, cloned/render-scoped snapshot state and old Undo history. A factory `UnregisterFactoryFunc` can remove its **canonical prototype**, but this does not independently prove every document/render/editor instance is already destroyed. Host D3D/AGM/RG execution and asynchronous requests introduce additional retention.

For a foreign class, qualifying safe unload requires verifying:
- all native child instances destroyed, including Undo/Redo and closed/open project state;
- no outstanding frame/evaluator callbacks or serializing Clones;
- no host application resource pointing to the external vtable or Creator;
- correct per-version Windows and macOS ABI, allocator and load/unload order.

## Acceptance criteria for a new CNL native property vs Layer

| Requirement | New native property/group | New native Layer family |
| --- | --- | --- |
| Private/public approved Stream Creator | Necessary | Necessary |
| Canonical schema / parent admission | Necessary | Necessary |
| Document-owned instance / StreamIDPath | Necessary | Necessary |
| AE standard Timeline and native edit controls | Necessary | Necessary |
| Keyframes, Undo, AEP save/reopen | Necessary | Necessary |
| Distinct BEE Layer constructor and CompItem admission | Depends on intended owner | **Necessary** |
| VectorArt evaluator and geometry rendering | If custom vector operator | If custom vector Layer |
| Unload, ABI and cross-version stability | Necessary | Necessary |

**Current evidence result: `NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM`.** None of these gates is satisfied end-to-end for an externally authored new CNL property or Layer. Prior CNL mock/independent engine tests remain valuable but are separate from actual AE acceptance.

## Related chapters

- [Registration and lifetime](factory-registration-lifetime.md)
- [Group admission](canonical-groups-admission.md)
- [Property operations](property-operations.md)
- [Native Vector Output and Ownership](../../vector-shape-system/native-vector-output-ownership.md)
- [Real native Layer admission](../../vector-shape-system/independent-native-layer-provider-admission.md)

Evidence: F-VECTOR-037/055–059/062–071/079/095/096. All private host internals referenced here are Windows x64 observations, not supported API declarations.
