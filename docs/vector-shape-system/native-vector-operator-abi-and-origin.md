---
status: research-active
last_verified: 2026-10-11
evidence: E2-L + H
versions: locally installed AE2025 / AE2026 BEE.dll, TDB.dll
---
# Native Vector Operator ABI, Editable Origins and the Effect-Owned Geometry Frontier

## Why this is a new frontier

CompNodeAE must be a **native-editable vector producer while remaining an effect plug-in**, without relying on a Shape Layer output. This cannot be established by raster effect output, PF_Path masks, script-created shape layers or a Custom UI overlay. The goal is not merely to use a Bezier library, but to register geometry, lifetime, timeline hierarchy, native Pen editing and host rendering **as one AE-native feature**.

The AE2025/AE2026 analyses distinguish four independent layers of contract:

1. **Creation/serialization** — host TDB stream type factory; canonical instantiation and saved stream identity.
2. **Native evaluation** — host BEE name-keyed evaluator registry, with 20 built-in reference-counted C++ objects.
3. **Editable provenance** — authored `TDB_StreamIDPath` and derived `BEE_VectorArt::OriginInfo`, including synthetic Repeater identifiers.
4. **Presentation and ownership** — `BEE_VectorLayer` host layer, ordinary Timeline native properties, selection/Tool subsystem and BEE/AGM/RG draw pipeline.

Registering into layer #2 alone cannot make a foreign effect a native shape layer; TDB data and ownership may also be required, and any actual foreign registration remains untested.

## ABI: the vtable split observed in **both** versions

Native evaluator `Operator` objects are polymorphic. Their vtable has two distinct physical subobject views, starting at object offsets 0 and 24 bytes. A static class-hierarchy RTTI audit recovers the native `RefCountedObject`, `RefCountedInterface` (virtual-base descriptor), `RefCountedImplementation`, `BEE_VectorStream::Operator`, derived `FilterOperator`, and seven `PathFilterOperatorT<Params>` subclasses.

The primary vtable's `+0x18` method is called by **both** normal and filter evaluation. Its second integer argument is literally `0` when normal `PopulateVectorArt` dispatch occurs, `1` for `StreamBasedFilter::DoFilter`. The mode gate was recovered from actual branches at all 20 operator entry points, in both installed builds:

| Operation family | Count | Method at primary vtable +0x18 | Concrete work function |
| --- | ---: | --- | --- |
| Group + Shape + Graphic | 9 | `test edx, edx`: accept mode 0, reject nonzero | dispatch to own vtable `+0x20` when requested |
| Vector Filters | 11 | `cmp edx, 1`: special filter path for mode 1 | dispatch via further vtable `+0x28` or common filter fallback |

This is reconstructed from **machine code**, not an official C++ ABI contract. Method input object types, exception model, temporal cache, matching version checks and ownership remain incompletely known. Do not attempt to define a third-party `Operator` class from this table alone.

For example, AE2026 concrete RVA landmarks:

- `RectOperator` primary slot3 `0x713ff0`: `test edx, edx` then `call [vftable+0x20]`.
- `FillOperator` slot3 `0x713bf0`: same mode0 gating and concrete call.
- `TrimOperator` slot3 `0x713980`: `cmp edx,1`, conditional `call [vftable+0x28]`.
- `RepeaterOperator` slot3 `0x714080`: same mode1 branch.
- `RepeaterOperator` primary slot5 `0x7156d0`: native filter implementation.

The addresses are valid **only for the exact local BEE.dll hash** recorded with the dataset; never hardcode as a portable interface.

## Native editable provenance: what actually generates it

We have now traced **actual** native operator functions in BEE.dll, not merely symbol names:

```text
 Authored Timeline TDB stream group
  ├─ Shape path: OM_Shape -> GetPathDataFromOM -> CAIMBezierPath
  ├─ Rectangle: GetRectPathData -> CAIMBezierPath
  └─ Ellipse: GetEllipsePathData -> CAIMBezierPath
                           |
                           v
                  BEE_VectorArt::Path
                           |
        OriginInfo(TDB_StreamIDPath) attached
                           |
                           v
            BEE_VectorArt::Group/children
                           |
                 AGM / render graph -> pixels
```

The 2025 and 2026 `ShapeOperator`, `RectOperator` and `EllipseOperator` concrete vtable methods **each** call an appropriate Bezier conversion function, `BEE_VectorArt::Path` constructor, `OriginInfo(TDB_StreamIDPath)`, and `SetOriginInfo`. Fill operator similarly attaches origin metadata; native Filter wrapper holds a `BEE_VectorLayer` and source path.

