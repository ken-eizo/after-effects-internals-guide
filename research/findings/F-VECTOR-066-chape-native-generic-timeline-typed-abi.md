---
date: 2026-10-14
status: PASS CNL typed native Timeline implementation; NOT Adobe-host native Timeline registration
evidence: E2-L Windows x64 MSVC builds, PE ABI exports, 4/4 native CTest; previous binary host research
---
# F-VECTOR-066 — Compiled extensible CNL native Timeline grammar and C ABI; separate host-native extension gap

## Product objective
The objective is to let third-party developers create whole new native AE
Timeline layer families with their OWN child property grammar, animators,
vector operators, nested editing, persistent identity and native renderer.
Not a normal PF Effect group, Adobe Shape carrier or script.

## Actual implementation on the working PC
D:/Developer/ShapeLayerAE/labs/native_shape_layer_prototype/ contains:
- ChapeNativeTimeline.h/cpp: native C++ runtime registry for arbitrary MatchName
  types; independent group, Float, Vector2, Color, Boolean; immediate parent
  child-type permission rules, reorder/reparent, cycle prevention, forward/reverse
  group-local evaluation order.
- Typed keyframes with signed 64-bit ticks; Hold or Linear sampling; Boolean is
  discrete; sampled event trace has scoped begin/property/end events.
- Deterministic CNLTLN01 archive of the COMPLETE custom schema, node hierarchy,
  order, values and keyframes; validated checksum, types, IDs, graph
  reachability, parent membership, child admission, non-cyclic structure,
  finite values and key monotonicity. Mutation Undo/Redo up to 64 snapshots.
- ChapeTimelineABI.h/cpp exports 15 C ABI functions (opaque CNL Timeline
  handle, schema definitions, property edits, animation evaluation,
  synchronous external visitor, archive, restore and Undo/Redo). No STL/C++
  objects cross the API. Callback pointers never remain registered afterward.
- ChapeTimelineHostDemo.cpp registers an additional public AEGP Animation menu
  command. When manually executed it constructs independent CNL VectorLayer
  and TextLayer families, animated typed properties and a binary roundtrip,
  writing TEMP/ChapeLayer_TypedTimelineDemo.tsv. No user AE project mutation,
  no BEE or TDB private registrations, and no AE host-native layer creation.

## Offline verification — real code
- MSVC Windows x64 AEX compiled and linked successfully.
- CTest 4/4 PASS: native Shape core, hierarchy rules, new typed Timeline and
  external C ABI with synchronous property visitor. Native archive tests include
  full roundtrip, checksum damage, truncations and extensive byte corruption.
- PE verification: public AEGP EntryPointFunc and PiPL; 37 existing CNL ABI
  exports and 15 new chape_timeline_ prefixed functions. No direct imports of
  BEE.dll, TDB.dll or FLT.dll.
- Separate MSVC build from the archived AEIG source also passed 4/4.
- User's AE previously confirmed an OLDER independent CNL engine AEX; the
  NEW typed Timeline engine AEX has NOT been executed within AE yet.
  Do not misrepresent a successful compiler/CTest as host acceptance.

## What the native code achieves for future extensions
Multiple independent custom layer-like schemas, user-defined child type
permissions, parameter-type policies and evaluation-order contracts now have
a single versioned CNL runtime. Other C/C++ modules can consume it rather
than duplicating a fixed Shape-specific UI tree. The current 4-channel value
representation does not enforce unused component constraints and does not
provide general BEE geometry/render reductions; group evaluation is currently
a CNL event stream.

## Remaining fundamental Adobe-native barriers
F-VECTOR-037 proves the existing BEE_Layer::CreateLayerFromType function has
a CLOSED eight-case integer constructor dispatcher (0..7). Simply registering
a custom TDB MatchName cannot create a ninth genuine host-native layer kind.
F-VECTOR-054 proves TDB typed creator table and 20-entry BEE evaluator are
separately registered. F-VECTOR-063/065 proves built-in native Contents
CanStore accepts one exact Group MatchName and 3 Adobe-native prefixes,
without consulting any creator or evaluator. F-VECTOR-028 shows BEE evaluator
registration is a private C++ polymorphic registry without a proven safe
external unregister, hence hot-unload risk.

Completion requires a safe external native BEE Layer owner extension route,
real TDB typed ownership plus serialization, an arbitrary-indexed Contents
admission contract, native BEE VectorArt evaluator + RG, Pen/Selection/IDPath,
AE-native Undo and save/reopen, and unload-time lifecycle safety. This route
is STILL UNPROVEN, and the documented public AEGP SDK does not expose these
private creator/owner registrations.

Never patch Adobe DLLs or run the unsafe private disposable registrar in a
normal AE host. If the external owner route is unavailable on unmodified AE,
record that hard limit instead of falsely claiming a native type by using a
Mask/Effect/Shape carrier. CompNodeAE and Phase F remain untouched.
