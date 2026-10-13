# CNL Native Shape Layer — independent engine prototype (2026-10-12)

This is a **REAL compiled C++ / AEGP AEX plugin** carrying its own native,
non-raster vector scene engine. It is not an ordinary PF Effect, and it never
uses a Mask or existing Adobe Shape Layer as a host carrier.

**Critical product status:** The new native Shape data model is CNL-owned
and has compiled and passed offline tests. However, the plugin is **NOT
YET REGISTERED AS A TRUE ADOBE BEE/TDB Shape Layer or a native AE Timeline
Contents owner**. Do not describe this as a finished AE-native Shape Layer.
Adobe's native Pen, Selection, BEE_VectorArt and RenderGraph have not been
bound. There is no in-host test yet for this particular AEX.

## Actual implemented features

- Native Windows x64 MSVC AEGP plugin `CNLNativeShapeLayer.aex`, with PiPL
  resource, `EntryPointFunc`, and a separate **37-symbol C ABI** for
  constructing, editing, persisting and vector-exporting CNL scenes.
- CNL-owned nested indexed `Contents` / `Group` / `Path` tree, stable
  `uint64_t` node IDs, editable cubic Bezier handles, procedural ellipse.
- Snapshot-based undo/redo, capped at 64 steps, with semantic status returns;
  failed mutations do not introduce a new Undo entry.
- Deterministic checksummed `CNLVEC01` archive, with strict version, checksum,
  bounds and malformed input validation. Same path/node ID restored on reload.
- True mathematical **SVG vector path output** preserving cubic segments
  and nested group order, not pixels, `PF_World`, a mask or baked Shape.
- Explicit capabilities struct returns **false** for host-native TDB/Contents,
  Pen and BEE_VectorArt bridges. Neither the user nor future developers may
  misread an offline "PASS" as proof of those features.

## Offline test results

```powershell
cmake -S D:\Developer\ShapeLayerAE\labs\native_shape_layer_prototype -B D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype -G "Visual Studio 17 2022" -A x64
cmake --build D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype --config Release
ctest --test-dir D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype -C Release --output-on-failure
python D:\Developer\ShapeLayerAE\labs\native_shape_layer_prototype\verify_native_shape_aex.py
```

Validated independent C++ logic: nested grouping, 90 generated shapes,
unique/stable IDs, path manipulation, corruption rejection, deterministic
archive, undo/redo branching, maximum history 64, SVG generation, injection-safe
name handling. 1/1 CTest PASS. PE analysis PASS: 64-bit, correct PiPL, public
AEGP entrypoint, 37 CNL C ABI symbols, **zero direct imports of BEE/TDB/FLT**.

## Binary

`D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype\Release\CNLNativeShapeLayer.aex`

This is a research binary, **not to install in a daily AE environment without
a test plan**. It is tested offline only. Installation and GUI testing, if
desired, are entirely user-driven. Never install it automatically.

## Optional disposable AE smoke test (user only)

- Use a disposable AE2026 process/project. Copy only this prototype AEX into
  the AE Plug-ins directory after closing AE; relaunch AE.
- Open menu: **Animation → CNL Native Shape: Independent Engine Self-Test
  (No Host Edits)**. It should not require a selected layer.
- The command builds a CNL-owned vector document, modifies a Bezier vertex,
  tests Undo/Redo and binary archive and writes:
  `%TEMP%\CNL_NativeShapeLayer_Prototype.tsv` and
  `%TEMP%\CNL_NativeShapeLayer_Prototype.svg`.
- The plugin never creates an AE Layer, modifies the project or registers an
  undocumented Adobe factory. It never claims real native Contents.
- Return the TSV or exact errors from this experimental smoke test.

## Next actual product milestone

The true product must implement a separate **Adobe Host NativeOwnerAdapter**
with complete lifecycle and version checks, and demonstrate ALL gates:

1. A foreign CNL-defined TDB stream class, canonical ownership and factory
   registration + cleanup without dangling C++ vtables.
2. Host native `BEE_CompItem` or otherwise valid host owner, not Mask,
   Effect Parade or existing Adobe Shape carrier.
3. Correct `Contents` parent-child stream registration, creation/selection,
   save/reopen and native host Undo.
4. CNL BEE evaluator registration + `BEE_VectorArt` and RG rendering.
5. Native Pen tool hit-testing and vertex writeback through `BEE_StreamSpec`.

Nothing in Adobe's documented AE SDK currently provides these extensions as
ordinary AEGP/PF suites. **Do not patch the host binary or call undocumented
registration routines in live AE until ABI ownership and teardown are proven.**
The older `CNLPrivateTDBDisposable.aex` remains unapproved and not run.

