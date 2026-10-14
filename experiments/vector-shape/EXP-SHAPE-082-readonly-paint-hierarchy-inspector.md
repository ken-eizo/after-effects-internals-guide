# EXP-SHAPE-082 — Read-only native Paint hierarchy inspector built in CNL AEGP

Scope: Paint effect created by AE Brush, NOT Paint Bucket, NOT Brush Strokes.

The SDK 25.6's actual `Examples/AEGP/Streamie/Streamie.cpp` demonstrates Adobe's public AEGP access to real `"ADBE Paint Group"` and native Stroke children. This experiment brings a *nonmutating* inspector to the current CNL prototype AEX rather than executing SDK Streamie's mutation calls.

New source: `D:/Developer/ShapeLayerAE/labs/native_shape_layer_prototype/ChapePaintNativeInspector.cpp` (copy also preserved in `experiments/vector-shape/probe-src/tools/ChapePaintNativeInspector.cpp`).

Menu name: `ChapeLayer: Inspect Adobe Paint Native Streams (Read Only)`.

On a user-installed disposable AE test:
1. Create a disposable project/layer, draw with Brush tool so AE automatically generates its own Paint effect and at least one brush stroke.
2. Run the inspector from the Animation menu.
3. Inspect `%TEMP%/ChapeLayer_PaintNativeHierarchy.tsv` and `%TEMP%/ChapeLayer_MenuRegistration.tsv`.
4. Compare real hierarchy MatchNames, leaf/group kinds, indexed child counts to SDK source and BEE static facts; do not add unfamiliar custom Stream types.

Expected log includes `paint_found=1`, `node` records of host native Paint subtree, `host_project_mutated=0`. **Expected ≠ measured**: no new inspector host log has yet been generated. Do not describe this as in-host PASS.

Offline verification:
```powershell
cmake --build D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype --config Release
ctest --test-dir D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype -C Release --output-on-failure
python D:\Developer\ShapeLayerAE\labs\native_shape_layer_prototype\verify_native_shape_aex.py
python D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_paint_sdk_and_inspector.py
```

PASS: Release AEX build, 4/4 CTest, x64 PiPL and C ABI verifier, static inspector read-only whitelist/blacklist. **NOT PROVEN:** newly registered native custom Stream or foreign Layer ownership. No AE installation mutated and no private Adobe C++ call made.

Details: `research/findings/F-VECTOR-082-sdk-streamie-and-readonly-paint-inspector.md`.