There is also a **direct proof for synthetic Repeater identity**. The 2026 `RepeaterOperator` native implementation `0x7156d0` calls `AppendSyntheticIndex()` at `0x7157f2` and `0x71581b`. In AE2025, corresponding calls at `0x6f13ea` and `0x6f1449` were found within `RepeaterOperator` `0x6f12c0`. Native group and `SymbolGroup` objects are created and origin information is attached inside the same call path.

This **promotes** the earlier hypothesis from F-VECTOR-005/F-VECTOR-006: `AppendSyntheticIndex` is indeed used in the concrete Repeater evaluation method. What is **not proven** is that synthetic paths can be edited independently with the Pen tool or that origin stamping alone is a general-purpose vector output plug-in interface.

## Implications for a true effect-native Shape feature

**Native stream factory + vector evaluator registry are necessary candidates, not sufficient.** An effect's `BEE_Effect`/Effect Parade is not the same owner type as `BEE_VectorLayer`. A fully independent CompNodeAE vector must still answer:

- Who creates/owns a `TDB_IndexedStreamGroup` or equivalent persistent Contents root underneath an effect?
- What does the host Timeline accept as a source of native path and group child identity, versus ordinary PF_ParamDef controls?
- Who registers the editable Bezier selection/hit-test target, converts `OriginInfo` to a `BEE_StreamSpec` and sends native Tool commands?
- How can an effect advertise a `BEE_VectorArt::Group` as its *render source*, rather than returning a bitmap `PF_World` in an effect selector?
- What releases the registrar's owned `Operator`, TDB canonical stream, code pointers and virtual base when project closes or a plug-in unloads?

No current public Effect SDK callback answers all of these, and no private third-party method has yet been safely exercised to provide them.

## Verification and next experiments

Two host-independent experiments were added:

**EXP-SHAPE-015:** enumerate all 20 native vtables, RTTI inheritance and mode dispatch in AE2025/2026; validate mode0=9 and mode1=11 in each version, without loading any private code.

**EXP-SHAPE-016:** trace concrete Path/Rectangle/Ellipse/Fill/Trim/Repeater operator callsites into Bezier paths, `BEE_VectorArt` and `OriginInfo`, including direct Repeater synthetic-index calls, in both binaries.

Future isolated-host experiments should first validate **read-only lifetime and identity invariants** after native selection and Undo. Only after completing the two separate registries' ABI and destructor semantics could reversible isolated registration be attempted. Normal working AE and installed ShapeLayerAE v3 remain unchanged.

## Findings, evidence and sources

An independent source-only consistency checker (`verify_native_vector_operator_evidence.py`) **passed** on the preserved 2025/2026 evidence: 20/20 names and concrete RTTI types agree, all 20 classes have both vtables, the 9/11 mode split holds, Path/Rect/Ellipse contain geometry-plus-origin call chains, and Repeater directly invokes `AppendSyntheticIndex` twice or more. Its JSON receipt is `datasets/ae-vector-operator-independent-crosscheck-2025-2026.json`. This is an E2-L artifact consistency check, not an AE host success claim.

- `research/findings/F-VECTOR-015-native-operator-vtables-inheritance-and-mode-abi.md`
- `research/findings/F-VECTOR-016-native-vectorart-origin-provenance-created-in-operators.md`
- `datasets/ae-vector-evaluator-vtable-slot-map-2025-2026.json`
- `datasets/ae-vector-evaluator-mode-abi-2025-2026.json`
- `datasets/ae-native-vector-operator-rtti-inheritance-2025-2026.json`
- `datasets/ae-vector-operator-vectorart-provenance-calls-2025-2026.json`
- `experiments/vector-shape/EXP-SHAPE-015-operator-mode-abi.md`
- `experiments/vector-shape/EXP-SHAPE-016-art-origin-stamping.md`

The official Adobe feature history places Shape Layers in **CS3 (2007)**; native editable vector mask facilities predate that. The emergence of editable SVG imports in 2025/2026 concerns conversion **into standard Shape Layers**, not an Effect SDK vector-return type. References: https://github.com/AdobeDocs/after-effects-feature-history and https://helpx.adobe.com/after-effects/desktop/import-files/import-svg-files/import-svg-files.html .