This prototype is deliberately separate from `D:\Developer\CompNodeAE`.
Phase F product integration remains paused pending user architecture review.


## ChapeLayer Phase 2 — native hierarchy semantics, 2026-10-13

**Implementation in ShapeLayerAE:**

- Layer > New > ChapeLayer (Native Type Pending): the documented AEGP_Menu_NEW is used. This reports no native AE ChapeLayer exists yet and deliberately creates neither stock Shape nor Mask nor Effect.
- Animation > ChapeLayer: Inspect Native Contents Admission (Read Only): select an existing stock Shape Layer containing a nested Shape Group. The action writes %TEMP%\ChapeLayer_HostAdmission_ReadOnly.tsv with scope, indexed_child, can_add, and cnl_evaluation_trace rows. Uses public AEGP_DynamicStreamSuite reads only. Never calls AddStream or private BEE/TDB and never modifies a project.
- ChapeHierarchyRules.h/.cpp: plugin-authored MatchName type registration, parent-specific child admissibility, stable node identity, custom named group types, reorder/reparent/cycle checks, and group-level Forward / Reverse evaluation order. Type policy revisions cannot orphan current nodes.
- ChapeHierarchyRulesTest.cpp: real Release-safe native C++ regression checks for customizable hierarchy and evaluation order. An evaluation trace is a CNL native scheduling abstraction, NOT Adobe BEE VectorArt renderer output.

**Research boundary:** a host AEGP_CanAddStream TRUE for unknown names under ADBE Vector Shape -, ADBE Vector Graphic -, or ADBE Vector Filter - reflects parent admission only. It does not prove an actual TDB native C++ type factory has been installed. Do NOT call AEGP_AddStream on an unknown type in a real AE project.

Built AEX and standalone CNL schema are **not** yet a host-registered new BEE Layer or Adobe native Timeline Contents. Host native class registration, owner lifetime, editor and Pen routing, Undo, serialization and BEE VectorArt remain open. This new AEX has not yet been tested inside AE by the user.

Rebuild: cmake --build D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype --config Release
Tests: ctest --test-dir D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype -C Release --output-on-failure
PE: python D:\Developer\ShapeLayerAE\labs\native_shape_layer_prototype\verify_native_shape_aex.py


## 2026-10-13 correction from actual AE2026 screenshots and TSV

The user confirmed that the previous AEX exposed the Animation probe but **did not visually show "ChapeLayer" in Layer > New**. The same probe produced AE's internal verification message:

"GetNewStreamRefByMatchname only works on named groups."

We inspected the actual user-host TSV at %TEMP%\ChapeLayer_HostAdmission_ReadOnly.tsv:
- active_layer_kind=4 (existing native Vector Layer);
- the layer's root is a NAMED_GROUP;
- ADBE Root Vectors Group is itself **INDEXED_GROUP** (kind=2);
- its child count on that fixture was zero;
- CanAddStream accepted unknown ADBE Vector Shape/Graphic/Filter-prefixed child names but rejected CNL:Forward/Reverse/Path;
- the CNL-own trace passed, but no Adobe stream was created.

**Bug corrected:** the probe had called GetNewStreamRefByMatchname(parent=ADBE Root Vectors Group, name=ADBE Vectors Group). This is categorically invalid on INDEXED_GROUP and caused the host assertion. The fixed version:
1. checks the parent's grouping type before every by-MatchName lookup;
2. directly treats ADBE Root Vectors Group as the actual indexed top-level native Contents;
3. traverses its children by GetNewStreamRefByIndex;
4. searches ADBE Vectors Group only under a NAMED_GROUP child whose matchName is ADBE Vector Group;
5. handles empty native Contents and disposes each ref only once.

**Menu investigation:** The public SDK's AEGP_Menu_NEW does specify the Layer > New submenu, but the user did not see the previous AT_BOTTOM inserted item. The new build tries AT_TOP and registers a separate public AEGP_Menu_LAYER *fallback* status command. On plugin startup it writes **%TEMP%\ChapeLayer_MenuRegistration.tsv** with exact GetUniqueCommand, InsertMenuCommand, and hook errors. A zero error from InsertMenuCommand alone is NOT proof the host displays the action.

The new binary has been built and its static PE/safety checks and 2/2 CTests passed, but it has not yet been run in the host. The user's current installed AEX should be manually replaced **only while AE is closed**, and only in an isolated disposable AE session. Don't claim the New submenu is fixed until the host screenshot and menu TSV confirm it.

The native Shape Contents grammar itself and arbitrary new BEE-owned Layer type remain **unregistered**, and no private TDB registrar has been called.
