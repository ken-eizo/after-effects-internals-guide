---
status: strongly-supported-static
last_verified: 2026-10-11
evidence: E2-L
versions: installed AE2025 + AE2026 BEE.dll
---
# F-VECTOR-015 — Native VectorArt operator polymorphic ABI: 20 vtables, RTTI inheritance and two evaluation modes

## Direct evidence

In both installed AE2025 and AE2026 BEE.dll binaries, all 20 registered `BEE_VectorStream::*Operator` concrete classes have a primary C++ vtable and a secondary vtable with MSVC RTTI complete-object-locator **subobject offset 24 bytes**. Direct `BEE_VectorStream` native evaluation calls the primary vtable offset `+0x18` (slot #3). This address is an **entry-point mode dispatcher**, not itself the whole geometry algorithm.

A bounded local PE analysis recovers each concrete primary and secondary vtable RVA and the real code pointers for slots 0–11, verifying the evaluation virtual slot via the `call [rax+0x18]` at `BEE.dll` AE2026 RVA `0x71111c` and filter use at `0x6f1654`. The apparent number of slots in a C++ vftable depends on the derived type; scanning must terminate at the next non-executable pointer, not blindly assume 12 methods.

All **20/20** operator mode dispatchers were classified from *literal branch instructions* in each installed host version:

| Category | Count | First branch at vtable +0x18 | Other call path |
| --- | ---: | --- | --- |
| Group, Shape (Path/Rect/Ellipse/Star), Graphic (Fill/Stroke/Gradient Fill/Gradient Stroke) | 9 | `test edx, edx` => branch if not mode 0 | calls the operator's other virtual slot `+0x20` on matching mode |
| Filter (Trim, Offset, Pucker-Bloat, Repeater, Reveal, Merge, Roughen, Wiggler, Zigzag, Round Corner, Twist) | 11 | `cmp edx, 1` => special behavior at mode 1 | uses a further filter-method virtual slot `+0x28` on matching mode, or a common dispatch fallback |

**Precise caveat:** `mode 0` and `mode 1` are observed integer values in two distinct native callsites, but not a named/stable external enum. `edx` register dispatch, indirect call offsets and stack setup were checked as machine instructions in both versions. Some functions have cold code outside their first `.pdata` entry. The bounded `ae-native-vector-evaluator-virtual-evaluation-2025-2026.json` dataset captures *hot function ranges only*; `audit_vector_eval_mode_bridge.py` and `ae-vector-evaluator-mode-abi-2025-2026.json` preserve full initial mode branches for both variants.

## MSVC RTTI inheritance: complete-object and virtual subobjects

The native RTTI CompleteObjectLocator -> ClassHierarchyDescriptor -> BaseClassArray -> BaseClassDescriptor layout was decoded in AE2025 and 2026, without loading Adobe functions. Each of the 20 operator classes has the same high-level native reference-counted base family:

```text
native BEE_VectorStream::Operator
  native reference-counting support:
    dvacore::utility::RefCountedObject
    dvacore::utility::RefCountedInterface (virtual-base PMD pdisp=16)
    dvacore::utility::RefCountedImplementation
  concrete variants:
    Shape/Rect/Ellipse/PolyStar/Group/Fill/Stroke/Gradient*
    FilterOperator
      ├─ PathFilterOperatorT<Params> (7 typed path filters)
      └─ Repeater/Reveal/Merge/Wiggler (4 direct filters)
```

The diagram is conceptual grouping, **not an ABI-safe C++ header or the sole linear class layout**. MSVC base-class descriptors distinguish virtual-base relationships, and `RefCountedInterface` is described by PMD `pdisp=16`. The observed second vftable at **object offset +24** proves that retaining reference-counted foreign C++ objects across plugin unloading and replacing them with a naive custom `struct` is unsafe.

## Why this matters for CompNodeAE

A complete custom operator must match host ABI for geometry evaluation and reference-counted lifetime. The TDB creator and the BEE evaluator are different registrations; even both being supplied would not by itself install an effect-owned native Timeline Content owner or Pen tool integration. A developer can use these RTTI/vtable facts to design an isolated, version-pinned ABI test harness, but should not register dummy pointers in a working After Effects process.

## Reproducible evidence

- `datasets/ae-vector-evaluator-vtable-slot-map-2025-2026.json`
- `datasets/ae-native-vector-evaluator-virtual-evaluation-2025-2026.json` (initial `.pdata` ranges only; not a full function reconstruction)
- `datasets/ae-vector-evaluator-mode-abi-2025-2026.json`
- `datasets/ae-native-vector-operator-rtti-inheritance-2025-2026.json`
- `experiments/vector-shape/probe-src/tools/audit_vector_evaluator_slots.py`
- `experiments/vector-shape/probe-src/tools/audit_vector_evaluator_virtual_call.py`
- `experiments/vector-shape/probe-src/tools/audit_vector_eval_mode_bridge.py`
- `experiments/vector-shape/probe-src/tools/audit_vector_evaluator_mode_abi.py`
- `experiments/vector-shape/probe-src/tools/audit_vector_operator_inheritance.py`

All source is from static locally installed Adobe DLLs, with source-only tools and JSON facts committed; no Adobe binaries are redistributed.

## Independent internal consistency gate

A separate source-only verifier (`experiments/vector-shape/probe-src/tools/verify_native_vector_operator_evidence.py`) validated the two-year evidence chain: all 20 unique MatchNames and concrete classes are aligned between data sets; both versions have 9/11 mode split and primary/secondary RTTI vtables; Path/Rectangle/Ellipse geometry-to-OriginInfo call sequences exist; Repeater's vtable slot5 has two or more direct `AppendSyntheticIndex` calls in each installed version. The command **passed** on the local evidence, with JSON receipt `datasets/ae-vector-operator-independent-crosscheck-2025-2026.json`. It verifies agreement among multiple static analyses, **not** an external AE plug-in integration or a live host behavior.
