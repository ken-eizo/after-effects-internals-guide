---
status: architecture-reference
last_verified: 2026-10-14
evidence: E0-S + E2-L + E2-X + H
versions: AE2025/2026 Windows and actual AE2026 Paint fixture
---

# Native Paint, Text Animator and Shape Contents Hierarchies

These three user-facing features all appear as nested native properties in the **standard After Effects Timeline**. They share parts of the TDB/BEE Stream substrate, but their **owner, schema, parent admission, evaluator and editor differ**.

## Paint — brush-created effect, not Paint Bucket

The feature under examination is the **Paint effect AE creates when its Brush tool is used**. It is a real `Required/Paint.aex` (present in both AE2025 and AE2026). The unrelated Stylize effects Paint Bucket and Brush Strokes are not part of this system.

The real implementation spans two components:

- **AEX effect entry:** `Required/Paint.aex` requests the internal `Paint Suite`; `AfterFXLib.dll` publishes that suite's function-pointer table, including `PaintEffectEntryPoint`.
- **Native property grammar:** `BEE_AVLayer::RegisterStreams` registers `BEE_PaintAtom::Create`, `BEE_PaintEffect::Create`, `BEE_PaintProperties::Create`, `BEE_PaintTransform::Create`, `BEE_PaintStrokesGroup::Create` through `TDB_ScRegisterStreams::Register`.

The Paint AEX does **not** directly import TDB/BEE. Its file format and plugin type alone do not confer the private registration API on a third party. First-party `BEE_PaintAtom` exports `Read`, `Write`, `CloneStream` and `FillInCanonicalUILayout`.

### Real AE2026 native Paint tree

E2-X host-observed on one Brush-created Paint with one stroke:

```text
ADBE Paint (NAMED; Paint)
 ├─ ADBE Paint-0000
 ├─ ADBE Paint On Transparent
 ├─ ADBE Paint Group (INDEXED; Strokes)
 │   └─ ADBE Paint Atom (NAMED; Brush)
 │       ├─ ADBE Paint Transfer Mode
 │       ├─ ADBE Paint Duration
 │       ├─ ADBE Paint Shape (Path)
 │       ├─ ADBE Paint Properties (NAMED; Stroke Options)
 │       │   ├─ Start / End / Color / Diameter
 │       │   ├─ Angle / Hardness / Roundness / Spacing
 │       │   ├─ Channels / Opacity / Flow
 │       │   └─ Clone Source / Position / Time / Time Shift / Source Type
 │       ├─ ADBE Paint Transform (NAMED)
 │       │   └─ Anchor Point / Position / Scale / Rotation
 │       └─ ADBE Paint Nibbler Group (INDEXED)
 └─ ADBE Effect Built In Params
```

The captured fixture had 35 Stream nodes, zero API errors and no project mutation; a later user-run v2 with **six strokes** traversed 170 native nodes, 142 leaf metadata rows and 109 potentially time-varying leaves (F-VECTOR-083/087).

**Paint Path subtlety:** `ADBE Paint Shape` reports `AEGP_StreamType_NO_DATA` even though Adobe can edit it with a brush-specific internal path implementation. Avoid treating public `NO_DATA` as absence of native value.

**Parent grammar:** `ADBE Paint Group` admits `ADBE Paint Atom`; unknown `CNL:PaintAtom` was rejected. Adobe's own `Examples/AEGP/Streamie/Streamie.cpp` illustrates legal manipulations of existing native Paint Strokes, **not** registration of a new `BEE_PaintAtom` class.

Sources: F-VECTOR-080–087; `datasets/ae-paint-native-hierarchy-host-v2-2026-20261014.tsv`; `datasets/ae-paint-native-stream-registration-2025-2026.json`.

## Text Animator — native groups with distinct accepted members

