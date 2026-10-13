---
date: 2026-10-14
status: PASS native CNL typed Timeline engine + C ABI + AEGP build; host-native Adobe Layer owner still not constructed
evidence: MSVC x64 double build, 4/4 CTest, PE PiPL/export/import verifier; prior Adobe binary research F-VECTOR-037/054/063
---
# EXP-SHAPE-066 — Real generic CNL Timeline grammar and versioned plug-in ABI

Active implementation folder:
D:/Developer/ShapeLayerAE/labs/native_shape_layer_prototype

Actual new C++ source:
- ChapeNativeTimeline.h, ChapeNativeTimeline.cpp, ChapeNativeTimelineTest.cpp
- ChapeTimelineABI.h, ChapeTimelineABI.cpp, ChapeTimelineABITest.cpp
- ChapeTimelineHostDemo.cpp, NATIVE_TIMELINE_V1.md

Rebuilt CNLNativeShapeLayer.aex (Win x64) with a new AEGP Animation command:
ChapeLayer: Test Typed Timeline Engine (CNL Only). This command constructs
two CNL-defined layer-like type families and their typed nested properties,
sampled animation, archive roundtrip, and writes a TSV report. No host project
mutation and no BEE/TDB private registration.

The model supports any schema-defined immediate child-type rules, scoped
forward/reverse evaluation order, stable node IDs, Float/Vector2/Color/Boolean,
linear/hold keyframes, CNLTLN01 deterministic schema+tree archive, Undo/Redo.
C ABI exports 15 functions and synchronous typed-property visitor callback.
The AEX PE also contains 37 existing CNL functions, no direct BEE/TDB/FLT
imports, Adobe public PiPL and EntryPointFunc.

Native MSVC Release CTest 4/4 PASS, including malformed archive tests. An
independent build of the archived AEIG source also passed CTest 4/4.

This is NOT an Adobe-native custom Timeline Layer/Contents. The source
defines an independent CNL runtime; it currently lacks TDB/BEE native
owner registration, Pen/Selection/RG/VectorArt and AE project native save
integration. Updated in-host AEX test pending user. Read F-VECTOR-066.

No Adobe process operations, no Adobe binaries modified, no
CNLPrivateTDBDisposable invoked, no CompNodeAE modifications, Phase F paused.
