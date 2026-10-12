---
date: 2026-10-12
status: compiled-independent-native-Shape-AEGP-runtime-PASS; AE-Timeline-native-owner-NOT-IMPLEMENTED
evidence: E2-L independently compiled Windows x64 AEGP + CTest/PE analysis
---

# F-VECTOR-060 — Compiled CNL native Shape runtime AEX: real C++ vector ownership, Undo and archive, no Adobe native owner yet

## Purpose

The end goal remains an **independently owned After Effects Shape Layer** with a
genuine Adobe Timeline Contents tree, native Pen editing, native Undo and
BEE_VectorArt/RenderGraph rendering. F-VECTOR-054–059 recovered the original
Adobe Shape internal chain. The immediate next step was **to actually compile
CNL's own native executable vector-owner implementation** rather than continuing
indefinite abstract analysis or adding a standard PF Effect.

## Delivered code and binary

A real C++ Windows x64 **AEGP AEX module** `CNLNativeShapeLayer.aex` has been
compiled successfully with MSVC and Adobe SDK 25.6. The plugin exports a public
AEGP `EntryPointFunc` and a **37-symbol stable CNL C ABI** with explicit
CNL-owned state. It contains **no PF Effect** and never creates an Adobe
Shape or Mask carrier.

Canonical source and local compiled AEX:

`D:\Developer\ShapeLayerAE\labs\native_shape_layer_prototype\`

`D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype\Release\CNLNativeShapeLayer.aex`

The implementation is also self-contained and independently rebuildable from
the archived source tree:

`experiments/vector-shape/probe-src/labs/native_shape_layer_prototype/`

`experiments/vector-shape/probe-src/labs/native_vector_core/`

Actual functionalities, not design claims:

- Independent native C++ Shape data owner with a `Contents` root, nested
  `Group`, `Path`, stable 64-bit node identity and cubic Bezier vertices.
- Creation of procedural ellipse as four cubic segments and direct editable
  in/out Bezier handles.
- CNL-owned Undo and Redo implementation, bounded at 64 snapshots;
  invalid edits preserve history, redo invalidates correctly after branch.
- Deterministic checksummed `CNLVEC01` binary save/archive and restore,
  including rejection of corrupted archives.
- **Mathematical SVG cubic-path renderer**, recursive grouped vector ordering,
  not pixel output, PF_World, a mask or baked Adobe Shape layer.
- Versioned `cnl_shape_features` ABI explicitly reports the four Adobe-native
  connection flags as **0**: TDB owner, Contents, Pen and VectorArt.

A safe Adobe Animation menu command in the AEX executes an independent
CNL-owned scene/Undo/archive self-test and writes a TSV and SVG into `%TEMP%`.
It is never automatically invoked at AEX initialization and does not modify
any AE Project. The plugin itself has NOT been installed or host-tested
during this session. Host startup compatibility is **not claimed**.

## Independent build/test evidence

Two separate MSVC builds:

1. Direct ShapeLayerAE source built to
   `build/native_shape_layer_prototype/Release/CNLNativeShapeLayer.aex`.
   SHA256 `f0b21da851aea656aff3434b9d2d45a166188ba3e93b53aa4400474f11d273c7`
   (after ownership exception-safety fix).
2. Archive-only AEIG source independently built to
   `build/native_shape_layer_prototype_archived_qa/Release/CNLNativeShapeLayer.aex`.
   SHA256 `ef40680fc67e7484acb15a55903be3a7816f38772777da3937df45dd7127d15e`.
   Different hashes are **not treated as reproducibility failures**;
   MSVC/PiPL/build paths may differ, but both binaries are compiled from
   the same source and both native C++ tests pass.

Both builds: **1/1 CTest PASS**, with fast complete test of nested group
construction, 90 editable/generated paths, mutation and undo branching,
bounded 64-step undo/redo, archive roundtrip with stable node IDs, corrupt
archive rejection and SVG vector output.

The PE verifier also PASSED the direct compiled AEX:
- Windows AMD64 PE, PiPL resource, `EntryPointFunc` export,
  **37 CNL C ABI exports**.
- No direct module imports of `BEE.dll`, `TDB.dll` or `FLT.dll`.
- No direct use of private BEE/TDB registration or any host Project-edit APIs
  in the test-menu command.
- No binary patches or AEX plugin installation performed.

## What this explicitly does NOT solve

Although a genuine compiled CNL vector owner and loadable-format AEX
**now exist**, they are **not the requested genuine Adobe-native Shape Layer**.
The CNL native scene is not a `BEE_Layer`, not an Adobe-registered
`TDB_StreamBase` subtype, cannot appear as its own Timeline Contents object,
does not receive AE Pen and Selection dispatch, and does not feed the
`BEE_VectorArt` render graph.

The documented AE plug-in SDK provides no verified public API for registering
a new `BEE_Layer` kind or native vector Contents producer. Prior analysis
F-VECTOR-037/054/058 confirms a closed eight-case layer creation switch and
separate TDB type factories, BEE evaluator and editor/owner contracts.
The old `CNLPrivateTDBDisposable.aex` remains **untested and unsafe**;
registration success, even if observed later, would not establish safe
project-owning CNL Layer/Undo/Pen/VectorArt.

## Strict next native host integration

1. Define a CNL-owned TDB `StreamBase` ABI/vtable/allocator compatible
   wrapper and prove its complete native eager register/create/canonical/
   unregister/refcounted teardown in a mock before *any* AE private call.
2. Trace and implement a valid new native owner registration outside the
   fixed `BEE_Layer::CreateLayerFromType` switch (or prove none is available).
3. Instantiate a CNL typed `Contents` child with stable TDB StreamIDPath,
   host serialize/Undo and native selection.
4. Register the matching BEE evaluator and prove its native
   `BEE_VectorArt` producer and RenderGraph output.
5. Only with safe manual disposable host consent perform private ABI tests.
   No call to Adobe's private factory may occur at AEX startup.

CompNodeAE, all user projects and in-host AE remained untouched. Phase F
integration is **still paused** for architectural review.
