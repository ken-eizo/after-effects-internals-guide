# Chape Native Timeline v1 — typed schema engine and plug-in C ABI

This is a **real native C++ typed Timeline runtime compiled into AEGP CNLNativeShapeLayer.aex**.
It is NOT an Adobe host-owned BEE_Layer, TDB_StreamBase, native AE Timeline Contents node, or native AE Pen renderer.

## Semantic tree, not PF_Param_GROUP

Runtime-definable child schemas and separate native type families:

    CNL:Stage
      CNL:VectorLayer
        CNL:ShapeGroup
          CNL:Position : Vector2 with keyframes
          CNL:Color : Color
      CNL:TextLayer
        CNL:TextAnimator
          CNL:Opacity : Float with keyframes
          CNL:Enabled : Boolean
      CNL:NewLayerFamily
        ... arbitrary plugin-defined child types ...

Every custom Type has a MatchName, container or property Kind,
allowed children and Forward/Reverse traversal semantics.
Nodes have stable uint64 IDs, ordered children, reparent/reorder and
cycle protection. Property Keyframes use signed int64 application-time ticks,
Hold / Linear interpolation, and Boolean uses discrete sampling.

## Real ABI v1

ChapeTimelineABI.h exports 15 C functions from the AEX, all implemented:

- chape_timeline_abi_version, create, destroy
- define_type, permit, add, move
- set_base, set_key, sample
- evaluate (synchronous typed property visitor callback)
- archive, restore, undo, redo

No C++ or STL objects cross the C ABI. The event's matchName pointer
is borrowed only for the callback duration. The module DOES NOT retain
third-party callback pointers or register them with Adobe. Users should
not reenter and mutate the same Document from a visitor.

Typed values are four doubles (Float, Vector2, Color, Boolean), although
the unused component restriction is currently a consumer convention.
Evaluation emits group begin/end and keyframed property values in
per-group Forward/Reverse order; this is NOT Adobe BEE VectorArt output.

Archives use CNLTLN01, deterministic schemas/nodes/properties,
version 1 and an FNV-1a checksum (integrity, not cryptographic integrity).
Load validates schema membership, node reachability, parent IDs, cycles,
keyframe ordering, type/kind, finite values and bounds before committing.
History is snapshot-based, 64 deep. Mutations copy the complete State,
so time/memory performance needs future optimization for large projects.

## In-host command (user test not yet executed)

Animation > ChapeLayer: Test Typed Timeline Engine (CNL Only)

Builds two independent native CNL layer families, creates groups/properties,
evaluates keyframed Position / Opacity, verifies stable archive roundtrip and
writes TEMP/ChapeLayer_TypedTimelineDemo.tsv.

No AE project change or BEE/TDB calls, and no real Adobe Layer is created.

## Actual tests

MSVC Release Windows x64 build PASS; four CTest suites PASS:
native SVG Shape core; typed child-schema/order; new generalized
multi-layer native CNL Timeline; public C ABI/visitor.

The binary verifier validates Adobe public AEGP EntryPoint/PiPL, CNL
export set and 15 new Timeline ABI functions, no direct BEE/TDB/FLT imports.

## The real Adobe host-native blocker

Native CNL data is not yet host-native AE Timeline data. Complete product
requires ALL these separately:

1. Safe host-admitted TDB_StreamBase C++ factory/canonical owner/Undo/IDPath
   with versioned ABI, lifecycle and guaranteed unregister.
2. Genuine independent BEE_Layer class creation and BEE_CompItem insertion
   beyond the built-in closed layer kind switch. No public mechanism proven.
3. Parent Contents admission for custom MatchNames. The builtin Shape
   CanStore uses ADBE Vector Group and exactly three Adobe native prefixes;
   parent acceptance does NOT mean a TDB creator or BEE evaluator exists.
4. The separate BEE VectorArt polymorphic evaluator registry and native
   RG compositor dispatch for new objects.
5. Native Pen/Selection/Timeline, host archive/reopen and native Undo.
6. Safe project closing and DLL unload without dangling vtables/callbacks.

If stock Adobe AE provides no safe foreign owner registration route,
report that as a real blocker rather than misrepresenting our own Timeline
runtime or using a built-in Shape Layer as a carrier.

Never run the dangerous CNLPrivateTDBDisposable.aex on a normal AE install.
CompNodeAE and Phase F integration remain untouched.

Build:
cmake --build D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype --config Release

Tests:
ctest --test-dir D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype -C Release --output-on-failure
