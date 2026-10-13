---
date: 2026-10-13
status: PASS offline AEX x64 build + 2/2 C++ CTest; host menu/probe pending user execution
evidence: installed AE SDK 25.6 headers + on-disk executable PE + ShapeLayerAE compiled tests + prior real EXP-SHAPE-005
---
# EXP-SHAPE-061 — ChapeLayer native hierarchy rule system + Layer New menu + host parent-admission matrix

## Delivered in the active source

D:\Developer\ShapeLayerAE\labs\native_shape_layer_prototype\

- NativeShapeLayerPlugin.cpp: registers "ChapeLayer (Native Type Pending)" in Layer > New by Adobe public AEGP_Menu_NEW. This command fails closed and never creates an Adobe Shape Layer, a mask or an Effect instead.
- ChapeHostAdmissionProbe.cpp: new read-only Animation menu probe; given selected stock Shape Layer with actual Group Contents, records SDK GetMatchName, grouping type, indexed child order and CanAddStream for built-in child MatchNames, unknown ADOBE-prefixed IDs, and unique CNL-defined IDs. It never calls AEGP_AddStream, private TDB, BEE or any mutation API. Output (host run pending): %TEMP%\ChapeLayer_HostAdmission_ReadOnly.tsv.
- ChapeHierarchyRules.h/.cpp: actual native C++ user-configurable type grammar, allowed-child rules, custom group-level execution order forward/reverse, reparent/reorder/cycle checks, stable IDs, rule-update validity checks.
- ChapeHierarchyRulesTest.cpp: release-safe CHECK regression tests, 37+ assertions, no NDEBUG disappearing tests.
- Existing CNL vector root, Bezier edit, archive/Undo/SVG unchanged.

## Exact scope of new meaning

The existing Shape Layers in After Effects do expose public Indexed Group manipulation. The separate user-defined host-native stream type creator, user-owned parent/child validity rules, custom native editor and per-group ordered evaluator are not public AEGP_DynamicStreamSuite functionality.

This lab **does demonstrate** a new CNL-owned grammar and ordered evaluation trace: group A emits A then B; a nested reverse group emits D then C; after reparent/reorder, traces change correctly. This is **NOT Adobe host Timeline-native operator creation, BEE VectorArt rendering, a built-in Shape render-order law, or new host native Layer registration.**

The AEGP CanAddStream unknown-prefix TRUE host evidence already existed under EXP-SHAPE-005. That is permission/admission only. Do not instantiate unknown types in a live AE session until private type factory existence, ABI safety and lifecycle are independently proven.

## Offline QA

Windows MSVC Release build PASSED, AEX PE check PASSED, CTest 2/2 PASSED:
- NativeShapeOwnedRuntime
- ChapeHierarchyRules

Native AEX at D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype\Release\CNLNativeShapeLayer.aex
SHA256: 3743f073606609ce1f486277b8b9c9455c38a014109c374b674c18651e913f45
Size: 111104 bytes. These exact receipts may change on recompilation.

AE host has **not** yet executed the updated menu/admission probe. The previous in-host PASS for the older independent engine only proves the earlier build worked in host.

The unresolved native-host product gates remain: foreign TDB stream class registration/unregister, actual native owner creation outside the closed stock LayerType dispatcher, BEE evaluator+VectorArt, Pen/Selection and native host Undo/Persistence. No AE process or user project modified. CompNodeAE unchanged. Phase F paused.