Adobe's text system includes multiple typed groups, each having its own canonical child list. Native vtables from AE2025/2026 expose the same common `TDB_StreamGroup::CanStore` semantics but **different** `FillInCanonicalUILayout` implementations:

| Owner group | Representative canonical members | Native implementation |
| --- | --- | --- |
| Text Animator | Selectors and Animator Properties | `BEE_TextAnimatorStreamGroup` |
| Text Selectors | Range, Wiggly, Expressible and other Selector classes | `BEE_TextSelectorsStreamGroup` |
| Text Animator Properties | Position, Scale, Opacity and other per-character parameters | `BEE_TextAnimatorPropertiesStreamGroup` |

A native editor can expose per-character operations and selectors only if the host has the correct BEE Text owner and evaluation contract. Supplying a new arbitrary TDB class name does not mutate the canonical allowed child set.

The analyzed 2026 Text Animator group method is `BEE_TextAnimatorStreamGroup::FillInCanonicalUILayout` at RVA `0x5D5180`, and Text Selectors' implementation is RVA `0x5D57A0`. These are internal PE offsets, **not SDK APIs**. F-VECTOR-084 is the exact vtable/static callsite evidence.

## Shape Contents — ordered native vector operations

Built-in Shape Layers have a root/native Contents hierarchy:

```text
BEE_VectorLayer
 └─ ADBE Root Vectors Group
      └─ vector group / transformation and Contents groups
           └─ ADBE Vectors Group (INDEXED)
                ├─ ADBE Vector Group
                ├─ ADBE Vector Shape - ...
                ├─ ADBE Vector Graphic - ...
                └─ ADBE Vector Filter - ...
```

The analyzed `BEE_VectorStream::VectorsStreamGroup` canonical child list includes **20** named standard entries in both 2025/2026: Group, Bezier Path, Rectangle, Ellipse, Polystar, Fill, Stroke, Gradient Fill/Stroke and various Path filters (Trim, Merge, Offset, Round, Repeater, etc.). The canonical list is a type grammar, not proof that all operations can be applied anywhere in the hierarchy.

### Evaluator is separate from the Stream class

`BEE_VectorStream` and `TDB_Stream` own the property side, while the BEE native vector evaluator/operator registry builds geometry, graphics and filters into `BEE_VectorArt` for bounds, geometry provenance, AGM/RG rasterization and caching. F-VECTOR-062 shows **ascending indexed-child traversal**; final visual stacking/draw semantics must not be assumed identical to this raw iteration ordering.

Creating a Stream with a prefix such as `ADBE Vector Shape - CNLProbe` can satisfy this group's **CanStore preflight** but says nothing about Creator, evaluator, native pen editing or save/reopen (F-VECTOR-063/065). See [Vector evaluator registry](../../vector-shape-system/native-vector-evaluator-registry.md) and [Vector runtime](../../vector-shape-system/runtime-architecture.md).

## Comparison: why a general custom group is not automatic

| System | Where native types originate | Parent permits unknown `CNL:` child? | Native renderer/editor |
| --- | --- | --- | --- |
| Paint Strokes | BEE first-party Paint Stream provider + Paint Suite | **False** in tested AE2026 fixture | Host brush/editor/paint renderer |
| Text Animator | BEE first-party Text Stream provider | No generic permission demonstrated | Text selector/animator |
| Shape Contents | BEE Vector Stream provider | Bare `CNL:` false; synthetically prefixed name *preflight* can be true | VectorArt, Shape tools |
| Arbitrary new CNL Group | **No externally validated factory** | **Not established** | **Not established** |

The private typed Group factory, its canonical UILayout, host document owner, selection/edit tools, expression/keyframe state, AEP serialization, evaluator and unload safety must be proved **independently**. No custom foreign CNL hierarchy is currently accepted by Adobe's Timeline.

See [Canonical group rules](canonical-groups-admission.md), [Object model](stream-object-model.md) and [Owner/editor/renderer](owner-editor-renderer.md).
