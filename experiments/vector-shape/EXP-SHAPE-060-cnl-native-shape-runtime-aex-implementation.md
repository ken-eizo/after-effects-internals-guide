---
date: 2026-10-12
status: PASS compiled native AEGP + independent ABI/Undo/vector C++ QA, host-BEE-ownership incomplete
evidence: E2-L two MSVC x64 builds, CTest, PE imports/exports/PiPL
---

# EXP-SHAPE-060 — Independent CNL-native Shape runtime compiled into actual AEX

**Created the code**, not merely a plan, as a new C++ AE AEGP module
`CNLNativeShapeLayer.aex`. Contains an independently CNL-owned hierarchical
Contents root/Group/Path scene with stable IDs, Bezier handles, procedural
ellipses, per-document Undo/Redo, archive roundtrip and SVG vector renderer.
It is NOT a PF effect, Mask, or existing Adobe Shape Layer carrier.

Canonical source:
`D:/Developer/ShapeLayerAE/labs/native_shape_layer_prototype`.
Rebuildable AEIG snapshot:
`experiments/vector-shape/probe-src/labs/native_shape_layer_prototype` +
`experiments/vector-shape/probe-src/labs/native_vector_core` and
the already checked-in `experiments/vector-shape/probe-src/tools/build_pipl.py`.

Local **CNLNativeShapeLayer.aex**, 82,432 bytes, with public AEGP entrypoint
and native C-ABI methods. After a small memory lifetime correction, original
built SHA256 `f0b21da851aea656aff3434b9d2d45a166188ba3e93b53aa4400474f11d273c7`.

Independent AEIG snapshot MSVC x64 build SHA256
`ef40680fc67e7484acb15a55903be3a7816f38772777da3937df45dd7127d15e`.
**Both 1/1 CTest PASS**, PE static verification PASS for original:
correct PiPL, EntryPointFunc, 37 native C ABI exports,
zero BEE/TDB/FLT DLL imports.

The AEGP Animation menu command (if the user manually tests it in a disposable
AE2026 environment) runs a CNL-only self-test and emits
`%TEMP%/CNL_NativeShapeLayer_Prototype.tsv` and `.svg`;
no project modification, private host registration or host-owned Shape.
This AEX has not been installed/tested in AE. No claim of true Adobe
Timeline-native Shape Layer or Pen/BEE_VectorArt is made.

An explicit versioned `CNL_ShapeFeatures` struct marks all host-native
bridges false. The next phase is a separate Adobe TDB/BEE host adapter, with
complete registration, teardown, per-version ABI checks, indexed native
Contents, selection/Undo and VectorArt. Full analysis in F-VECTOR-060.

**No `CompNodeAE` changes, AE GUI operations or private host calls.**
